---
name: jianyouyou-login
description: >
  登录建必优（建筑工程质量管理平台）并获取认证 Token。
  Use when: 用户说"登录建必优"、"建必优登录"、"获取建必优token"、"建必优授权"。
  NOT for: 其他平台的登录，或已有有效 token 的情况。
version: 1.0.0
author: King
user-invocable: true
metadata:
  openclaw:
    emoji: "🏗️"
    skillKey: "jianyouyou-login"
    requires:
      bins:
        - python3
---

# 建必优登录 Skill

## Description

自动完成建必优平台的 OAuth 登录授权流程：启动本地回调服务 → 打开授权页 → 等待用户扫码/登录 → 接收回调 Token → 保存到本地供后续调用使用。

## When to Use

- 用户说"登录建必优"
- 用户说"建必优登录"、"建必优授权"
- 用户说"获取建必优 token"
- 调用建必优 API 前发现 token 不存在或已过期
- 用户说"我要操作建必优"（先检查 token，若无则触发登录）

## When NOT to Use

- Token 文件已存在且未过期（先用 `check-token` 步骤验证）
- 用户明确说使用已有凭据
- 非建必优平台的登录场景

## Workflow

### Step 1：检查已有 Token

执行以下命令检查本地是否已有有效 token：

```bash
python3 ~/.openclaw/workspace/skills/jianyouyou-login/scripts/check_token.py
```

- 若返回 `TOKEN_VALID`，告知用户"建必优 token 有效，无需重新登录"，**结束流程**
- 若返回 `TOKEN_EXPIRED` 或 `TOKEN_NOT_FOUND`，继续 Step 2

### Step 2：启动本地回调服务并打开授权页

执行登录脚本，脚本会自动：
1. 在本地 `127.0.0.1:19877` 启动临时 HTTP 回调服务
2. 用系统浏览器打开建必优授权页
3. 等待用户完成扫码/账密登录（最长 3 分钟）

```bash
python3 ~/.openclaw/workspace/skills/jianyouyou-login/scripts/login.py
```

告知用户："✅ 已打开建必优授权页，请在浏览器中完成登录..."

### Step 3：等待回调并保存 Token

脚本执行完毕后：

- 若输出包含 `LOGIN_SUCCESS`：
  - 告知用户"✅ 建必优登录成功，Token 已保存"
  - 输出 token 有效期信息（从脚本输出中提取）

- 若输出包含 `LOGIN_TIMEOUT`：
  - 告知用户"⏰ 登录超时（3分钟内未完成），请重试"

- 若输出包含 `LOGIN_FAILED`：
  - 告知用户错误原因（从脚本输出中提取）

### Step 4：验证可用性（可选）

登录成功后，执行一次轻量 API 验证：

```bash
python3 ~/.openclaw/workspace/skills/jianyouyou-login/scripts/verify_token.py
```

输出验证结果，告知用户是否可以正常调用建必优 API。

## Token 存储位置

Token 保存在：`~/.openclaw/workspace/.jianyouyou_credentials.json`

格式：
```json
{
  "token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_at": "2026-04-01T10:00:00",
  "user_info": {
    "username": "xxx",
    "real_name": "xxx"
  }
}
```

## 注意事项

- 回调端口 `19877`，若被占用脚本会自动尝试 `19878`、`19879`
- Token 有效期一般为 8 小时，过期后需重新登录
- 授权页 URL 在 `references/config.md` 中配置，可按实际建必优部署地址修改
