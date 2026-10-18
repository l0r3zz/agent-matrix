use anyhow::{anyhow, Context, Result};
use dotenvy::dotenv;
use log::{error, info, warn};
use pulldown_cmark::{html, Options, Parser};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet, VecDeque};
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::fs;
use tokio::time::timeout;

const MAX_CHARS_PER_MESSAGE: usize = 32000;
const MAX_PERSISTED_EVENT_IDS: usize = 1000;

/// Read the canonical Agent Zero API credential from `/a0/usr/workdir/matrix-bot/.a0-api-key`
/// (or `.a0-api-key` in `bot_dir`). Do not fall back to `.env`.
fn load_canonical_a0_api_key(bot_dir: &Path) -> Result<String> {
    let secret_path = std::env::var("A0_API_KEY_FILE")
        .map(PathBuf::from)
        .unwrap_or_else(|_| bot_dir.join(".a0-api-key"));

    let raw = std::fs::read_to_string(&secret_path).with_context(|| {
        format!(
            "Failed to read canonical Agent Zero credential from {} (fail-closed)",
            secret_path.display()
        )
    })?;
    let token = raw.trim().to_string();
    if token.is_empty() {
        return Err(anyhow!(
            "Canonical Agent Zero credential file {} is empty (fail-closed)",
            secret_path.display()
        ));
    }

    info!(
        "Loaded canonical Agent Zero credential from {} (len={})",
        secret_path.display(),
        token.len()
    );
    Ok(token)
}

/// Strip Matrix mention "pills" from plain-text message bodies.
/// Element sends mentions as `[@user:server](https://matrix.to/#/@user:server)`
/// in the plain-text `body` field. This function converts them to plain `@user:server`.
fn strip_matrix_mention_pills(input: &str) -> String {
    let mut result = String::with_capacity(input.len());
    let chars: Vec<char> = input.chars().collect();
    let len = chars.len();
    let mut i = 0;
    while i < len {
        if chars[i] == '[' && i + 1 < len && chars[i + 1] == '@' {
            if let Some(bracket_close) = chars[i..].iter().position(|&c| c == ']') {
                let bracket_close = i + bracket_close;
                let after = bracket_close + 1;
                if after < len && chars[after] == '(' {
                    if let Some(paren_close) = chars[after..].iter().position(|&c| c == ')') {
                        let paren_close = after + paren_close;
                        let link: String = chars[after + 1..paren_close].iter().collect();
                        if link.starts_with("https://matrix.to/") {
                            let mention: String = chars[i + 1..bracket_close].iter().collect();
                            result.push_str(&mention);
                            i = paren_close + 1;
                            continue;
                        }
                    }
                }
            }
        }
        result.push(chars[i]);
        i += 1;
    }
    result
}

#[derive(Clone, Debug)]
struct Config {
    homeserver_url: String,
    user_id: String,
    access_token: String,
    device_id: String,
    a0_api_url: String,
    a0_api_key: String,
    bot_display_name: String,
    agent_identity: String,
    sync_timeout_ms: u64,
    state_file: PathBuf,
    cursor_file: PathBuf,
    amctl_url: String,
    amctl_api_key: String,
    trigger_prefixes: Vec<String>,
}

#[derive(Debug, Default, Serialize, Deserialize)]
struct RoomState {
    #[serde(flatten)]
    room_contexts: HashMap<String, String>,
}

#[derive(Debug, Default, Serialize, Deserialize)]
struct SyncCursorState {
    #[serde(default)]
    version: u32,
    next_batch: Option<String>,
    #[serde(default)]
    processed_events: Vec<String>,
}

struct Bot {
    cfg: Config,
    matrix_client: reqwest::Client,
    a0_client: reqwest::Client,
    state: RoomState,
    whoami_user_id: String,
    trusted_senders: HashSet<String>,
    processed_events_set: HashSet<String>,
    processed_events_order: VecDeque<String>,
}

