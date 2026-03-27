#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

settings_path = Path('/a0/usr/settings.json')
mcp_env_path = Path('/a0/usr/workdir/matrix-mcp-server/.env')

# Extract token from MCP env
mcp_token = ''
for line in mcp_env_path.read_text().splitlines():
    if line.startswith('MATRIX_ACCESS_TOKEN='):
        mcp_token = line.split('=',1)[1].strip().strip('"').strip("'")
        break

if not mcp_token:
    raise SystemExit('MATRIX_ACCESS_TOKEN not found in MCP .env')

obj = json.loads(settings_path.read_text())
servers_val = obj.get('mcp_servers')
if servers_val is None:
    raise SystemExit('settings.json missing mcp_servers')

# In this environment mcp_servers is a STRING containing JSON.
if isinstance(servers_val, str):
    inner = servers_val
    # Replace matrix_access_token value inside the string (robust enough here)
    # Example: "matrix_access_token": "GfBR...."
    new_inner, n = re.subn(r'("matrix_access_token"\s*:\s*")([^"]*)("\s*)', r'\1' + mcp_token + r'\3', inner, count=1)
    if n != 1:
        # If key not found, try to inject where headers live.
        # Fail loudly so we don't corrupt configs silently.
        raise SystemExit('Could not find matrix_access_token inside settings.json mcp_servers string')
    obj['mcp_servers'] = new_inner
else:
    raise SystemExit(f'Unexpected type for mcp_servers: {type(servers_val).__name__}')

settings_path.write_text(json.dumps(obj, indent=4, ensure_ascii=False))
print('Updated settings.json mcp_servers.headers.matrix_access_token to match MCP .env')
