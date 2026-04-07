use anyhow::{anyhow, Context, Result};
use dotenvy::dotenv;
use log::{error, info, warn};
use pulldown_cmark::{html, Options, Parser};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::fs;
use tokio::time::timeout;

const MAX_CHARS_PER_MESSAGE: usize = 32000;

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
            // Potential mention pill: look for closing `](https://matrix.to/`
            if let Some(bracket_close) = chars[i..].iter().position(|&c| c == ']') {
                let bracket_close = i + bracket_close;
                // Check for `](https://matrix.to/` after the closing bracket
                let after = bracket_close + 1;
                if after < len && chars[after] == '(' {
                    // Find the closing paren
                    if let Some(paren_close) = chars[after..].iter().position(|&c| c == ')') {
                        let paren_close = after + paren_close;
                        let link: String = chars[after + 1..paren_close].iter().collect();
                        if link.starts_with("https://matrix.to/") {
                            // Extract the mention text (without brackets)
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
    bot_start_time_ms: i64,
    trigger_prefixes: Vec<String>,
}

#[derive(Debug, Default, Serialize, Deserialize)]
struct RoomState {
    #[serde(flatten)]
    room_contexts: HashMap<String, String>,
}

struct Bot {
    cfg: Config,
    matrix_client: reqwest::Client,
    a0_client: reqwest::Client,
    state: RoomState,
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
        let a0_api_key = std::env::var("A0_API_KEY").unwrap_or_default();
        let bot_display_name = std::env::var("BOT_DISPLAY_NAME").unwrap_or_else(|_| "Agent Zero".to_string());
        let agent_identity = std::env::var("AGENT_IDENTITY").unwrap_or_else(|_| bot_display_name.clone());
        let sync_timeout_ms = std::env::var("SYNC_TIMEOUT_MS")
            .ok()
            .and_then(|v| v.parse::<u64>().ok())
            .unwrap_or(30000);

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

        let bot_start_time_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as i64;
        let state_file = bot_dir.join("room_contexts.json");

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
            bot_start_time_ms,
            trigger_prefixes,
        })
    }
}

impl Bot {
    async fn new(cfg: Config) -> Result<Self> {
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
        Ok(Self {
            cfg,
            matrix_client,
            a0_client,
            state,
        })
    }

    fn matrix_url(&self, path: &str) -> String {
        format!("{}{}", self.cfg.homeserver_url.trim_end_matches('/'), path)
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
    fs::write(path, json).await?;
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
    let mut bot = Bot::new(cfg).await?;
    bot.set_display_name().await;

    let mut since: Option<String>;

    let mut attempt = 0u32;
    loop {
        attempt += 1;
        match timeout(Duration::from_secs(60), bot.sync(None, 10000, true)).await {
            Ok(Ok(sync)) => {
                since = sync.get("next_batch").and_then(Value::as_str).map(ToString::to_string);
                info!(
                    "Initial sync complete. Next batch: {}",
                    since.clone().unwrap_or_default()
                );
                handle_sync(&mut bot, &sync).await?;
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
    let mut empty_sync_count: u32 = 0;
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
                            info!("Sync loop heartbeat: {} syncs completed", sync_count);
                        }
                        // Check if this is an empty/stale sync
                        let has_rooms = sync.get("rooms").and_then(Value::as_object)
                            .map(|r| !r.is_empty()).unwrap_or(false);
                        if !has_rooms {
                            empty_sync_count += 1;
                            if empty_sync_count >= 5 {
                                warn!("Consecutive empty syncs: {} -- forcing full sync (clearing since token)", empty_sync_count);
                                since = None;
                                empty_sync_count = 0;
                            }
                        } else {
                            empty_sync_count = 0;
                        }
                        since = sync.get("next_batch").and_then(Value::as_str).map(ToString::to_string);
                        if let Err(e) = handle_sync(&mut bot, &sync).await {
                            warn!("Sync handler error: {}", e);
                        }
                    }
                    Ok(Err(e)) => {
                        empty_sync_count += 1;
                        if empty_sync_count >= 5 {
                            warn!("Consecutive sync errors/timeouts: {} -- forcing full sync", empty_sync_count);
                            since = None;
                            empty_sync_count = 0;
                        }
                        warn!("Sync error: {} -- retrying in 5s", e);
                        tokio::time::sleep(Duration::from_secs(5)).await;
                    }
                    Err(_) => {
                        empty_sync_count += 1;
                        if empty_sync_count >= 5 {
                            warn!("Consecutive sync timeouts: {} -- forcing full sync", empty_sync_count);
                            since = None;
                            empty_sync_count = 0;
                        }
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
                        if sync_count % 60 == 0 {
                            info!("Sync loop heartbeat: {} syncs completed", sync_count);
                        }
                        let has_rooms = sync.get("rooms").and_then(Value::as_object)
                            .map(|r| !r.is_empty()).unwrap_or(false);
                        if !has_rooms {
                            empty_sync_count += 1;
                            if empty_sync_count >= 5 {
                                warn!("Consecutive empty syncs: {} -- forcing full sync", empty_sync_count);
                                since = None;
                                empty_sync_count = 0;
                            }
                        } else {
                            empty_sync_count = 0;
                        }
                        since = sync.get("next_batch").and_then(Value::as_str).map(ToString::to_string);
                        if let Err(e) = handle_sync(&mut bot, &sync).await {
                            warn!("Sync handler error: {}", e);
                        }
                    }
                    Ok(Err(e)) => {
                        empty_sync_count += 1;
                        if empty_sync_count >= 5 {
                            warn!("Consecutive sync errors/timeouts: {} -- forcing full sync", empty_sync_count);
                            since = None;
                            empty_sync_count = 0;
                        }
                        warn!("Sync error: {} -- retrying in 5s", e);
                        tokio::time::sleep(Duration::from_secs(5)).await;
                    }
                    Err(_) => {
                        empty_sync_count += 1;
                        if empty_sync_count >= 5 {
                            warn!("Consecutive sync timeouts: {} -- forcing full sync", empty_sync_count);
                            since = None;
                            empty_sync_count = 0;
                        }
                        warn!("Sync timeout -- retrying in 10s");
                        tokio::time::sleep(Duration::from_secs(10)).await;
                    }
                }
                false
            }
        };

        if should_stop {
            info!("Received shutdown signal -- shutting down...");
            break;
        }
    }

    info!("Matrix bot stopped.");
    Ok(())
}

