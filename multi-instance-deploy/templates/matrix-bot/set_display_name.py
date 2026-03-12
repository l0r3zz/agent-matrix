#!/usr/bin/env python3
"""
Set Matrix Bot Display Name - Globally or Per-Room
====================================================
Usage:
    python3 set_display_name.py "My Cool Name"              # Set global display name
    python3 set_display_name.py "Room Bot" --room ROOM_ID   # Set per-room display name
    python3 set_display_name.py --reset                     # Reset to default (user ID)

Author: Agent Zero
Version: 1.0
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from nio import AsyncClient

# Load environment
BOT_DIR = Path(__file__).parent
load_dotenv(BOT_DIR / ".env")

HOMESERVER_URL = os.getenv("MATRIX_HOMESERVER_URL", "http://localhost:8008")
USER_ID = os.getenv("MATRIX_USER_ID", "")
ACCESS_TOKEN = os.getenv("MATRIX_ACCESS_TOKEN", "")
DEVICE_ID = os.getenv("MATRIX_DEVICE_ID", "AgentZeroBot")


async def set_global_display_name(name: str):
    """Set display name globally (all rooms)."""
    if not all([HOMESERVER_URL, USER_ID, ACCESS_TOKEN]):
        print("❌ Error: Missing required environment variables")
        print("   Need: MATRIX_HOMESERVER_URL, MATRIX_USER_ID, MATRIX_ACCESS_TOKEN")
        sys.exit(1)
    
    client = AsyncClient(
        homeserver=HOMESERVER_URL,
        user=USER_ID,
        device_id=DEVICE_ID,
    )
    client.access_token = ACCESS_TOKEN
    client.user_id = USER_ID
    
    try:
        response = await client.set_displayname(name)
        if hasattr(response, 'displayname'):
            print(f"✅ Global display name set to: {name}")
        else:
            print(f"⚠️  Response: {response}")
    except Exception as e:
        print(f"❌ Error setting display name: {e}")
    finally:
        await client.close()


async def set_room_display_name(room_id: str, name: str):
    """Set display name for a specific room."""
    if not all([HOMESERVER_URL, USER_ID, ACCESS_TOKEN]):
        print("❌ Error: Missing required environment variables")
        sys.exit(1)
    
    client = AsyncClient(
        homeserver=HOMESERVER_URL,
        user=USER_ID,
        device_id=DEVICE_ID,
    )
    client.access_token = ACCESS_TOKEN
    client.user_id = USER_ID
    
    try:
        content = {
            "displayname": name,
            "membership": "join"
        }
        response = await client.room_put_state(
            room_id=room_id,
            event_type="m.room.member",
            content=content,
            state_key=USER_ID
        )
        if hasattr(response, 'event_id'):
            print(f"✅ Room display name set to: {name}")
            print(f"   Room: {room_id}")
        else:
            print(f"⚠️  Response: {response}")
    except Exception as e:
        print(f"❌ Error setting room display name: {e}")
    finally:
        await client.close()


async def reset_display_name():
    """Reset display name to default (user ID localpart)."""
    default_name = USER_ID.split(":")[0].lstrip("@") if USER_ID else "Agent"
    await set_global_display_name(default_name)


async def main():
    parser = argparse.ArgumentParser(
        description="Set Matrix bot display name globally or per-room"
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="Display name to set"
    )
    parser.add_argument(
        "--room", "-r",
        help="Room ID to set per-room display name"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset to default display name"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Show current configuration"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("📋 Current Configuration:")
        print(f"   Homeserver: {HOMESERVER_URL}")
        print(f"   User ID: {USER_ID}")
        print(f"   Device ID: {DEVICE_ID}")
        return
    
    if args.reset:
        await reset_display_name()
        return
    
    if not args.name:
        print("❌ Error: Please provide a display name or use --reset")
        parser.print_help()
        sys.exit(1)
    
    if args.room:
        await set_room_display_name(args.room, args.name)
    else:
        await set_global_display_name(args.name)


if __name__ == "__main__":
    asyncio.run(main())