impl Config {
    fn from_env(bot_dir: PathBuf) -> Result<Self> {
        let homeserver_url =
            std::env::var("MATRIX_HOMESERVER_URL").unwrap_or_else(|_| "http://localhost:8008".to_string());
        let user_id = std::env::var("MATRIX_USER_ID").unwrap_or_default();
        let access_token = std::env::var("MATRIX_ACCESS_TOKEN").unwrap_or_default();
        let device_id = std::env::var("MATRIX_DEVICE_ID").unwrap_or_else(|_| "AgentZeroBot".to_string());
        let a0_api_url =
            std::env::var("A0_API_URL").unwrap_or_else(|_| "http://localhost:80/api/api_message".to_string());
        // Phase 3 Credential Authority: read strictly from .a0-api-key (no fallback to .env)
        let a0_api_key = load_canonical_a0_api_key(&bot_dir)?;
        let bot_display_name = std::env::var("BOT_DISPLAY_NAME").unwrap_or_else(|_| "Agent Zero".to_string());
        let agent_identity = std::env::var("AGENT_IDENTITY").unwrap_or_else(|_| bot_display_name.clone());
        let sync_timeout_ms = std::env::var("SYNC_TIMEOUT_MS")
            .ok()
            .and_then(|v| v.parse::<u64>().ok())
            .unwrap_or(30000);
        let amctl_url =
            std::env::var("AMCTL_URL").unwrap_or_else(|_| "http://172.23.88.254:8077".to_string());
        let amctl_api_key =
            std::env::var("AMCTL_API_KEY").unwrap_or_else(|_| "amctl-dev-key-2026".to_string());

        if homeserver_url.is_empty() || user_id.is_empty() || access_token.is_empty() {
            return Err(anyhow!(
                "Missing config: MATRIX_HOMESERVER_URL, MATRIX_USER_ID, MATRIX_ACCESS_TOKEN"
            ));
        }

        let agent_short = user_id
            .split(':')
            .next()
            .unwrap_or("agent")
            .trim_start_matches('@')
            .to_string();
        let mut trigger_prefixes = vec![
            format!("{agent_short}:"),
            format!("{agent_short},"),
            format!("@{agent_short}"),
            "@all-agents:".to_string(),
            "@all-agents,".to_string(),
        ];
        if !bot_display_name.trim().is_empty() && !bot_display_name.eq_ignore_ascii_case(&agent_short) {
            trigger_prefixes.push(format!("{}:", bot_display_name));
            trigger_prefixes.push(format!("{},", bot_display_name));
            trigger_prefixes.push(format!("@{}", bot_display_name));
        }

        let state_file = bot_dir.join("room_contexts.json");
        let cursor_file = bot_dir.join("sync_cursor.json");

        Ok(Self {
            homeserver_url,
            user_id,
            access_token,
            device_id,
            a0_api_url,
            a0_api_key,
            bot_display_name,
            agent_identity,
            sync_timeout_ms,
            state_file,
            cursor_file,
            amctl_url,
            amctl_api_key,
            trigger_prefixes,
        })
    }
}

