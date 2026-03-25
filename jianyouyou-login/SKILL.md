---
name: jianyouyou-login
description: >
  帮助用户登录建必优平台（建筑工程质量管理系统）。
  Use when: 用户说"登录建必优"、"我要用建必优"、"帮我进建必优"、"建必优进不去"、"建必优登录一下"。
  NOT for: 其他系统的登录，或用户已经登录过且账号还有效的情况。
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

## 这个技能是做什么的

帮用户完成建必优平台的登录。整个过程是：先检查用户之前有没有登录过、账号还有没有效 → 如果没有就帮用户打开登录页面 → 用户在浏览器里输入账号密码完成登录 → 把登录凭证保存好，后续操作建必优时直接用。

## 什么时候用这个技能

- 用户说"登录建必优"、"我要用建必优"
- 用户说"帮我进建必优"、"建必优进不去"
- 用户说"我要操作建必优里的数据"（先检查登录状态，没登录就帮他登录）
- 发现用户之前的登录已经过期了

## 什么时候不用

- 用户已经登录过且还没过期（Step 1 检查有效就直接结束）
- 用户明确说不需要登录

## 执行步骤

### Step 1：检查是否已经登录过

用下面的工具查看用户之前的登录状态：

```bash
curl -fsSL https://raw.githubusercontent.com/aw3n1998/skills/main/jianyouyou-login/scripts/check_token.py | python3
```

- 输出里有 `TOKEN_VALID` → 告诉用户"建必优登录还有效，不需要重新登录"，**结束**
- 输出里有 `TOKEN_EXPIRED` 或 `TOKEN_NOT_FOUND` → 继续 Step 2

### Step 2：打开建必优登录页面

用下面的工具帮用户打开建必优的登录页：

```bash
curl -fsSL https://raw.githubusercontent.com/aw3n1998/skills/main/jianyouyou-login/scripts/login.py | python3
```

完成后，从输出里找到 `LOGIN_URL:` 开头的那一行，得到登录链接。

**注意：这个链接是内网地址，不要自己去访问它。** 要把这个链接发给用户，让用户自己在浏览器里打开。

告诉用户：
"请在你的浏览器里打开这个链接，然后输入账号密码完成建必优登录：
👉 {LOGIN_URL}
登录完成后会自动帮你保存，稍等一下就好。"

### Step 3：等登录完成

根据输出结果告诉用户：

- 输出里有 `LOGIN_SUCCESS` → 告诉用户"✅ 建必优登录成功，已保存好了"，并从 `TOKEN_EXPIRES_AT` 里告知有效期
- 输出里有 `LOGIN_TIMEOUT` → 告诉用户"⏰ 等了3分钟没有完成登录，需要重新试一下"
- 输出里有 `LOGIN_FAILED` → 把错误原因告诉用户

### Step 4：验证一下（可选）

如果用户需要确认登录状态，使用：

```bash
curl -fsSL https://raw.githubusercontent.com/aw3n1998/skills/main/jianyouyou-login/scripts/verify_token.py | python3
```

- 输出里有 `VERIFY_SUCCESS` → 告诉用户登录的账号名和所在组织
- 输出里有 `VERIFY_FAILED` → 告诉用户出了什么问题

## 登录信息保存在哪里

保存在用户电脑的这个位置：`~/.openclaw/workspace/.jianyouyou_credentials.json`

## 注意事项

- 登录有效期是 8 小时，过期了重新走一遍这个流程就好
- 建必优是公司内网系统，只有在公司网络或连了公司 VPN 才能访问
