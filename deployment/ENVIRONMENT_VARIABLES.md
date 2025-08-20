# Environment Variables Documentation

This document describes all environment variables used by the DOI Management Application.

## Quick Setup

1. Copy the template: `cp production.env.template .env`
2. Run setup script: `./deployment/scripts/setup-environment.sh`
3. Edit `.env` file with your specific values

## Required Variables (Production)

These variables **must** be set in production environment:

### Security
- `SECRET_KEY` - Flask secret key for sessions and CSRF protection
  - **Required in production**
  - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
  - Example: `SECRET_KEY=your-super-secret-key-here`

### Database
- `DATABASE_URL` - Complete database connection string
  - **Required in production** 
  - Format: `mysql+pymysql://username:password@host:port/database`
  - Example: `DATABASE_URL=mysql+pymysql://doi_user:secretpassword@localhost:3306/doi_db`

Alternative individual database settings:
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 3306)
- `DB_NAME` - Database name (default: doi_db)
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password

## Optional Variables

### Application Settings
- `FLASK_ENV` - Environment mode (development/production/testing)
- `FLASK_DEBUG` - Enable debug mode (True/False, default: False in production)
- `UPLOAD_FOLDER` - Path for file uploads (default: /opt/doi-app/uploads)
- `MAX_CONTENT_LENGTH` - Maximum file upload size in bytes (default: 10MB)
- `ALLOWED_EXTENSIONS` - Comma-separated list of allowed file extensions

### Session Configuration
- `PERMANENT_SESSION_LIFETIME` - Session timeout in seconds (default: 3600)
- `SESSION_COOKIE_SECURE` - Require HTTPS for session cookies (default: True in production)
- `SESSION_COOKIE_HTTPONLY` - HttpOnly flag for session cookies (default: True)
- `SESSION_COOKIE_SAMESITE` - SameSite policy (default: Lax)

### Caching
- `CACHE_TYPE` - Cache backend type (simple/redis/memcached, default: simple)
- `CACHE_DEFAULT_TIMEOUT` - Default cache timeout in seconds (default: 300)

### Rate Limiting
- `RATELIMIT_STORAGE_URL` - Rate limiting storage backend (default: memory://)
- `RATELIMIT_DEFAULT` - Default rate limits (default: 200/day;50/hour)

### Logging
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR, default: INFO)
- `LOG_FILE` - Log file path (default: logs/doi_app.log)
- `LOG_MAX_BYTES` - Maximum log file size in bytes (default: 10MB)
- `LOG_BACKUP_COUNT` - Number of log files to keep (default: 10)

### Database Performance
- `SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE` - Connection pool size (default: 10)
- `SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW` - Max overflow connections (default: 20)
- `SQLALCHEMY_ENGINE_OPTIONS_POOL_RECYCLE` - Connection recycle time in seconds (default: 3600)
- `SQLALCHEMY_ENGINE_OPTIONS_POOL_PRE_PING` - Enable connection pre-ping (default: True)

### Monitoring and Error Tracking
- `SENTRY_DSN` - Sentry DSN for error tracking
  - Optional but recommended for production
  - Format: `https://key@sentry.io/project-id`
- `SENTRY_ENVIRONMENT` - Environment name for Sentry (default: development)

### Health Checks
- `HEALTH_CHECK_DATABASE` - Include database check in health endpoint (default: True)
- `HEALTH_CHECK_TIMEOUT` - Health check timeout in seconds (default: 5)

### SSL/HTTPS
- `SSL_REDIRECT` - Redirect HTTP to HTTPS (default: True in production)
- `FORCE_HTTPS` - Force HTTPS in URLs (default: True in production)

### Application URLs
- `APPLICATION_URL` - Base application URL (used for redirects)
- `API_BASE_URL` - Base API URL (used for API documentation)

### Email Configuration (Future Use)
- `MAIL_SERVER` - SMTP server hostname
- `MAIL_PORT` - SMTP server port (default: 587)
- `MAIL_USE_TLS` - Use TLS encryption (True/False, default: True)
- `MAIL_USERNAME` - SMTP username
- `MAIL_PASSWORD` - SMTP password

### External APIs
- `CROSSREF_API_URL` - Crossref API base URL (default: https://api.crossref.org)
- `CROSSREF_DEPOSIT_URL` - Crossref deposit API URL

### Backup Settings
- `BACKUP_RETENTION_DAYS` - Days to keep backup files (default: 30)
- `DATABASE_BACKUP_PATH` - Path for database backups (default: backups)

## Environment-Specific Defaults

### Development Environment
```bash
FLASK_ENV=development
FLASK_DEBUG=True
SESSION_COOKIE_SECURE=False
SSL_REDIRECT=False
FORCE_HTTPS=False
LOG_LEVEL=DEBUG
```

### Production Environment
```bash
FLASK_ENV=production
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
SSL_REDIRECT=True
FORCE_HTTPS=True
LOG_LEVEL=INFO
```

### Testing Environment
```bash
FLASK_ENV=testing
TESTING=True
WTF_CSRF_ENABLED=False
DATABASE_URL=sqlite:///:memory:
```

## Security Best Practices

1. **Never commit .env files** to version control
2. **Use strong, unique values** for SECRET_KEY
3. **Restrict file permissions** on .env files: `chmod 600 .env`
4. **Use environment-specific values** (don't share between dev/prod)
5. **Regularly rotate secrets** in production
6. **Use SSL/HTTPS** in production (set SSL_REDIRECT=True)

## Validation

Use the validation script to check your configuration:

```bash
./deployment/scripts/setup-environment.sh validate
```

This will check:
- Required variables are set
- No placeholder values remain
- Database connectivity (optional)
- Configuration consistency

## Troubleshooting

### Common Issues

1. **SECRET_KEY not set error**
   - Solution: Generate and set SECRET_KEY in .env file

2. **Database connection fails**
   - Check DATABASE_URL format
   - Verify database exists and credentials are correct
   - Ensure MySQL server is running

3. **Permission denied on uploads**
   - Check UPLOAD_FOLDER permissions
   - Ensure directory exists and is writable

4. **Session cookies not secure**
   - Set SESSION_COOKIE_SECURE=True for HTTPS
   - Ensure SSL_REDIRECT=True in production

### Environment Variables Loading Order

1. System environment variables
2. `.env` file in project root
3. Default values in config.py

Later sources override earlier ones.

## Examples

### Minimal Production .env
```bash
SECRET_KEY=abc123-very-long-secret-key
DATABASE_URL=mysql+pymysql://doi_user:password123@localhost:3306/doi_prod
SENTRY_DSN=https://key@sentry.io/project
```

### Development .env
```bash
SECRET_KEY=dev-secret-key
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/doi_dev
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

### Testing .env
```bash
FLASK_ENV=testing
DATABASE_URL=sqlite:///:memory:
WTF_CSRF_ENABLED=False
```