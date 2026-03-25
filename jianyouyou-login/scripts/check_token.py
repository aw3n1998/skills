#!/usr/bin/env python3
"""
检查本地建必优 Token 是否存在且有效
输出：TOKEN_VALID | TOKEN_EXPIRED | TOKEN_NOT_FOUND
"""

import json
import sys
from datetime import datetime
from pathlib import Path

CREDENTIALS_FILE = Path.home() / ".openclaw" / "workspace" / ".jianyouyou_credentials.json"
# 提前多少秒判定为"即将过期"（默认提前 10 分钟刷新）
EXPIRY_BUFFER_SECONDS = 600


def main():
    if not CREDENTIALS_FILE.exists():
        print("TOKEN_NOT_FOUND")
        sys.exit(1)

    try:
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            creds = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"TOKEN_NOT_FOUND: 凭据文件损坏 ({e})")
        sys.exit(1)

    token = creds.get("token")
    expires_at_str = creds.get("expires_at")

    if not token:
        print("TOKEN_NOT_FOUND: token 字段为空")
        sys.exit(1)

    if not expires_at_str:
        # 没有过期时间，保守认为有效
        print("TOKEN_VALID")
        user_info = creds.get("user_info", {})
        if user_info.get("username"):
            print(f"USER: {user_info.get('real_name', user_info.get('username', ''))}")
        sys.exit(0)

    try:
        expires_at = datetime.fromisoformat(expires_at_str)
    except ValueError:
        print("TOKEN_EXPIRED: 过期时间格式异常，建议重新登录")
        sys.exit(1)

    now = datetime.now()
    remaining = (expires_at - now).total_seconds()

    if remaining <= EXPIRY_BUFFER_SECONDS:
        print(f"TOKEN_EXPIRED: token 已过期或即将过期（剩余 {max(0, int(remaining))} 秒）")
        sys.exit(1)

    print("TOKEN_VALID")
    print(f"TOKEN_EXPIRES_AT: {expires_at_str}")
    print(f"REMAINING_SECONDS: {int(remaining)}")

    user_info = creds.get("user_info", {})
    if user_info.get("username"):
        print(f"USER: {user_info.get('real_name', user_info.get('username', ''))}")


if __name__ == "__main__":
    main()