impl Bot {
    async fn new(cfg: Config, initial_events: Vec<String>) -> Result<Self> {
        let mut matrix_headers = HeaderMap::new();
        matrix_headers.insert(
            AUTHORIZATION,
            HeaderValue::from_str(&format!("Bearer {}", cfg.access_token)).context("invalid access token")?,
        );
        matrix_headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));

        let matrix_client = reqwest::Client::builder()
            .default_headers(matrix_headers)
            .timeout(Duration::from_secs(70))
            .build()
            .context("build matrix client")?;

        let a0_client = reqwest::Client::builder()
            .timeout(Duration::from_secs(300))
            .build()
            .context("build a0 client")?;

        let state = load_state(&cfg.state_file).await.unwrap_or_default();
        let whoami_user_id = cfg.user_id.clone();

        let mut processed_events_set = HashSet::new();
        let mut processed_events_order = VecDeque::new();
        for ev_id in initial_events {
            if processed_events_set.insert(ev_id.clone()) {
                processed_events_order.push_back(ev_id);
            }
        }
        while processed_events_order.len() > MAX_PERSISTED_EVENT_IDS {
            if let Some(old) = processed_events_order.pop_front() {
                processed_events_set.remove(&old);
            }
        }

        let mut bot = Self {
            cfg,
            matrix_client,
            a0_client,
            state,
            whoami_user_id,
            trusted_senders: HashSet::new(),
            processed_events_set,
            processed_events_order,
        };
        bot.verify_whoami().await?;
        bot.refresh_trusted_senders().await;
        Ok(bot)
    }

    fn matrix_url(&self, path: &str) -> String {
        format!("{}{}", self.cfg.homeserver_url.trim_end_matches('/'), path)
    }

    async fn verify_whoami(&mut self) -> Result<()> {
        let url = self.matrix_url("/_matrix/client/v3/account/whoami");
        let resp = self.matrix_client.get(url).send().await.context("call /whoami")?;
        if !resp.status().is_success() {
            return Err(anyhow!("/whoami failed with HTTP {}", resp.status()));
        }
        let data: Value = resp.json().await.context("parse /whoami JSON")?;
        let actual = data.get("user_id").and_then(Value::as_str).unwrap_or("").to_string();
        if actual.is_empty() || actual != self.cfg.user_id {
            return Err(anyhow!(
                "Identity mismatch in /whoami: actual '{}' != configured '{}'",
                actual,
                self.cfg.user_id
            ));
        }
        self.whoami_user_id = actual;
        info!("Verified /whoami identity: {}", self.whoami_user_id);
        Ok(())
    }

    async fn refresh_trusted_senders(&mut self) {
        let url = format!("{}/api/v1/trusted-senders", self.cfg.amctl_url.trim_end_matches('/'));
        match self
            .a0_client
            .get(&url)
            .header("X-API-Key", &self.cfg.amctl_api_key)
            .timeout(Duration::from_secs(5))
            .send()
            .await
        {
            Ok(resp) if resp.status().is_success() => {
                if let Ok(items) = resp.json::<Vec<Value>>().await {
                    let mut set = HashSet::new();
                    for item in items {
                        if let Some(uid) = item.get("matrix_user_id").and_then(Value::as_str) {
                            set.insert(uid.to_string());
                        }
                    }
                    if !set.is_empty() {
                        info!("Loaded {} trusted sender(s) from am-ctl platform", set.len());
                        self.trusted_senders = set;
                        return;
                    }
                }
            }
            Ok(resp) => {
                warn!("Failed to fetch trusted_senders from am-ctl: HTTP {}", resp.status());
            }
            Err(e) => {
                warn!("Could not reach am-ctl for trusted_senders: {e}");
            }
        }

        if self.trusted_senders.is_empty() {
            // Safe baseline fallback if platform is temporarily unreachable
            self.trusted_senders.insert("@admin:v-site.net".to_string());
            self.trusted_senders.insert("@l0r3zz:v-site.net".to_string());
        }
    }

    fn record_processed_event(&mut self, event_id: &str) -> bool {
        if event_id.is_empty() {
            return true;
        }
        if !self.processed_events_set.insert(event_id.to_string()) {
            return false;
        }
        self.processed_events_order.push_back(event_id.to_string());
        while self.processed_events_order.len() > MAX_PERSISTED_EVENT_IDS {
            if let Some(old) = self.processed_events_order.pop_front() {
                self.processed_events_set.remove(&old);
            }
        }
        true
    }

    async fn set_display_name(&self) {
        if self.cfg.bot_display_name.trim().is_empty() {
            return;
        }
        let user_enc = urlencoding::encode(&self.cfg.user_id);
        let url = self.matrix_url(&format!("/_matrix/client/v3/profile/{user_enc}/displayname"));
        let body = json!({ "displayname": self.cfg.bot_display_name });
        match self.matrix_client.put(url).json(&body).send().await {
            Ok(resp) if resp.status().is_success() => {
                info!("Set display name to: {}", self.cfg.bot_display_name);
            }
            Ok(resp) => {
                warn!("Failed to set display name: HTTP {}", resp.status());
            }
            Err(err) => {
                warn!("Failed to set display name: {err}");
            }
        }
    }

    async fn send_message(&self, room_id: &str, body_text: &str) -> Result<()> {
        let room_enc = urlencoding::encode(room_id);
        let txn = format!(
            "rustbot-{}",
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis()
        );
        let url = self.matrix_url(&format!(
            "/_matrix/client/v3/rooms/{room_enc}/send/m.room.message/{txn}"
        ));

        let mut payload = json!({
            "msgtype": "m.text",
            "body": body_text,
        });

        let formatted = markdown_to_html(body_text);
        if let Some(obj) = payload.as_object_mut() {
            obj.insert("format".to_string(), Value::String("org.matrix.custom.html".to_string()));
            obj.insert("formatted_body".to_string(), Value::String(formatted));
        }

        let resp = self.matrix_client.put(url).json(&payload).send().await?;
        if !resp.status().is_success() {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            return Err(anyhow!("send_message failed {status}: {text}"));
        }
        Ok(())
    }

    async fn set_typing(&self, room_id: &str, typing: bool) -> Result<()> {
        let room_enc = urlencoding::encode(room_id);
        let user_enc = urlencoding::encode(&self.cfg.user_id);
        let url = self.matrix_url(&format!("/_matrix/client/v3/rooms/{room_enc}/typing/{user_enc}"));
        let payload = json!({
            "typing": typing,
            "timeout": 60000
        });
        let resp = self.matrix_client.put(url).json(&payload).send().await?;
        if !resp.status().is_success() {
            warn!("typing update failed with status {}", resp.status());
        }
        Ok(())
    }

    async fn join_room(&self, room_id: &str) -> Result<bool> {
        let room_enc = urlencoding::encode(room_id);
        let url = self.matrix_url(&format!("/_matrix/client/v3/join/{room_enc}"));
        let resp = self.matrix_client.post(url).json(&json!({})).send().await?;
        Ok(resp.status().is_success())
    }

    async fn sync(&self, since: Option<&str>, timeout_ms: u64, full_state: bool) -> Result<Value> {
        let mut req = self.matrix_client.get(self.matrix_url("/_matrix/client/v3/sync")).query(&[
            ("timeout", timeout_ms.to_string()),
            ("full_state", full_state.to_string()),
            ("set_presence", "online".to_string()),
            ("filter", "".to_string()),
        ]);
        if let Some(s) = since {
            req = req.query(&[("since", s.to_string())]);
        }
        let resp = req.send().await?;
        let status = resp.status();
        let body = resp.text().await?;
        if !status.is_success() {
            return Err(anyhow!("sync failed {status}: {body}"));
        }
        serde_json::from_str::<Value>(&body).context("parse /sync response")
    }

    async fn ask_agent_zero(&mut self, message: &str, room_id: &str, sender: &str) -> String {
        let context_id = self.state.room_contexts.get(room_id).cloned().unwrap_or_default();
        let message = format!(
            "[System: You are {}, a sovereign AI agent on the Agent-Matrix network. Your Matrix ID is {}. Always identify yourself as {}.]\n{}",
            self.cfg.agent_identity, self.cfg.user_id, self.cfg.agent_identity, message
        );
        let mut payload = json!({
            "message": message,
            "context_id": context_id,
        });
        let mut req = self.a0_client.post(&self.cfg.a0_api_url).json(&payload);
        if !self.cfg.a0_api_key.is_empty() {
            payload["api_key"] = Value::String(self.cfg.a0_api_key.clone());
            req = self
                .a0_client
                .post(&self.cfg.a0_api_url)
                .header("X-API-KEY", self.cfg.a0_api_key.clone())
                .json(&payload);
        }

        info!(
            "Sending to Agent Zero | room={} | ctx={} | from={}",
            room_id,
            self.state.room_contexts.get(room_id).cloned().unwrap_or_else(|| "NEW".to_string()),
            sender
        );

        let first = req.send().await;
        match first {
            Ok(resp) if resp.status().is_success() => {
                return self.handle_a0_success(room_id, resp).await;
            }
            Ok(resp) if resp.status().as_u16() == 401 => {
                if let Ok(new_token) = load_canonical_a0_api_key(
                    self.cfg.state_file.parent().unwrap_or_else(|| Path::new(".")),
                ) {
                    if !new_token.is_empty() && new_token != self.cfg.a0_api_key {
                        info!("Got 401 from Agent Zero, retrying with reloaded .a0-api-key");
                        self.cfg.a0_api_key = new_token.clone();
                        payload["api_key"] = Value::String(new_token.clone());
                        let retry_req = self
                            .a0_client
                            .post(&self.cfg.a0_api_url)
                            .header("X-API-KEY", &new_token)
                            .json(&payload);
                        match retry_req.send().await {
                            Ok(retry_resp) if retry_resp.status().is_success() => {
                                return self.handle_a0_success(room_id, retry_resp).await;
                            }
                            Ok(retry_resp) => {
                                let status = retry_resp.status();
                                let body = retry_resp.text().await.unwrap_or_default();
                                error!("Agent Zero 401 retry failed with status {}: {}", status, body);
                                return format!("Agent Zero auth error after retry (HTTP {}). Check token sync.", status);
                            }
                            Err(e) => {
                                error!("Agent Zero 401 retry call failed: {e}");
                                return format!("Unexpected error on retry: {e}");
                            }
                        }
                    }
                }
                error!("Agent Zero returned 401 and .a0-api-key is unchanged");
                return "Agent Zero authentication failed. Check bot logs.".to_string();
            }
            Ok(resp) if resp.status().as_u16() == 404 && !context_id.is_empty() => {
                info!("Clearing stale context for room {}, retrying...", room_id);
                self.state.room_contexts.remove(room_id);
                if let Err(e) = save_state(&self.cfg.state_file, &self.state).await {
                    warn!("failed to save state after context clear: {e}");
                }
                payload["context_id"] = Value::String(String::new());
                let mut retry_req = self.a0_client.post(&self.cfg.a0_api_url).json(&payload);
                if !self.cfg.a0_api_key.is_empty() {
                    retry_req = self
                        .a0_client
                        .post(&self.cfg.a0_api_url)
                        .header("X-API-KEY", self.cfg.a0_api_key.clone())
                        .json(&payload);
                }
                match retry_req.send().await {
                    Ok(retry_resp) if retry_resp.status().is_success() => {
                        return self.handle_a0_success(room_id, retry_resp).await;
                    }
                    Ok(retry_resp) => {
                        error!("Agent Zero retry failed with status {}", retry_resp.status());
                        return "Agent Zero context error. Check bot logs.".to_string();
                    }
                    Err(e) => {
                        error!("Agent Zero retry call failed: {e}");
                        return format!("Unexpected error: {e}");
                    }
                }
            }
            Ok(resp) => {
                let status = resp.status();
                let body = resp.text().await.unwrap_or_default();
                error!("Agent Zero API error {}: {}", status, body);
                return format!("Agent Zero API error {}. Check bot logs.", status);
            }
            Err(e) => {
                error!("Cannot connect to Agent Zero API: {e}");
                return "Cannot reach Agent Zero. Is the container running?".to_string();
            }
        }
    }

    async fn handle_a0_success(&mut self, room_id: &str, resp: reqwest::Response) -> String {
        let data: Value = match resp.json().await {
            Ok(v) => v,
            Err(e) => {
                return format!("Unexpected error: {}", e);
            }
        };
        let reply = data
            .get("response")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim()
            .to_string();
        let new_ctx = data.get("context_id").and_then(Value::as_str).unwrap_or("").to_string();
        if !new_ctx.is_empty() && self.state.room_contexts.get(room_id).map(String::as_str) != Some(new_ctx.as_str())
        {
            self.state.room_contexts.insert(room_id.to_string(), new_ctx.clone());
            if let Err(e) = save_state(&self.cfg.state_file, &self.state).await {
                warn!("failed to save state: {e}");
            } else {
                info!("Context saved | room={} | ctx={}", room_id, new_ctx);
            }
        }
        if reply.is_empty() {
            "(Agent Zero returned an empty response)".to_string()
        } else {
            reply
        }
    }
}

