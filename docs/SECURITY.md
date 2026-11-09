# Security Guide - DAAV Backend

## 🚨 Identified and Fixed Vulnerabilities

### 1. Path Traversal / Directory Traversal
**Problem:** The system allowed access to files outside authorized directories via sequences like `../../../etc/passwd`.

**Implemented solutions:**
- ✅ Module `app/utils/security.py` with strict path validation
- ✅ Class `PathSecurityValidator` to sanitize and validate all paths
- ✅ Verification that files remain within authorized directories
- ✅ Blocking of dangerous patterns (`../`, `~/`, `/etc/`, etc.)

### 2. File Injection
**Problem:** File upload without validation allowing malicious file writing.

**Implemented solutions:**
- ✅ Validation of allowed file extensions
- ✅ Filename sanitization (removal of dangerous characters)
- ✅ File size limitation (`MAX_FILE_SIZE`, 100MB per file by default)
- ✅ Validation of destination directories

### 3. Unrestricted Directory Access
**Problem:** Recursive reading of all files without restriction.

**Implemented solutions:**
- ✅ Whitelist of authorized directories
- ✅ Exclusion of system and hidden files

## 🛡️ Implemented Security Measures

### Path Validation (`PathSecurityValidator`)
```python
# Usage
validated_path = PathSecurityValidator.validate_file_path(user_input)
safe_filename = PathSecurityValidator.validate_filename(filename)
```

**Features:**
- Detection of dangerous patterns
- Path normalization
- Extension validation
- Base directory control

### Access Control (`FileAccessController`)
```python
# Access verification
can_access = FileAccessController.can_read_file(file_path, allowed_dirs)
content = FileAccessController.get_restricted_file_content(file_path, max_size)
```

**Features:**
- Verification of authorized directories
- File size limitation
- Permission management

### Security Middleware (`SecurityMiddleware`)

**Integration in main.py:**
```python
if settings.security_enabled:
    app.add_middleware(
        SecurityMiddleware,
        rate_limit=settings.security_rate_limit,
        time_window=settings.security_time_window
    )
```
The middleware can be disabled with `SECURITY_ENABLED=false`.

**Configuration for Users:**
The rate limiting and time window for security are set using environment variables. You can adjust these values in your deployment settings to control how many requests are allowed and over what period.

```bash
# Maximum requests allowed per time window
SECURITY_RATE_LIMIT=100

# Time window in seconds
SECURITY_TIME_WINDOW=60
```

These variables should be set in your environment or `.env` file before starting the backend. The application will automatically use these values to configure the security middleware.

**Features:**
- ✅ Rate limiting (configurable req/min per IP)
- ✅ Path traversal detection (`../`, `/etc/`, etc.)
- ✅ Suspicious pattern detection (encoded attacks)
- ✅ Large request size blocking (> 10 × `MAX_FILE_SIZE`, i.e. 1000MB by default → HTTP 413)
- ✅ Temporary IP blocking (1 hour after exceeding the rate limit)
- ✅ File access monitoring and logging
- ✅ Automatic security event logging

