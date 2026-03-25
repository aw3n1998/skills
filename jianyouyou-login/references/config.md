# 建必优登录 Skill 配置说明

## 必填配置（首次使用前必须修改）

在系统环境变量或 `openclaw.json` 中配置以下变量：

| 变量名 | 说明 | 示例 |
|---|---|---|
| `JYY_BASE_URL` | 建必优服务器地址 | `https://jyy.yourcompany.com` |
| `JYY_CLIENT_ID` | OAuth 客户端 ID | `qclaw-agent` |

### 在 openclaw.json 中配置（推荐）

```json
{
  "skills": {
    "entries": {
      "jianyouyou-login": {
        "enabled": true,
        "env": {
          "JYY_BASE_URL": "https://jyy.yourcompany.com",
          "JYY_CLIENT_ID": "qclaw-agent"
        }
      }
    }
  }
}
```

---

## 建必优后端需要配置的内容

你的建必优 Spring Boot 后端需要：

### 1. 注册 OAuth 客户端

在建必优后台（或数据库 `oauth_client` 表）添加：

```sql
INSERT INTO oauth_client (client_id, redirect_uri, scope)
VALUES ('qclaw-agent', 'http://127.0.0.1:19877/callback', 'openid');
```

> `redirect_uri` 必须允许 `127.0.0.1:19877` 到 `127.0.0.1:19881` 的端口范围（Skill 会自动选择可用端口）

### 2. 授权回调返回格式

建必优登录成功后，重定向到：

```
http://127.0.0.1:19877/callback?token={JWT}&token_type=Bearer&expires_in=28800
```

或者 POST JSON 到回调地址：

```json
{
  "token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 28800,
  "user_info": {
    "username": "zhangsan",
    "realName": "张三",
    "orgName": "某建筑公司"
  }
}
```

### 3. 验证接口

Skill 使用 `GET /api/user/current` 验证 token，需返回：

```json
{
  "code": 200,
  "data": {
    "username": "zhangsan",
    "realName": "张三",
    "orgName": "某建筑公司"
  }
}
```

---

## Token 文件位置

`~/.openclaw/workspace/.jianyouyou_credentials.json`

其他建必优 Skill 读取 token 的方式：

```python
import json
from pathlib import Path

creds_file = Path.home() / ".openclaw" / "workspace" / ".jianyouyou_credentials.json"
creds = json.loads(creds_file.read_text())
token = creds["token"]
headers = {"Authorization": f"Bearer {token}"}
```
