# 建必优登录 Skill 配置说明

## 当前配置（已生效）

| 项目 | 值 |
|---|---|
| 建必优服务器 | `http://192.168.2.17:8080` |
| 登录页地址 | `http://192.168.2.17:8080/ai` |
| 本地回调地址 | `http://127.0.0.1:19877/callback` |
| Token 保存位置 | `~/.openclaw/workspace/.jianyouyou_credentials.json` |

无需配置任何环境变量，地址已直接写入脚本。

---

## 关键问题：建必优前端需要配合改造

这个 Skill 的工作原理是：

```
QClaw 打开登录页
    → 用户在浏览器里输入账号密码
    → 建必优前端登录成功
    → 前端把 token 发到 http://127.0.0.1:19877/callback
    → Skill 收到 token，保存到本地
```

**建必优前端（Vue.js）需要在登录成功后加一段代码：**

在你的登录成功回调里（通常是 `login.vue` 或 `auth.js` 里处理 `/api/auth/login` 响应的地方），添加：

```javascript
// 登录成功后，检查 URL 是否带有 redirect_uri 参数
const params = new URLSearchParams(window.location.search)
const redirectUri = params.get('redirect_uri')

if (redirectUri && redirectUri.startsWith('http://127.0.0.1:')) {
  // 把 token 发回给 QClaw 的本地回调服务
  const token = response.data.token  // 你的实际 token 字段名
  window.location.href = `${redirectUri}?token=${token}&token_type=Bearer&expires_in=28800`
}
```

> 如果你的登录接口返回的字段名不叫 `token`，改成实际字段名即可，比如 `access_token`、`Authorization` 等。

---

## 建必优后端登录接口参考

通常建必优 Spring Boot 的登录接口是：

```
POST http://192.168.2.17:8080/api/auth/login
Body: { "username": "xxx", "password": "xxx" }
Response: { "code": 200, "data": { "token": "eyJ...", "expireTime": 28800 } }
```

确认实际字段名后，对应修改前端代码里的 `response.data.token` 即可。

---

## 验证接口

`verify_token.py` 会调用：

```
GET http://192.168.2.17:8080/api/user/current
Header: Authorization: Bearer {token}
```

如果建必优的获取当前用户接口路径不是 `/api/user/current`，
请修改 `scripts/verify_token.py` 第 17 行的 `VERIFY_ENDPOINT`。

---

## 安装命令

```bash
# Windows（PowerShell）
xcopy /E /I jianyouyou-login "%USERPROFILE%\.openclaw\workspace\skills\jianyouyou-login"

# 或者直接解压 zip 到：
# C:\Users\你的用户名\.openclaw\workspace\skills\jianyouyou-login\
```