**What it blocks:**
- Path traversal: `../../../etc/passwd` (→ HTTP 400)
- Rate limits: more than `SECURITY_RATE_LIMIT` requests per `SECURITY_TIME_WINDOW` from the same IP (100/60s by default → HTTP 429, then IP blocked for 1 hour)
- Suspicious headers: Headers containing attack patterns
- System paths: `/etc/`, `/proc/`, `C:\Windows\`

Patterns are regular expressions defined in `SecurityConfig.SUSPICIOUS_REQUEST_PATTERNS` (`app/config/security.py`) and checked on the URL path and query (raw and URL-decoded) and on header values.

**Client IP**: `X-Real-IP` / `X-Forwarded-For` are only trusted when the request comes from a loopback or private address (e.g. the Nginx container); otherwise the socket address is used, so these headers cannot be spoofed to bypass rate limiting.

> The rate-limit and blocked-IP state is kept in memory, per worker process.

## 🔑 Authentication & Authorization

- **JWT** access tokens (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, 60 min by default) and refresh tokens (`JWT_REFRESH_TOKEN_EXPIRE_DAYS`, 90 days by default), signed with `JWT_SECRET_KEY` (min. 32 characters, no default value — see [Application secrets](#application-secrets))
- **Password change**: only through `POST /auth/change-password`, which requires the current password (`PUT /auth/me` refuses the `password` field), so that a stolen token alone cannot be used to take over an account. Admins can still set the password of another user with `PUT /auth/users/{id}`
- **Token revocation**: changing the password (`POST /auth/change-password`, password reset, or update by an admin through `PUT /auth/users/{id}`) revokes all the tokens issued before, so other sessions are logged out. `POST /auth/change-password` returns new tokens for the current session
- **Password hashing** with Argon2id (`passlib`)
- **Password policy**: at least 8 characters, one uppercase, one lowercase and one special character
- **Roles**: `admin` and `user`; datasets and workflows are owned by a user and can be shared
- **Registration**: only admins can create users unless `ALLOW_PUBLIC_REGISTRATION=true`; only admins can create admin users
- **Password reset** by email (SMTP settings, token valid `PASSWORD_RESET_TOKEN_EXPIRE_HOURS`)
- **Default admin**: `admin` / `Admin123!` is created when no user exists. A password change is required at first login (`must_change_password` flag): until then, every endpoint except `GET /auth/me` and `POST /auth/change-password` returns `403 Password change required`. Any account logging in with this default password gets the same requirement
- **PDC (M2M) requests** (`/ptx/executeChainService`, `/ptx/pdcInput`, `/api/...`, `/output/...`): authenticated by matching request headers against the credentials configured by each user (constant-time comparison, deactivated accounts are ignored). Service chain data received this way is stored for each authenticated user and can only be read or deleted by that user

## 💉 Injection & SSRF Protection

Dataset models validate user-provided connection parameters (`app/models/interface/dataset_interface.py`):
- **MySQL**: `database` and `table` must be plain SQL identifiers (`[A-Za-z0-9_]`, max 64 chars)
- **Elasticsearch**: `index` must be a valid index name; wildcard expressions are rejected
- **API output filters**: Drupal JSON:API filters on `/api/...` and `/output/...` are converted to parameterized DuckDB queries; values are bound as parameters, field paths are quoted as SQL identifiers and group conjunctions are restricted to `AND` / `OR` (`app/utils/drupal_filter_converter.py`). Once the output file is loaded, file and network access is disabled on the DuckDB connection, so that a filter can never read other files
- **SSRF**: API and Elasticsearch URLs must use `http`/`https` and must not target `localhost` or private/internal addresses (private, loopback, link-local, reserved ranges, including IPv4-mapped IPv6 addresses) (`app/utils/ssrf.py`). The URL is checked when the dataset is saved, and for Elasticsearch the hostname is also resolved right before each connection: a hostname that resolves to an internal address is refused
- **ALLOWED_PRIVATE_HOSTS**: comma-separated hostnames or IPs allowed to point to internal addresses anyway, for data sources on the same network (e.g. the `elasticsearch` service of the Docker Compose `elastic` profile). Keep it empty unless needed

## 📁 Authorized Directories

### Whitelist
- `UPLOAD_DIR` (default `uploads/`, resolved from `app/`) - Files uploaded by users
- `app/ptx/` - PTX data
- `app/inputs/` - Input files
- Any directory listed in `DIRECTORY_WHITE_LIST`

### Forbidden Directories
- `/etc/`, `/proc/`, `/sys/` (Unix)
- `C:\Windows\`, `C:\Users\` (Windows)  
- Any system or user directory

## 📄 Allowed File Extensions

### Data Formats
- `.csv`, `.tsv` - Tabular data files
- `.json` - JSON data
- `.xlsx`, `.xls` - Excel files
- `.parquet` - Parquet format
- `.avro` - Avro format
- `.feather`, `.orc` - Other data formats

### Text Formats
- `.txt` - Text files
- `.md` - Markdown
- `.yml`, `.yaml` - YAML configuration
- `.xml` - XML data
- `.log` - Log files

### Media Formats
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.svg`
- Audio: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma`
- Video: `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`

The list is defined in `SecurityConfig.ALLOWED_FILE_EXTENSIONS` (`app/config/security.py`).

<a id="application-secrets"></a>
## 🗝️ Application Secrets

`JWT_SECRET_KEY` (signs the authentication tokens) and `FIELD_ENCRYPTION_KEY` (encrypts the dataset credentials) have **no default value**. They are read from the environment or from `backendApi/.env`.

If one of them is not set, the backend does not stop:
1. On first start, a temporary key is generated and stored in `SECRETS_DIR` (`backendApi/secrets/` locally, the `backend-secrets` volume at `/app/secrets` in Docker) as `JWT_SECRET_KEY_TMP` / `FIELD_ENCRYPTION_KEY_TMP` (file readable by the owner only). It is reused on every restart and shared by all workers.
2. An **error** is logged at every start until the key is configured.

To configure the keys, copy the generated values to the real variables and **save them in a secrets vault** (password manager, HashiCorp Vault...):

```bash
# Docker
docker compose exec backend cat /app/secrets/JWT_SECRET_KEY_TMP /app/secrets/FIELD_ENCRYPTION_KEY_TMP
# Local install
cat backendApi/secrets/JWT_SECRET_KEY_TMP backendApi/secrets/FIELD_ENCRYPTION_KEY_TMP
```

Then set `JWT_SECRET_KEY=...` and `FIELD_ENCRYPTION_KEY=...` in `backendApi/.env` or in `docker-compose.yml` and restart the backend. You can also generate your own values:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"                                  # JWT_SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"     # FIELD_ENCRYPTION_KEY
```

