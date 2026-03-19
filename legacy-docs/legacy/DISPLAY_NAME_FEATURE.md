# Bot Display Name Feature - Deployment Notes
**Date:** 2026-03-12  
**Version:** Display Name Support v1.0

## Changes Made

### 1. matrix_bot.py
- Added automatic display name setting on bot startup
- Location: After `client.access_token = ACCESS_TOKEN`
- Uses: `BOT_DISPLAY_NAME` from environment
- API: `client.set_displayname(BOT_DISPLAY_NAME)`

### 2. set_display_name.py (NEW)
Created utility script with commands:
```bash
python3 set_display_name.py "Name"           # Global display name
python3 set_display_name.py "Name" -r ROOM   # Per-room display name  
python3 set_display_name.py --reset          # Reset to default
python3 set_display_name.py --list           # Show config
```

### 3. .env.template
Added comments for BOT_DISPLAY_NAME and AGENT_IDENTITY

### 4. multi-instance-guide.md
Added "Bot Display Names (Matrix Aliases)" section with:
- Configuration instructions
- Usage examples
- Technical API details table

### 5. operations-manual.md  
Added "Appendix: Bot Display Name Configuration" with:
- Environment variable reference
- File locations
- Usage examples

## Deployment to g2s

Run from g2s host or with SSH:
```bash
# On g2s:
cd /opt/agent-zero/multi-instance-deploy
rsync -av templates/matrix-bot/ /opt/agent-zero/multi-instance-deploy/templates/matrix-bot/

# Or use existing sync script:
./scripts/sync-fleet.sh
```

## Files Changed
- templates/matrix-bot/matrix_bot.py (modified)
- templates/matrix-bot/set_display_name.py (created)
- templates/matrix-bot/.env.template (comments added)
- multi-instance-guide.md (section added)
- operations-manual.md (appendix added)

## Backups Created
- matrix_bot.py.pre-displayname
