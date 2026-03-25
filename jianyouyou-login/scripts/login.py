#!/usr/bin/env python3
"""
建必优登录脚本
流程：启动本地 HTTP 回调服务 → 打开授权页 → 接收 token → 保存到本地
"""

import http.server
import threading
import webbrowser
import json
import os
import sys
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from pathlib import Path

# ── 配置区 ────────────────────────────────────────────────────────────
CONFIG = {
    # 建必优服务器地址
    "BASE_URL": "http://192.168.2.99:8080",
    # 登录页路径（直接打开 /ai 登录页，用户在页面完成账密登录后跳转回调）
    "AUTH_PATH": "/ai",
    # 客户端 ID
    "CLIENT_ID": "qclaw-agent",
    # Token 保存路径（Windows 路径兼容）
    "CREDENTIALS_FILE": Path.home() / ".openclaw" / "workspace" / ".jianyouyou_credentials.json",
    # 本地回调端口
    "CALLBACK_PORT_START": 19877,
    # 等待用户登录超时（秒）
    "TIMEOUT": 180,
}
# ─────────────────────────────────────────────────────────────────────

received_data: dict = {}
server_instance = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """接收建必优回调的临时 HTTP 服务"""

    def do_GET(self):
        parsed = urlparse(self.path)

        # 只处理 /callback 路径
        if not parsed.path.startswith("/callback"):
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)

        # 提取 token（支持两种回调格式）
        token = (
            params.get("token", [None])[0]
            or params.get("access_token", [None])[0]
        )
        error = params.get("error", [None])[0]

        if token:
            received_data["token"] = token
            received_data["token_type"] = params.get("token_type", ["Bearer"])[0]
            received_data["expires_in"] = int(params.get("expires_in", [28800])[0])  # 默认 8h
            received_data["success"] = True
            html = self._success_html()
        elif error:
            received_data["error"] = error
            received_data["success"] = False
            html = self._error_html(error)
        else:
            received_data["error"] = "回调参数缺失"
            received_data["success"] = False
            html = self._error_html("回调参数缺失")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        """支持 POST 形式的 token 回调（部分建必优版本使用）"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            token = data.get("token") or data.get("access_token")
            if token:
                received_data["token"] = token
                received_data["token_type"] = data.get("token_type", "Bearer")
                received_data["expires_in"] = data.get("expires_in", 28800)
                received_data["user_info"] = data.get("user_info", {})
                received_data["success"] = True
                html = self._success_html()
            else:
                received_data["error"] = "POST body 中未找到 token"
                received_data["success"] = False
                html = self._error_html("未找到 token")
        except json.JSONDecodeError:
            # 尝试 form 格式
            from urllib.parse import parse_qs
            form = parse_qs(body.decode("utf-8", errors="ignore"))
            token = (form.get("token", [None])[0] or form.get("access_token", [None])[0])
            if token:
                received_data["token"] = token
                received_data["success"] = True
                html = self._success_html()
            else:
                received_data["error"] = "无法解析回调数据"
                received_data["success"] = False
                html = self._error_html("无法解析回调数据")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _success_html(self):
        return """<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>授权成功</title>
<style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f0f9f0;}
.box{text-align:center;padding:40px;background:white;border-radius:12px;box-shadow:0 2px 20px rgba(0,0,0,.1);}
h2{color:#22c55e;} p{color:#666;}</style></head>
<body><div class="box">
<h2>✅ 授权成功</h2>
<p>Token 已获取，正在回传到 QClaw...</p>
<p style="margin-top:20px;color:#999;font-size:13px">此页面可以关闭</p>
<script>setTimeout(()=>window.close(),2000)</script>
</div></body></html>"""

    def _error_html(self, error):
        return f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>授权失败</title>
<style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#fff0f0;}}
.box{{text-align:center;padding:40px;background:white;border-radius:12px;box-shadow:0 2px 20px rgba(0,0,0,.1);}}
h2{{color:#ef4444;}} p{{color:#666;}}</style></head>
<body><div class="box">
<h2>❌ 授权失败</h2>
<p>错误信息：{error}</p>
<p style="margin-top:20px;color:#999;font-size:13px">请关闭此页面后重试</p>
</div></body></html>"""

    def log_message(self, format, *args):
        pass  # 静默，不打印 HTTP 日志


def find_free_port(start: int) -> int:
    """从 start 开始找一个可用端口"""
    import socket
    for port in range(start, start + 5):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("无法找到可用端口（19877-19881 全部被占用）")


def start_callback_server(port: int):
    """在独立线程中启动回调 HTTP 服务"""
    global server_instance
    server_instance = http.server.HTTPServer(("127.0.0.1", port), CallbackHandler)
    server_instance.handle_request()  # 收到一次请求后退出


def save_credentials(token_data: dict):
    """保存 token 到本地文件"""
    credentials_file = CONFIG["CREDENTIALS_FILE"]
    credentials_file.parent.mkdir(parents=True, exist_ok=True)

    expires_at = (
        datetime.now() + timedelta(seconds=token_data.get("expires_in", 28800))
    ).isoformat()

    credentials = {
        "token": token_data["token"],
        "token_type": token_data.get("token_type", "Bearer"),
        "expires_at": expires_at,
        "user_info": token_data.get("user_info", {}),
        "saved_at": datetime.now().isoformat(),
    }

    with open(credentials_file, "w", encoding="utf-8") as f:
        json.dump(credentials, f, ensure_ascii=False, indent=2)

    return expires_at


def main():
    port = find_free_port(CONFIG["CALLBACK_PORT_START"])
    redirect_uri = f"http://127.0.0.1:{port}/callback"

    # 建必优登录页地址，附带 callback_url 参数
    # 建必优前端登录成功后，需要重定向到 callback_url?token=xxx
    # 如果建必优前端不支持 callback_url 参数，可以直接打开登录页，
    # 由用户登录后手动触发，或由前端 postMessage 发送 token
    login_url = (
        f"{CONFIG['BASE_URL']}{CONFIG['AUTH_PATH']}"
        f"?callback_url={redirect_uri}"
    )

    # 启动本地回调服务（后台线程）
    server_thread = threading.Thread(target=start_callback_server, args=(port,), daemon=True)
    server_thread.start()

    print(f"[INFO] 本地回调监听已启动：{redirect_uri}", flush=True)
    print(f"[INFO] 正在打开建必优登录页：{login_url}", flush=True)
    webbrowser.open(login_url)
    print(f"[INFO] 请在浏览器中完成账号密码登录，最长等待 {CONFIG['TIMEOUT']} 秒...", flush=True)

    # 等待回调
    deadline = time.time() + CONFIG["TIMEOUT"]
    while time.time() < deadline:
        if received_data:
            break
        time.sleep(0.5)

    if not received_data:
        print("LOGIN_TIMEOUT: 等待超时，用户未在规定时间内完成登录", flush=True)
        print(f"[HINT] 如建必优前端不支持自动回调，请参考 references/config.md 中的前端改造说明", flush=True)
        sys.exit(1)

    if not received_data.get("success"):
        error = received_data.get("error", "未知错误")
        print(f"LOGIN_FAILED: {error}", flush=True)
        sys.exit(1)

    expires_at = save_credentials(received_data)
    print(f"LOGIN_SUCCESS", flush=True)
    print(f"TOKEN_EXPIRES_AT: {expires_at}", flush=True)
    print(f"CREDENTIALS_FILE: {CONFIG['CREDENTIALS_FILE']}", flush=True)


if __name__ == "__main__":
    main()
