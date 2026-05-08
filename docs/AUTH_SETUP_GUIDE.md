# Hướng dẫn Authentication & Setup Admin

## Tổng quan

DeerFlow sử dụng hệ thống xác thực dựa trên **JWT cookie** với bảo vệ **CSRF Double Submit Cookie**. Hệ thống phân biệt 2 flow đăng ký khác nhau cho admin và user thường.

---

## 1. Setup Admin (Lần đầu khởi động)

### Khi nào hiện trang Setup?

Trang `/setup` tự động hiện khi **chưa có admin nào** trong database.

**Flow tự động:**

```
Browser → /login hoặc /workspace
  → Frontend gọi GET /api/v1/auth/setup-status
  → Backend kiểm tra count_admin_users() == 0
  → Trả về { needs_setup: true }
  → Redirect sang /setup
```

### Cách kích hoạt lại trang Setup Admin

Xóa database để reset trạng thái "first boot":

```bash
rm -rf backend/.deer-flow/data
make stop && make dev
```

Truy cập `http://localhost:2026` → tự động redirect sang `/setup`.

### API liên quan

| Endpoint | Method | Mô tả |
|----------|--------|--------|
| `/api/v1/auth/setup-status` | GET | Kiểm tra hệ thống đã có admin chưa |
| `/api/v1/auth/initialize` | POST | Tạo admin đầu tiên (chỉ gọi được khi chưa có admin) |

**Request body cho `/api/v1/auth/initialize`:**

```json
{
  "email": "admin@example.com",
  "password": "your-strong-password"
}
```

- Password tối thiểu 8 ký tự
- Không được dùng mật khẩu phổ biến (password123, admin123, ...)
- Tài khoản được tạo với `system_role: "admin"`, `needs_setup: false`
- Session cookie tự động được set sau khi tạo thành công

### Files liên quan

| File | Vai trò |
|------|---------|
| `frontend/src/app/(auth)/setup/page.tsx` | Giao diện trang Setup |
| `backend/app/gateway/routers/auth.py` → `initialize_admin()` | API tạo admin |
| `backend/app/gateway/app.py` → `_ensure_admin_user()` | Startup hook kiểm tra admin |

---

## 2. Đăng ký User Thường

### Cách truy cập

Truy cập `/login` → Click **"Don't have an account? Sign up"** → Nhập email + password → **Create Account**.

### API liên quan

| Endpoint | Method | Mô tả |
|----------|--------|--------|
| `/api/v1/auth/register` | POST | Đăng ký user mới (luôn là `system_role: "user"`) |
| `/api/v1/auth/login/local` | POST | Đăng nhập bằng email/password |

### Files liên quan

| File | Vai trò |
|------|---------|
| `frontend/src/app/(auth)/login/page.tsx` | Giao diện Login/Register |
| `backend/app/gateway/routers/auth.py` → `register()` | API đăng ký user |

---

## 3. Flow tổng quan

```
┌─────────────────────────────────────────────────────┐
│                    First Boot                        │
│  (chưa có admin trong DB)                           │
│                                                     │
│  Browser → /login → check setup-status              │
│         → needs_setup: true                         │
│         → redirect /setup                           │
│         → POST /api/v1/auth/initialize              │
│         → Admin created → redirect /workspace       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                 Normal Operation                     │
│  (đã có admin trong DB)                             │
│                                                     │
│  Browser → /login → check setup-status              │
│         → needs_setup: false                        │
│         → Hiện form Login / Register                │
│         ┌──────────────────────────────────────┐    │
│         │ Login:    POST /api/v1/auth/login     │    │
│         │ Register: POST /api/v1/auth/register  │    │
│         └──────────────────────────────────────┘    │
│         → Session cookie set → redirect /workspace  │
└─────────────────────────────────────────────────────┘
```

---

## 4. CSRF Protection

### Cơ chế Double Submit Cookie

- Auth endpoints (`/login`, `/register`, `/initialize`) **KHÔNG cần** CSRF token (vì user chưa có token lần đầu)
- Tuy nhiên, chúng **BẮT BUỘC** kiểm tra **Origin header** để chống Cross-site request
- Các endpoint khác (POST/PUT/DELETE/PATCH) yêu cầu **CSRF token** trong cả cookie và header `X-CSRF-Token`

### Lỗi thường gặp: "Cross-site auth request denied"

**Nguyên nhân**: nginx.local.conf sử dụng `$host` thay vì `$http_host`, khiến port bị mất khỏi Host header.

**Ví dụ:**
- Browser gửi `Origin: http://localhost:2026`
- nginx forward với `Host: localhost` (mất `:2026`)
- Gateway tính `request_origin = http://localhost`
- So sánh: `http://localhost:2026 ≠ http://localhost` → **Bị reject**

**Fix**: Trong `docker/nginx/nginx.local.conf`, đảm bảo tất cả location blocks sử dụng:

```nginx
# ✅ Đúng — giữ port
proxy_set_header Host $http_host;

# ❌ Sai — mất port
# proxy_set_header Host $host;
```

### Files CSRF liên quan

| File | Vai trò |
|------|---------|
| `backend/app/gateway/csrf_middleware.py` | CSRF middleware chính |
| `docker/nginx/nginx.local.conf` | Nginx config cho dev mode |
| `docker/nginx/nginx.conf` | Nginx config cho Docker production |

---

## 5. Các endpoint Auth đầy đủ

| Endpoint | Method | Auth Required | Mô tả |
|----------|--------|--------------|--------|
| `/api/v1/auth/setup-status` | GET | ❌ | Kiểm tra cần setup không |
| `/api/v1/auth/initialize` | POST | ❌ | Tạo admin đầu tiên |
| `/api/v1/auth/register` | POST | ❌ | Đăng ký user thường |
| `/api/v1/auth/login/local` | POST | ❌ | Đăng nhập |
| `/api/v1/auth/logout` | POST | ❌ | Đăng xuất |
| `/api/v1/auth/me` | GET | ✅ | Lấy thông tin user hiện tại |
| `/api/v1/auth/change-password` | POST | ✅ | Đổi mật khẩu |

---

## 6. Cấu trúc thư mục Auth

```
backend/app/gateway/
├── auth/                    # Auth core module
│   ├── config.py           # Auth configuration
│   ├── errors.py           # Error codes & responses
│   ├── jwt.py              # JWT encode/decode
│   └── password.py         # Password hashing (argon2)
├── auth_middleware.py       # Auth middleware (fail-closed)
├── csrf_middleware.py       # CSRF protection
├── langgraph_auth.py        # LangGraph auth handler
└── routers/
    └── auth.py             # Auth API endpoints

frontend/src/
├── core/auth/
│   ├── AuthProvider.tsx    # React auth context
│   ├── server.ts           # SSR auth check
│   ├── proxy-policy.ts     # Proxy header policy
│   └── types.ts            # Auth types
└── app/(auth)/
    ├── login/page.tsx      # Login/Register page
    └── setup/page.tsx      # Admin setup page
```
