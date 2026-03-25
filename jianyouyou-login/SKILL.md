---
name: jianyouyou-login
description: >
  登录建必优（建筑工程质量管理平台）并获取认证 Token。
  Use when: 用户说"登录建必优"、"建必优登录"、"获取建必优token"、"建必优授权"。
  NOT for: 其他平台的登录，或已有有效 token 的情况。
version: 1.2.0
author: King
user-invocable: true
metadata:
  openclaw:
    emoji: "🏗️"
    skillKey: "jianyouyou-login"
requires:
  bins:
    - python3
    - curl
---

# 建必优登录 Skill

## Description

自动完成建必优平台登录授权流程：从 GitHub 拉取最新脚本 → 启动本地回调服务 → 打开登录页 → 等待用户完成账密登录 → 接收回调 Token → 保存到本地供后续调用使用。

脚本托管在 GitHub，每次执行自动拉取最新版本，无需重新安装 Skill。

## When to Use

- 用户说"登录建必优"
- 用户说"建必优登录"、"建必优授权"
- 用户说"获取建必优 token"
- 调用建必优 API 前发现 token 不存在或已过期
- 用户说"我要操作建必优"（先检查 token，若无则触发登录）

## When NOT to Use

- Token 文件已存在且未过期（先用 Step 1 检查）
- 用户明确说使用已有凭据
- 非建必优平台的登录场景

## GitHub 脚本基础地址

```
https://raw.githubusercontent.com/aw3n1998/skills/main/jianyouyou-login/scripts/
```

## Workflow

### Step 1：检查已有 Token

从 GitHub 拉取 check_token.py 并执行：

```bash
curl -fsSL https://raw.githubusercontent.com/aw3n1998/skills/main/jianyouyou-login/scripts/check_token.py | python3
```

- 若输出包含 `TOKEN_VALID`，告知用户"建必优 token 有效，无需重新登录"，**结束流程**
- 若输出包含 `TOKEN_EXPIRED` 或 `TOKEN_NOT_FOUND`，继续 Step 2

### Step 2：启动本地回调服务并打开登录页

从 GitHub 拉取 login.py 并执行：

```bash
curl -fsSL https://raw.githubusercontent.com/aw3n1998/skills/main/jianyouyou-login/scripts/login.py | python3
```

脚本会自动：
1. 在本地 `127.0.0.1:19877` 启动临时 HTTP 回调服务
2. 尝试用系统浏览器打开 `http://192.168.2.99:8080/ai` 登录页
3. 等待用户完成账密登录（最长 3 分钟）

**重要：** 从脚本输出中提取 `LOGIN_URL:` 开头的那一行，得到完整登录链接。
**不要尝试自己访问该链接**——它是内网地址，只有用户本地浏览器才能打开。
无论浏览器是否自动弹出，都必须把登录链接直接发给用户，告知：
"请在你的浏览器中打开以下链接完成建必优登录：\n👉 {LOGIN_URL}"

### Step 3：等待回调并保存 Token

脚本执行完毕后根据输出判断：

- 若输出包含 `LOGIN_SUCCESS`：
  - 告知用户"✅ 建必优登录成功，Token 已保存"
  - 从输出中提取 `TOKEN_EXPIRES_AT` 告知有效期

- 若输出包含 `LOGIN_TIMEOUT`：
  - 告知用户"⏰ 登录超时（3分钟内未完成），请重试"

- 若输出包含 `LOGIN_FAILED`：
  - 从输出中提取错误原因告知用户

### Step 4：验证可用性（可选）

从 GitHub 拉取 verify_token.py 并执行：

```bash
curl -fsSL https://raw.githubusercontent.com/aw3n1998/skills/main/jianyouyou-login/scripts/verify_token.py | python3
```

- 若输出包含 `VERIFY_SUCCESS`，告知用户登录用户名和所属组织
- 若输出包含 `VERIFY_FAILED`，告知用户错误原因

## Token 存储位置

Token 保存在：`~/.openclaw/workspace/.jianyouyou_credentials.json`

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

- 脚本每次从 GitHub 实时拉取，GitHub 上更新脚本后立即生效，无需重装 Skill
- 回调端口 `19877`，若被占用脚本自动尝试 `19878`、`19879`
- Token 有效期 8 小时，过期后重新执行此 Skill 登录
- 网络需能访问 `github.com` 和 `192.168.2.17:8080`