| Key | If it is lost or changed |
|---|---|
| `JWT_SECRET_KEY` | Users have to log in again |
| `FIELD_ENCRYPTION_KEY` | Dataset credentials can no longer be decrypted and must be re-entered (unless the previous key is still available as `FIELD_ENCRYPTION_KEY_TMP`, see below) |

The placeholder JWT secrets shipped by previous versions of `docker-compose.yml`, `.env.example` and the settings are public: they are refused and treated as not set.

> ⚠️ `docker compose down -v` deletes the `backend-secrets` volume. Configure the keys before relying on the generated ones.

## 🔐 Encryption of Sensitive Dataset Fields

Dataset credentials (MySQL passwords, API tokens, PTX tokens, etc.) are encrypted at rest in MongoDB using **Fernet** (AES-128-CBC + HMAC-SHA256) with `FIELD_ENCRYPTION_KEY` (or its temporary value, see above).

### Encrypted fields per dataset type

| Dataset type | Encrypted fields |
|---|---|
| MySQL | `password` |
| MongoDB | `uri` (contains credentials) |
| Elasticsearch | `password`, `key`, `bearerToken` |
| PTX/PDC | `token`, `refreshToken`, `secret_key`, `service_key` |
| API | `bearerToken`, `basicToken`, `clientSecret` |

### Migration and key change

The `enc:` prefix distinguishes encrypted values from plain ones. At every start, the backend re-encrypts the stored credentials with the current `FIELD_ENCRYPTION_KEY`:
- plain-text values (stored by previous versions) are encrypted;
- values encrypted with a previous key are decrypted and re-encrypted. Previous keys accepted for decryption: the key derived (HKDF-SHA256) from `JWT_SECRET_KEY` or from the former public placeholder JWT secrets (used by previous versions when `FIELD_ENCRYPTION_KEY` was not set), and `FIELD_ENCRYPTION_KEY_TMP` when a different `FIELD_ENCRYPTION_KEY` has been configured.

Values that cannot be decrypted with any known key are left unchanged and reported as errors in the logs: the credentials of these datasets must be re-entered.

---

## 🔧 Configuration

