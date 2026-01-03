# MySQL Migration Guide

## Current State
- Using SQLite/LibSQL via `@libsql/client`
- Experiencing 10-13 second login/signup times
- Better Auth slowness in Docker environment

## Proposed Solution
Migrate to MySQL 8.4 with Redis session caching.

## Performance Improvements

### 1. MySQL vs SQLite
- Better connection pooling
- More concurrent queries
- Better performance under load
- Production-ready for auth systems

### 2. Redis Session Caching
- Sessions cached in Redis for fast lookup
- Reduces database queries
- 10-50x faster session validation
- Automatic expiration management

### 3. HTTP/2 and Optimization
- Enable HTTP/2 in Docker
- Fix browser queuing issues
- Connection reuse
- Better resource loading

## Migration Steps

### 1. Update Dependencies
```bash
docker compose -f app/client/docker-compose.yml exec client bun install mysql2 ioredis @types/mysql2
```

### 2. Update Configuration
- Copy `app/client/mysql-schema.sql` to MySQL initialization
- Update `app/client/.env.local` with MySQL credentials
- Update `app/client/src/lib/auth.ts` to use `auth-mysql.ts`

### 3. Update Docker Compose
Already included in `app/client/docker-compose.yml`:
- MySQL 8.4 service
- Redis 7 service
- Health checks
- Volume persistence

### 4. Initialize Database
```bash
# Start infrastructure
docker compose -f app/client/docker-compose.yml up -d mysql redis

# Verify MySQL is running
docker compose -f app/client/docker-compose.yml logs mysql

# Tables will be auto-created by mysql-schema.sql on startup
```

### 5. Test Migration
```bash
# Restart client with new config
docker compose -f app/client/docker-compose.yml restart client

# Test signup/login
curl -X POST http://localhost:3000/api/auth/sign-up/email \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"password"}'

# Should be < 500ms with MySQL + Redis
```

## Environment Variables Required

```env
# MySQL
MYSQL_HOST=mysql
MYSQL_USER=root
MYSQL_PASSWORD=betterauth
MYSQL_DATABASE=bunny_auth

# Better Auth
BETTER_AUTH_SECRET=<generate with openssl rand -base64 32>
BETTER_AUTH_URL=http://localhost:3000

# Redis (optional but recommended)
REDIS_URL=redis://redis:6379
```

## Expected Performance

| Operation | Current (SQLite) | Target (MySQL + Redis) |
|-----------|------------------|------------------------|
| Database Init | 20-40ms | < 5ms |
| Signup | 10-13s | < 500ms |
| Login | 10-13s | < 200ms |
| Session Check | N/A | < 10ms (Redis) |

## Troubleshooting

### MySQL Connection Failed
```bash
# Check MySQL logs
docker compose -f app/client/docker-compose.yml logs mysql

# Verify connection
docker compose -f app/client/docker-compose.yml exec client mysql -h mysql -u root -pbetterauth bunny_auth
```

### Redis Connection Failed
```bash
# Check Redis logs
docker compose -f app/client/docker-compose.yml logs redis

# Test Redis
docker compose -f app/client/docker-compose.yml exec client redis-cli -h redis ping
```

### Still Slow After Migration
1. Check if Redis is being used (look for Redis logs)
2. Verify connection pool size in `auth-mysql.ts`
3. Check MySQL query performance
4. Ensure HTTP/2 is enabled in Docker

## Rollback Plan

If issues occur, revert changes:
1. Restore `app/client/src/lib/auth.ts` from git
2. Remove MySQL/Redis services from docker-compose.yml
3. Restart client container
4. Database will fall back to SQLite