async fn load_state(path: &Path) -> Result<RoomState> {
    if !path.exists() {
        return Ok(RoomState::default());
    }
    let content = fs::read_to_string(path).await?;
    let map: HashMap<String, String> = serde_json::from_str(&content).unwrap_or_default();
    Ok(RoomState { room_contexts: map })
}

async fn save_state(path: &Path, state: &RoomState) -> Result<()> {
    let json = serde_json::to_string_pretty(&state.room_contexts)?;
    let tmp = path.with_extension("json.tmp");
    fs::write(&tmp, json).await?;
    fs::rename(&tmp, path).await?;
    Ok(())
}

async fn load_sync_cursor(path: &Path) -> SyncCursorState {
    if !path.exists() {
        return SyncCursorState {
            version: 1,
            next_batch: None,
            processed_events: Vec::new(),
        };
    }
    match fs::read_to_string(path).await {
        Ok(content) => serde_json::from_str::<SyncCursorState>(&content).unwrap_or(SyncCursorState {
            version: 1,
            next_batch: None,
            processed_events: Vec::new(),
        }),
        Err(_) => SyncCursorState {
            version: 1,
            next_batch: None,
            processed_events: Vec::new(),
        },
    }
}

async fn save_sync_cursor(path: &Path, next_batch: &Option<String>, events: &VecDeque<String>) -> Result<()> {
    let state = SyncCursorState {
        version: 1,
        next_batch: next_batch.clone(),
        processed_events: events.iter().cloned().collect(),
    };
    let json = serde_json::to_string(&state)?;
    let tmp = path.with_extension("json.tmp");
    fs::write(&tmp, json).await?;
    fs::rename(&tmp, path).await?;
    Ok(())
}