async fn handle_sync(bot: &mut Bot, sync: &Value) -> Result<()> {
    if let Some(invites) = sync.get("rooms").and_then(|r| r.get("invite")).and_then(Value::as_object) {
        for (room_id, _) in invites {
            info!("Invited to {} -- joining...", room_id);
            let mut joined = false;
            for attempt in 0..4 {
                if attempt > 0 {
                    let delay = 5 * (attempt + 1);
                    info!("Retry {}/3 -- waiting {}s...", attempt, delay);
                    tokio::time::sleep(Duration::from_secs(delay as u64)).await;
                }
                if bot.join_room(room_id).await.unwrap_or(false) {
                    joined = true;
                    info!("Joined room: {} (attempt {})", room_id, attempt + 1);
                    let hello = format!("Hello! I'm {}, an AI agent powered by Agent Zero.", bot.cfg.bot_display_name);
                    let _ = bot.send_message(room_id, &hello).await;
                    break;
                }
                warn!("Join attempt {}/4 failed", attempt + 1);
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
        let member_count = room_obj
            .get("summary")
            .and_then(|s| s.get("m.joined_member_count"))
            .and_then(Value::as_i64);
        let is_one_on_one = member_count.map(|c| c == 2).unwrap_or(true);
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
            let sender = event.get("sender").and_then(Value::as_str).unwrap_or("");
            if sender == bot.cfg.user_id {
                continue;
            }
            let ts = event.get("origin_server_ts").and_then(Value::as_i64).unwrap_or(0);
            if ts < bot.cfg.bot_start_time_ms.saturating_sub(10_000) {
                continue;
            }
            let content = event.get("content").unwrap_or(&Value::Null);
            let msg_type = content.get("msgtype").and_then(Value::as_str).unwrap_or("");
            if msg_type != "m.text" {
                continue;
            }
            let mut body = content
                .get("body")
                .and_then(Value::as_str)
                .unwrap_or("")
                .trim()
                .to_string();
            // Normalize Matrix mention pills: convert Element's
            // [@user:server](https://matrix.to/#/@user:server) to plain @user:server
            let mut body = strip_matrix_mention_pills(&body).trim().to_string();
            if body.is_empty() {
                continue;
            }

            let body_lower = body.to_lowercase();
            let triggered = bot
                .cfg
                .trigger_prefixes
                .iter()
                .any(|p| body_lower.starts_with(&p.to_lowercase()));
            if !is_one_on_one && !triggered {
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

            info!("Message in {} from {}: {}", room_id, sender, body);

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
