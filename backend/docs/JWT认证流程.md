## JWT 认证实现完成

### 新增文件

1. backend/utils/auth.py - JWT 工具模块
- create_access_token(username) - 生成 JWT token（24小时有效期）
- verify_token(token) - 验证 JWT token，返回用户名
- extract_token_from_header(authorization) - 从 Header 中提取 token
- 使用 datetime.now(timezone.utc) 替代已弃用的 utcnow()

### 修改文件

2. backend/routers/auth.py
- /api/login 现在返回 {"status": "success", "token": "<jwt_token>"}
- 符合设计文档要求

3. backend/routers/unlock.py
- /api/unlock 现在验证 JWT token 而不是用户名密码
- 从 Header 中读取 Authorization: Bearer <token>
- 符合设计文档要求："Header: 需携带 Token (Authorization: Bearer ...)"

---
### 使用方式

前端调用流程：

1. 登录获取 token:
POST /api/login
Body: { username: "admin", password: "123456" }
Response: { status: "success", token: "eyJ0eXAiOiJKV1QiLCJhbGci..." }

2. 使用 token 开门:
POST /api/unlock
Headers: { Authorization: "Bearer eyJ0eXAiOiJKV1QiLCJhbGci..." }
Response: { status: "success", message: "Door unlock initiated" }

---
注意事项

- Token 有效期：24小时
- SECRET_KEY 目前是硬编码的，生产环境应该从环境变量读取
- 只有 /api/unlock 需要 token 认证，其他端点不需要