### Environment Variables
```bash
# Secrets (no default value: temporary keys are generated in SECRETS_DIR if empty)
JWT_SECRET_KEY=
FIELD_ENCRYPTION_KEY=
# SECRETS_DIR=secrets

# Security middleware
SECURITY_ENABLED=true
SECURITY_RATE_LIMIT=100
SECURITY_TIME_WINDOW=60

# Security log
SECURITY_LOG_FILE=security.log
SECURITY_LOG_LEVEL=INFO

# Upload directory (optional, default: uploads)
UPLOAD_DIR=uploads

# Max file size (optional, default: 100MB)
MAX_FILE_SIZE=100MB

# WhiteList directory who can bypass path restriction security
# Example by default /opt is not readeable to avoid unauthorized access to 3rd app conf
# You can add a sub directory on this list to avoid this exclusion to give access to subpath
DIRECTORY_WHITE_LIST=/opt/uploads,/opt/static
```
## 🔍 Monitoring and Logs

### Security Logs
Security events are logged by the `security` logger in `SECURITY_LOG_FILE` (default `security.log`, in the log directory, rotated with `SECURITY_LOG_MAX_SIZE` / `SECURITY_LOG_BACKUP_COUNT`):

```
[SECURITY] 2026-01-01 12:00:00,000 - ERROR - SUSPICIOUS_PATTERN_DETECTED: Suspicious pattern in request from 192.168.1.100: /datasets/../../etc/passwd
[SECURITY] 2026-01-01 12:01:00,000 - WARNING - RATE_LIMIT_EXCEEDED: ...
[SECURITY] 2026-01-01 12:02:00,000 - WARNING - BLOCKED_IP_ACCESS: ...
```

### Monitored Event Types
- `SUSPICIOUS_PATTERN_DETECTED` - Suspicious pattern (path traversal, encoded attack...) in URL, query or headers
- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded (IP is then blocked)
- `BLOCKED_IP_ACCESS` - Request from a temporarily blocked IP
- `LARGE_REQUEST_DETECTED` - Request body larger than allowed
- `FILE_ACCESS` - File access
- `SUSPICIOUS_FILE_ACCESS_PATTERN` - Abnormal file access pattern from one IP
- `REQUEST_ERROR` - Unhandled error while processing a request

## 🧪 Security Tests

### Running Tests
```bash
cd backendApi
python -m pytest tests/security -v
```

Test files: `test_path_security.py`, `test_security_middleware.py`, `test_injection_validators.py`, `test_secret_keys.py`, `test_m2m_auth.py` (plus `tests/models/interface/test_dataset_interface.py` and `tests/services/test_reencryption_service.py` for field encryption and `tests/utils/test_drupal_filter_converter.py` for API output filters).

### Tested Scenarios
- ✅ Unix/Windows path traversal
- ✅ Null byte injection
- ✅ Windows reserved filenames
- ✅ Unauthorized extensions
- ✅ Excessive file sizes
- ✅ Access outside authorized directories
- ✅ Rate limiting, IP blocking and suspicious pattern detection (middleware)
- ✅ SQL identifier injection, Elasticsearch wildcards and SSRF URLs
- ✅ SQL injection through API output filter paths and group conjunctions, file access from DuckDB filter queries
- ✅ Revocation of the tokens issued before a password change
- ✅ Refusal of password changes without the current password (`PUT /auth/me`)
- ✅ M2M authentication (wrong credentials, deactivated accounts) and per-user isolation of service chain data
- ✅ Proxy header spoofing and false positives of the middleware patterns
- ✅ Encryption of sensitive dataset fields at rest
- ✅ Temporary secret generation, refusal of public placeholder secrets, re-encryption with the current key

## 🚀 Deployment Recommendations

### In Production
1. **Environment variables**: Configure all tokens/secrets
2. **HTTPS**: Use HTTPS exclusively
3. **Reverse Proxy**: Nginx/Apache with additional limitations
4. **Monitoring**: Monitor security logs
5. **Backup**: Regularly backup authorized data only

### Nginx Configuration (example)
```nginx
# Limit upload size
client_max_body_size 100M;

# Security headers
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";

# Block access to sensitive files
location ~ /\. {
    deny all;
}

location ~ \.(env|ini|conf)$ {
    deny all;
}
```
