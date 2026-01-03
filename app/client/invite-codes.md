# Invite Codes

## Valid Invite Keys

### Special Codes
- `ASDF-WHALECUM` - Special invite code

### Pattern-Based Codes
- Keys starting with `SN-` are automatically valid

## How to Add New Invite Codes

### Option 1: Add Specific Code
Edit `app/client/app/invite/page.tsx`:
```typescript
const validKeys = [
  "ASDF-WHALECUM",
  "YOUR-NEW-CODE"
];
```

### Option 2: Add Pattern
Edit `app/client/app/invite/page.tsx`:
```typescript
setStatus(
  inviteKey.startsWith("SN-") ||
  inviteKey.startsWith("YOUR-PREFIX") ||
  validKeys.includes(inviteKey)
    ? "valid"
    : "invalid"
);
```

## Note
This is currently client-side mock validation. For production:
1. Store invite codes in database
2. Create API endpoint for validation
3. Track code usage (one-time use)
4. Admin interface for generating codes

## Testing
Test invite codes with:
```bash
docker compose exec client bun run test:e2e
```

Tests verify:
- Invalid codes show error
- SN- prefix codes work
- Specific codes (like ASDF-WHALECUM) work
- Valid codes redirect to signup with key
