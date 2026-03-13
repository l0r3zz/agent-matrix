#!/usr/bin/env python3
import json, sys, os

env_file = sys.argv[1] if len(sys.argv) > 1 else '/a0/usr/workdir/matrix-mcp-server/.env'
settings_file = sys.argv[2] if len(sys.argv) > 2 else '/a0/usr/settings.json'

def get_env_token(path):
    if not os.path.exists(path): return ''
    for line in open(path):
        if line.startswith('MATRIX_ACCESS_TOKEN='):
            return line.split('=',1)[1].strip().strip('"').strip("'")
    return ''

def get_a0_token(path):
    if not os.path.exists(path): return ''
    try:
        s = json.load(open(path))
        mcp = json.loads(s.get('mcp_servers', '[]'))
        for srv in mcp:
            t = srv.get('headers', {}).get('matrix_access_token', '')
            if t: return t
    except: pass
    return ''

env_tok = get_env_token(env_file)
a0_tok = get_a0_token(settings_file)

if not env_tok or not a0_tok:
    print('SKIP')
elif env_tok == a0_tok:
    print('MATCH')
else:
    print(f'MISMATCH env={env_tok[:8]}... a0={a0_tok[:8]}...')
