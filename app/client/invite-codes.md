# Invite Codes

## System Overview

The invite code system is fully integrated with the database and provides server-side validation, tracking, and management.

## Active Invite Codes

### Stealth Release Code
- `STEALTH-2026` - Valid until January 7, 2027
- Unlimited uses
- Full registration with username support

## How to Generate New Invite Codes

### Via API
```bash
docker compose exec client bun -e "
fetch('http://localhost:3000/api/invite/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    code: 'YOUR-CODE-HERE',
    expiresInDays: 365,
    maxUses: null,
    notes: 'Description of this invite code'
  })
})
.then(res => res.json())
.then(data => console.log(data));
"
```

### Via Database
```bash
docker compose exec mysql mysql -uroot -pbetterauth bunny_auth
```
Then:
```sql
INSERT INTO invite_code (id, code, expires_at, used_count, created_at, updated_at)
VALUES (UUID(), 'YOUR-CODE', DATE_ADD(NOW(), INTERVAL 365 DAY), 0, NOW(), NOW());
```

## Features

1. Server-side validation via `/api/invite/validate`
2. Usage tracking (increment count on successful registration)
3. Expiration dates
4. Optional maximum use limits
5. Full registration flow with username selection
6. Join date tracking

## Registration Flow

1. User enters invite code at `/invite`
2. System validates code via API
3. Valid codes redirect to `/auth?mode=signup&invite=CODE`
4. User fills in:
   - Full name
   - Email
   - Password
   - Username (required for invite-based signups)
5. Upon successful registration:
   - User account is created
   - Username is saved
   - Join date is recorded
   - Invite code usage count is incremented

## Testing

Test invite codes:
```bash
docker compose exec client bun run test:e2e
```

Test API validation:
```bash
docker compose exec client bun -e "
fetch('http://localhost:3000/api/invite/validate?code=STEALTH-2026')
  .then(res => res.json())
  .then(data => console.log(data));
"
```
