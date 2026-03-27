use anyhow::{anyhow, Context, Result};
use dotenvy::dotenv;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde_json::json;

#[derive(Clone, Debug)]
struct Config {
    homeserver_url: String,
    user_id: String,
    access_token: String,
    device_id: String,
}

impl Config {
    fn from_env() -> Self {
        Self {
            homeserver_url: std::env::var("MATRIX_HOMESERVER_URL")
                .unwrap_or_else(|_| "http://localhost:8008".to_string()),
            user_id: std::env::var("MATRIX_USER_ID").unwrap_or_default(),
            access_token: std::env::var("MATRIX_ACCESS_TOKEN").unwrap_or_default(),
            device_id: std::env::var("MATRIX_DEVICE_ID").unwrap_or_else(|_| "AgentZeroBot".to_string()),
        }
    }
}

fn usage() {
    eprintln!("Usage:");
    eprintln!("  set-display-name-rust \"My Name\"");
    eprintln!("  set-display-name-rust \"Room Bot\" --room ROOM_ID");
    eprintln!("  set-display-name-rust --reset");
    eprintln!("  set-display-name-rust --list");
}

#[tokio::main]
async fn main() {
    let _ = dotenv();
    if let Err(e) = run().await {
        eprintln!("Error: {e}");
        std::process::exit(1);
    }
}

async fn run() -> Result<()> {
    let cfg = Config::from_env();
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() {
        usage();
        return Err(anyhow!("missing arguments"));
    }

    if args.iter().any(|a| a == "--list") {
        println!("Current Configuration:");
        println!("  Homeserver: {}", cfg.homeserver_url);
        println!("  User ID: {}", cfg.user_id);
        println!("  Device ID: {}", cfg.device_id);
        return Ok(());
    }

    if cfg.homeserver_url.is_empty() || cfg.user_id.is_empty() || cfg.access_token.is_empty() {
        return Err(anyhow!(
            "Missing required env vars: MATRIX_HOMESERVER_URL, MATRIX_USER_ID, MATRIX_ACCESS_TOKEN"
        ));
    }

    let mut name: Option<String> = None;
    let mut room_id: Option<String> = None;
    let mut reset = false;

    let mut i = 0usize;
    while i < args.len() {
        match args[i].as_str() {
            "--room" | "-r" => {
                if i + 1 >= args.len() {
                    return Err(anyhow!("--room requires ROOM_ID"));
                }
                room_id = Some(args[i + 1].clone());
                i += 2;
            }
            "--reset" => {
                reset = true;
                i += 1;
            }
            x if x.starts_with("--") => {
                return Err(anyhow!("unknown flag: {}", x));
            }
            value => {
                if name.is_none() {
                    name = Some(value.to_string());
                    i += 1;
                } else {
                    return Err(anyhow!("unexpected argument: {}", value));
                }
            }
        }
    }

    if reset {
        let default_name = cfg
            .user_id
            .split(':')
            .next()
            .unwrap_or("Agent")
            .trim_start_matches('@')
            .to_string();
        set_global_display_name(&cfg, &default_name).await?;
        println!("Global display name reset to: {}", default_name);
        return Ok(());
    }

    let name = name.ok_or_else(|| anyhow!("Please provide a display name or use --reset"))?;
    if let Some(room) = room_id {
        set_room_display_name(&cfg, &room, &name).await?;
        println!("Room display name set to: {}", name);
        println!("Room: {}", room);
    } else {
        set_global_display_name(&cfg, &name).await?;
        println!("Global display name set to: {}", name);
    }
    Ok(())
}

fn client(cfg: &Config) -> Result<reqwest::Client> {
    let mut headers = HeaderMap::new();
    headers.insert(
        AUTHORIZATION,
        HeaderValue::from_str(&format!("Bearer {}", cfg.access_token)).context("invalid MATRIX_ACCESS_TOKEN")?,
    );
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
    reqwest::Client::builder()
        .default_headers(headers)
        .build()
        .context("build reqwest client")
}

async fn set_global_display_name(cfg: &Config, name: &str) -> Result<()> {
    let user_enc = urlencoding::encode(&cfg.user_id);
    let url = format!(
        "{}/_matrix/client/v3/profile/{}/displayname",
        cfg.homeserver_url.trim_end_matches('/'),
        user_enc
    );
    let resp = client(cfg)?.put(url).json(&json!({ "displayname": name })).send().await?;
    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(anyhow!("set display name failed {status}: {body}"));
    }
    Ok(())
}

async fn set_room_display_name(cfg: &Config, room_id: &str, name: &str) -> Result<()> {
    let room_enc = urlencoding::encode(room_id);
    let user_enc = urlencoding::encode(&cfg.user_id);
    let url = format!(
        "{}/_matrix/client/v3/rooms/{}/state/m.room.member/{}",
        cfg.homeserver_url.trim_end_matches('/'),
        room_enc,
        user_enc
    );
    let payload = json!({
        "displayname": name,
        "membership": "join"
    });
    let resp = client(cfg)?.put(url).json(&payload).send().await?;
    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(anyhow!("set room display name failed {status}: {body}"));
    }
    Ok(())
}
