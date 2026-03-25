#!/usr/bin/env python3
"""
用已保存的 Token 调用建必优 API，验证可用性
"""

import json
import sys
import os
import urllib.request
import urllib.error
from pathlib import Path

CREDENTIALS_FILE = Path.home() / ".openclaw" / "workspace" / ".jianyouyou_credentials.json"
BASE_URL = "http://192.168.2.17:8080"

# 用于验证的轻量接口（返回当前用户信息）
VERIFY_ENDPOINT = f"{BASE_URL}/api/user/current"


def load_token() -> str:
    if not CREDENTIALS_FILE.exists():
        print("VERIFY_FAILED: 凭据文件不存在，请先登录")
        sys.exit(1)
    with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
        creds = json.load(f)
    token = creds.get("token")
    if not token:
        print("VERIFY_FAILED: 凭据文件中无 token")
        sys.exit(1)
    return token, creds.get("token_type", "Bearer")


def main():
    token, token_type = load_token()

    req = urllib.request.Request(
        VERIFY_ENDPOINT,
        headers={
            "Authorization": f"{token_type} {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)

            # 提取用户信息并回写到凭据文件
            user_info = data.get("data", data)
            if user_info:
                with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    creds = json.load(f)
                creds["user_info"] = {
                    "username": user_info.get("username", ""),
                    "real_name": user_info.get("realName", user_info.get("real_name", "")),
                    "org": user_info.get("orgName", ""),
                }
                with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
                    json.dump(creds, f, ensure_ascii=False, indent=2)

            print("VERIFY_SUCCESS")
            print(f"USER: {user_info.get('realName', user_info.get('username', '未知用户'))}")
            print(f"ORG: {user_info.get('orgName', '')}")

    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("VERIFY_FAILED: Token 无效或已失效（401 Unauthorized），请重新登录")
        else:
            print(f"VERIFY_FAILED: HTTP {e.code} - {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"VERIFY_FAILED: 无法连接建必优服务器 ({BASE_URL}) - {e.reason}")
        print(f"[HINT] 请确认电脑与 192.168.2.17 在同一局域网，且服务已启动")
        sys.exit(1)


if __name__ == "__main__":
    main()