fn markdown_to_html(input: &str) -> String {
    let mut options = Options::empty();
    options.insert(Options::ENABLE_TABLES);
    options.insert(Options::ENABLE_STRIKETHROUGH);
    options.insert(Options::ENABLE_TASKLISTS);
    let parser = Parser::new_ext(input, options);
    let mut output = String::new();
    html::push_html(&mut output, parser);
    output.replace('\n', "<br/>\n")
}

fn chunk_by_chars(input: &str, max_chars: usize) -> Vec<String> {
    let chars: Vec<char> = input.chars().collect();
    if chars.is_empty() {
        return vec![String::new()];
    }
    chars
        .chunks(max_chars)
        .map(|chunk| chunk.iter().collect::<String>())
        .collect()
}

fn built_in_response(body: &str, agent_identity: &str, user_id: &str) -> Option<String> {
    match body.trim().to_lowercase().as_str() {
        "ping" => Some("PONG".to_string()),
        "hello" => Some(format!("Hello! I'm {}, online and ready.", agent_identity)),
        "whoami" => Some(format!("I'm {} ({})", agent_identity, user_id)),
        _ => None,
    }
}

#[tokio::main]
async fn main() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    let mut attempt = 0u32;
    loop {
        attempt += 1;
        match run().await {
            Ok(()) => {
                info!("Clean shutdown.");
                break;
            }
            Err(e) if attempt < 10 => {
                let backoff = std::cmp::min(30, 2u64 * attempt as u64);
                error!("FATAL CRASH (attempt {}/10): {e} -- restarting in {backoff}s", attempt);
                let _ = append_crash_log(&format!("Attempt {attempt}: {e}")).await;
                tokio::time::sleep(Duration::from_secs(backoff)).await;
            }
            Err(e) => {
                error!("FATAL CRASH: {e} -- max retries exceeded, exiting");
                let _ = append_crash_log(&format!("Final attempt {attempt}: {e}")).await;
                std::process::exit(1);
            }
        }
    }
}

