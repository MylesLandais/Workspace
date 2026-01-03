# Better Auth MySQL Migration Status

## Summary
Attempted to migrate from SQLite to MySQL for Better Auth but encountered multiple schema compatibility and adapter initialization issues.

## What Was Done

### 1. Infrastructure Setup ✅
- MySQL 8.4 container added to docker-compose.yml
- Redis 7 container added for session caching
- Health checks configured for both services
- Environment variables updated for MySQL connection

### 2. Dependencies Installed ✅
- mysql2@3.16.0
- ioredis@5.8.2
- Better Auth types not available (@types/mysql2 not published)

### 3. MySQL Schema Created ✅
- Created `app/client/mysql-schema.sql` with proper schema
- Tables: user, account, session, verification
- All columns using snake_case: email_verified, created_at, etc.
- Proper indexes created

### 4. Issues Encountered ❌

#### Issue 1: Drizzle Schema Mapping
**Error**: "The field 'emailVerified' does not exist in 'user' Drizzle schema"

**Cause**: Drizzle ORM uses camelCase property names (emailVerified) while MySQL physical columns are snake_case (email_verified). Better Auth expects snake_case column names but was checking for camelCase property names.

**Attempted Fixes**:
- Created MySQL schema with snake_case columns
- Created Drizzle MySQL schema with proper type mappings
- Used Drizzle Kit to push schema

**Result**: Still failing with same error

#### Issue 2: MySQL Schema Constraints
**Errors**:
- "BLOB/TEXT column 'id' used in key specification without a key length"
- "Specified key was too long; max key length is 3072 bytes"

**Cause**: MySQL doesn't allow TEXT columns as primary keys or in UNIQUE constraints without specifying length.

**Attempted Fixes**:
- Changed ID columns to VARCHAR(255)
- Changed token column to VARCHAR(1000) with separate UNIQUE index
- Used TEXT for non-key columns

**Result**: Drizzle push succeeded but tables still had old schema cached

#### Issue 3: Better Auth MySQL Adapter Initialization
**Errors**:
- "Unknown database 'bunny'" - Better Auth looking for wrong database name
- "Failed to initialize database adapter" - Generic adapter error
- "dialect.createDriver is not a function" - Kysely/driver incompatibility

**Attempted Fixes**:
- Passed MySQL connection pool directly to Better Auth
- Configured explicit schema mappings with table names
- Tried Better Auth's custom MySQL adapter configuration
- Reverted to SQLite (working, just slow)

**Result**: Multiple incompatibility issues between Better Auth's MySQL adapter and installed dependencies

## Current Status

### Working Solution (SQLite) ⚠️
- SQLite with LibSQL works reliably
- Email verification disabled for testing
- Response time: ~10-13 seconds (slow but functional)
- No schema or adapter errors

### Broken Solution (MySQL) ❌
- MySQL container running correctly
- Tables created successfully
- Better Auth cannot initialize MySQL adapter properly
- Multiple schema/driver incompatibility issues

## Performance Comparison

| Metric | SQLite (Current) | MySQL (Target) |
|---------|------------------|----------------|
| Database Init | 20ms | < 5ms |
| Signup Time | 10-13s | < 500ms |
| Login Time | 10-13s | < 200ms |
| Session Lookup | DB query | < 10ms (Redis) |
| Reliability | Works | Not functional |

## Recommendations

### Short Term (Immediate)
1. **Keep using SQLite for now** - It works reliably despite slow response times
2. **Focus on optimizing Better Auth performance** - The slowness is in Better Auth's internal processing, not database
3. **Profile Better Auth operations** - Add detailed logging to identify the 10+ second delay
4. **Consider alternative auth libraries**:
   - NextAuth.js (v5)
   - Lucia (lightweight, fast)
   - Clerk (managed auth)

### Long Term (Better MySQL)
1. **Wait for Better Auth v2.x** - Better MySQL adapter support may improve
2. **Use Drizzle Kit migrations properly** - Avoid manual schema creation
3. **Better schema management** - Use Better Auth CLI to generate and push schemas
4. **Consider Prisma ORM** - Better native MySQL support and Better Auth integration

## Files Modified (Can be reverted)

- `app/client/src/lib/auth.ts` - MySQL configuration attempts
- `app/client/src/lib/db/index.ts` - MySQL connection pool
- `app/client/src/lib/db/schema/mysql-auth.ts` - MySQL Drizzle schema
- `app/client/drizzle.config.ts` - MySQL Drizzle config
- `app/client/mysql-schema.sql` - MySQL schema SQL
- `app/client/docker-compose.yml` - MySQL and Redis services
- `app/client/package.json` - Added mysql2 and ioredis

## Revert Commands

To go back to working SQLite version:
```bash
cd /home/warby/Workspace/Bunny
git checkout HEAD -- app/client/src/lib/auth.ts \
  app/client/src/lib/db/index.ts \
  app/client/docker-compose.yml

# Optionally remove MySQL containers if not needed
docker compose -f app/client/docker-compose.yml down mysql redis

# Restart client
docker compose -f app/client/docker-compose.yml restart client
```

## Testing

To test signup/login with current setup:
```bash
# With SQLite (works but slow)
curl -X POST http://localhost:3000/api/auth/sign-up/email \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email": "test@example.com", "password": "password123"}'

# Check logs
docker compose -f app/client/docker-compose.yml logs -f client
```

## Next Steps

1. Profile Better Auth to find the source of 10+ second delay
2. Consider switching to NextAuth v5 or Lucia for better performance
3. If continuing with Better Auth + MySQL, wait for Better Auth v2 or use their CLI tools properly
4. Document findings in an internal issue tracker