async fn run() -> Result<()> {
    let bot_dir = std::env::current_dir().context("resolve working directory")?;
    let _ = dotenv();
    let cfg = Config::from_env(bot_dir.clone())?;
    info!("Starting Matrix Bot: {} @ {}", cfg.user_id, cfg.homeserver_url);
    info!("Agent Zero API: {}", cfg.a0_api_url);
    info!("Device ID: {}", cfg.device_id);

    let cursor_state = load_sync_cursor(&cfg.cursor_file).await;
    let mut since = cursor_state.next_batch;
    if let Some(ref s) = since {
        info!(
            "Loaded persisted sync cursor from {}: next_batch={} (dedup_events={})",
            cfg.cursor_file.display(),
            s,
            cursor_state.processed_events.len()
        );
    }

    let mut bot = Bot::new(cfg, cursor_state.processed_events).await?;
    bot.set_display_name().await;

    let mut attempt = 0u32;
    loop {
        attempt += 1;
        let initial_full = since.is_none();
        match timeout(Duration::from_secs(60), bot.sync(since.as_deref(), 5000, initial_full)).await {
            Ok(Ok(sync)) => {
                if let Some(nb) = sync.get("next_batch").and_then(Value::as_str) {
                    since = Some(nb.to_string());
                }
                info!(
                    "Initial sync complete. Next batch: {}",
                    since.clone().unwrap_or_default()
                );
                handle_sync(&mut bot, &sync).await?;
                if let Err(e) = save_sync_cursor(&bot.cfg.cursor_file, &since, &bot.processed_events_order).await {
                    warn!("Failed to persist sync cursor: {e}");
                }
                break;
            }
            Ok(Err(e)) => {
                let backoff = std::cmp::min(30, 5 + attempt * 2);
                warn!("Initial sync failed: {} -- retrying in {}s", e, backoff);
                tokio::time::sleep(Duration::from_secs(backoff as u64)).await;
            }
            Err(_) => {
                let backoff = std::cmp::min(30, 5 + attempt * 2);
                warn!("Initial sync timeout -- retrying in {}s", backoff);
                tokio::time::sleep(Duration::from_secs(backoff as u64)).await;
            }
        }
    }

    #[cfg(unix)]
    let mut sigterm = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
        .context("register SIGTERM handler")?;

    info!("Starting sync loop -- bot is live!");
    let mut sync_count: u64 = 0;
    loop {
        #[cfg(unix)]
        let should_stop = tokio::select! {
            _ = tokio::signal::ctrl_c() => true,
            _ = sigterm.recv() => true,
            result = timeout(Duration::from_secs(45), bot.sync(since.as_deref(), bot.cfg.sync_timeout_ms, false)) => {
                match result {
                    Ok(Ok(sync)) => {
                        sync_count += 1;
                        if sync_count % 60 == 0 {
                            info!("Sync loop heartbeat: {} syncs completed (cursor={})", sync_count, since.as_deref().unwrap_or("none"));
                            bot.refresh_trusted_senders().await;
                        }
                        // Phase 8 Sync Hardening: treat empty incremental syncs as healthy;
                        // NEVER reset `since = None` on empty syncs. Atomically persist every next_batch.
                        if let Some(nb) = sync.get("next_batch").and_then(Value::as_str) {
                            since = Some(nb.to_string());
                        }
                        if let Err(e) = handle_sync(&mut bot, &sync).await {
                            warn!("Sync handler error: {}", e);
                        }
                        if let Err(e) = save_sync_cursor(&bot.cfg.cursor_file, &since, &bot.processed_events_order).await {
                            warn!("Failed to persist sync cursor: {e}");
                        }
                    }
                    Ok(Err(e)) => {
                        warn!("Sync error: {} -- retrying in 5s", e);
                        tokio::time::sleep(Duration::from_secs(5)).await;
                    }
                    Err(_) => {
                        warn!("Sync timeout -- retrying in 10s");
                        tokio::time::sleep(Duration::from_secs(10)).await;
                    }
                }
                false
            }
        };

        #[cfg(not(unix))]
        let should_stop = tokio::select! {
            _ = tokio::signal::ctrl_c() => true,
            result = timeout(Duration::from_secs(45), bot.sync(since.as_deref(), bot.cfg.sync_timeout_ms, false)) => {
                match result {
                    Ok(Ok(sync)) => {
                        sync_count += 1;
                        if let Some(nb) = sync.get("next_batch").and_then(Value::as_str) {
                            since = Some(nb.to_string());
                        }
                        if let Err(e) = handle_sync(&mut bot, &sync).await {
                            warn!("Sync handler error: {}", e);
                        }
                        let _ = save_sync_cursor(&bot.cfg.cursor_file, &since, &bot.processed_events_order).await;
                    }
                    Ok(Err(e)) => {
                        warn!("Sync error: {} -- retrying in 5s", e);
                        tokio::time::sleep(Duration::from_secs(5)).await;
                    }
                    Err(_) => {
                        warn!("Sync timeout -- retrying in 10s");
                        tokio::time::sleep(Duration::from_secs(10)).await;
                    }
                }
                false
            }
        };

        if should_stop {
            info!("Received shutdown signal -- saving cursor and shutting down...");
            let _ = save_sync_cursor(&bot.cfg.cursor_file, &since, &bot.processed_events_order).await;
            break;
        }
    }

    info!("Matrix bot stopped.");
    Ok(())
}

fn extract_invite_sender(invite_obj: &Value, my_user_id: &str) -> Option<String> {
    let events = invite_obj
        .get("invite_state")
        .and_then(|s| s.get("events"))
        .and_then(Value::as_array)?;

    // Look for the m.room.member invite event targeting our user_id
    for ev in events {
        let ev_type = ev.get("type").and_then(Value::as_str).unwrap_or("");
        let state_key = ev.get("state_key").and_then(Value::as_str).unwrap_or("");
        let membership = ev
            .get("content")
            .and_then(|c| c.get("membership"))
            .and_then(Value::as_str)
            .unwrap_or("");
        if ev_type == "m.room.member" && state_key == my_user_id && membership == "invite" {
            if let Some(sender) = ev.get("sender").and_then(Value::as_str) {
                return Some(sender.to_string());
            }
        }
    }
    // Fallback: any sender in invite_state events that isn't us
    for ev in events {
        if let Some(sender) = ev.get("sender").and_then(Value::as_str) {
            if sender != my_user_id {
                return Some(sender.to_string());
            }
        }
    }
    None
}

async fn handle_sync(bot: &mut Bot, sync: &Value) -> Result<()> {
    // Phase 8 Auto-Join: Only accept invites from trusted senders in platform `trusted_senders` table
    if let Some(invites) = sync.get("rooms").and_then(|r| r.get("invite")).and_then(Value::as_object) {
        if !invites.is_empty() {
            bot.refresh_trusted_senders().await;
        }
        for (room_id, invite_obj) in invites {
            let sender = extract_invite_sender(invite_obj, &bot.whoami_user_id).unwrap_or_else(|| "unknown".to_string());
            let invite_dedup_key = format!("invite:{}:{}", room_id, sender);
            if !bot.trusted_senders.contains(&sender) {
                if bot.record_processed_event(&invite_dedup_key) {
                    warn!(
                        "AUTO-JOIN REJECTED: Ignoring invite to room={} from untrusted sender={} (decision=reject_untrusted)",
                        room_id, sender
                    );
                }
                continue;
            }

            info!(
                "AUTO-JOIN ACCEPTED: Invite to room={} from trusted sender={} -- joining...",
                room_id, sender
            );
            let mut joined = false;
            for attempt in 0..4 {
                if attempt > 0 {
                    let delay = 5 * (attempt + 1);
                    info!("Retry {}/3 -- waiting {}s...", attempt, delay);
                    tokio::time::sleep(Duration::from_secs(delay as u64)).await;
                }
                if bot.join_room(room_id).await.unwrap_or(false) {
                    joined = true;
                    info!("Joined room: {} (attempt {}, inviter={})", room_id, attempt + 1, sender);
                    let hello = format!("Hello! I'm {}, an AI agent powered by Agent Zero.", bot.cfg.bot_display_name);
                    let _ = bot.send_message(room_id, &hello).await;
                    break;
                }
                warn!("Join attempt {}/4 failed for room={}", attempt + 1, room_id);
            }
            if !joined {
                error!("Failed to join {} after 4 attempts.", room_id);
            }
        }
    }

    let joined_rooms = sync
        .get("rooms")
        .and_then(|r| r.get("join"))
        .and_then(Value::as_object);
    if joined_rooms.is_none() {
        return Ok(());
    }

    for (room_id, room_obj) in joined_rooms.unwrap() {
        let timeline = room_obj
            .get("timeline")
            .and_then(|t| t.get("events"))
            .and_then(Value::as_array);
        if timeline.is_none() {
            continue;
        }
        for event in timeline.unwrap() {
            let event_type = event.get("type").and_then(Value::as_str).unwrap_or("");
            if event_type != "m.room.message" {
                continue;
            }
            let event_id = event.get("event_id").and_then(Value::as_str).unwrap_or("").to_string();
            let sender = event.get("sender").and_then(Value::as_str).unwrap_or("");

            // Phase 8 Self-Event Suppression using verified /whoami identity
            if sender == bot.whoami_user_id || sender == bot.cfg.user_id {
                info!(
                    "Event decision | room={} | event_id={} | sender={} | decision=drop_self_event",
                    room_id, event_id, sender
                );
                let _ = bot.record_processed_event(&event_id);
                continue;
            }

            // Phase 8 Bounded Persistent Event-ID Deduplication across restarts
            if !event_id.is_empty() && !bot.record_processed_event(&event_id) {
                info!(
                    "Event decision | room={} | event_id={} | sender={} | decision=drop_duplicate",
                    room_id, event_id, sender
                );
                continue;
            }

            let ts = event.get("origin_server_ts").and_then(Value::as_i64).unwrap_or(0);
            let now_ms = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
            if now_ms - ts > 300_000 {
                info!(
                    "Event decision | room={} | event_id={} | sender={} | decision=drop_stale_ts",
                    room_id, event_id, sender
                );
                continue;
            }
            let content = event.get("content").unwrap_or(&Value::Null);
            let msg_type = content.get("msgtype").and_then(Value::as_str).unwrap_or("");
            if msg_type != "m.text" {
                continue;
            }
            let raw_body = content
                .get("body")
                .and_then(Value::as_str)
                .unwrap_or("")
                .trim()
                .to_string();
            let mut body = strip_matrix_mention_pills(&raw_body).trim().to_string();
            if body.is_empty() {
                continue;
            }

            // Phase 8 Trigger Policy Enforcement: require declared mention/command prefix
            // EVEN in two-member (one-on-one) rooms to prevent agent-to-agent feedback loops.
            let body_lower = body.to_lowercase();
            let triggered = bot
                .cfg
                .trigger_prefixes
                .iter()
                .any(|p| body_lower.starts_with(&p.to_lowercase()));
            if !triggered {
                info!(
                    "Event decision | room={} | event_id={} | sender={} | decision=ignore_untriggered",
                    room_id, event_id, sender
                );
                continue;
            }
            for p in &bot.cfg.trigger_prefixes {
                if body_lower.starts_with(&p.to_lowercase()) {
                    body = body.chars().skip(p.chars().count()).collect::<String>().trim().to_string();
                    break;
                }
            }
            if body.is_empty() {
                continue;
            }

            info!(
                "Event decision | room={} | event_id={} | sender={} | decision=process_addressed",
                room_id, event_id, sender
            );

            if let Some(reply) = built_in_response(&body, &bot.cfg.agent_identity, &bot.cfg.user_id) {
                let _ = bot.send_message(room_id, &reply).await;
                continue;
            }

            let _ = bot.set_typing(room_id, true).await;
            let full_message = format!(
                "[MATRIX MESSAGE - reply with plain conversational text only, DO NOT use any Matrix tools, do not send messages via MCP. Keep responses concise and conversational - a few sentences max. No status reports or diagnostics unless explicitly asked.]\nFrom: {}\nRoom: {}\n\n{}",
                sender, room_id, body
            );
            let reply = bot.ask_agent_zero(&full_message, room_id, sender).await;
            let _ = bot.set_typing(room_id, false).await;

            for chunk in chunk_by_chars(&reply, MAX_CHARS_PER_MESSAGE) {
                if let Err(e) = bot.send_message(room_id, &chunk).await {
                    warn!("Failed to send response chunk: {}", e);
                    break;
                }
            }
        }
    }
    Ok(())
}

async fn append_crash_log(err: &str) -> Result<()> {
    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let path = std::env::current_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join("crash.log");
    let existing = fs::read_to_string(&path).await.unwrap_or_default();
    let mut out = existing;
    out.push_str("\n========================================================================\n");
    out.push_str(&format!("CRASH at {ts}\n"));
    out.push_str("========================================================================\n");
    out.push_str(err);
    out.push('\n');
    fs::write(path, out).await?;
    Ok(())
}
