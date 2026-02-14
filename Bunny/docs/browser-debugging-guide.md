# Browser Debugging Guide

## Firefox Developer Tools

### Opening Developer Tools

1. **Keyboard Shortcuts:**
   - `F12` - Open/close Developer Tools
   - `Ctrl+Shift+K` (Linux/Windows) or `Cmd+Option+K` (Mac) - Open Console
   - `Ctrl+Shift+I` (Linux/Windows) or `Cmd+Option+I` (Mac) - Open Inspector

2. **Right-click Menu:**
   - Right-click anywhere on the page → "Inspect Element"
   - Then click the "Console" tab

### Key Tabs for Debugging

#### 1. Console Tab

- **Purpose:** View JavaScript errors, warnings, and log messages
- **What to look for:**
  - Red errors (🚨 prefixed errors from our error logger)
  - Network errors
  - Authentication errors
  - Sentry event IDs (✅ Event captured with ID: ...)

#### 2. Network Tab

- **Purpose:** Monitor HTTP requests and responses
- **What to check:**
  - Failed requests (red status codes like 500, 400)
  - Request payloads (click request → "Payload" tab)
  - Response bodies (click request → "Response" tab)
  - Request headers (especially Authorization headers)

#### 3. Inspector Tab

- **Purpose:** Inspect and modify DOM elements
- **Useful for:** Checking form values, element states, CSS issues

### Debugging Authentication Errors

#### Step 1: Check Console for Error Details

When you see an error, look for:

```
🚨 [timestamp] Error Captured
Error: [error message]
Stack: [stack trace]
Tags: { auth_flow: "signup", error_code: "..." }
Extra Context: { email: "...", error_message: "..." }
```

#### Step 2: Check Network Tab

1. Open Network tab
2. Filter by "Fetch/XHR" to see API calls
3. Look for requests to `/api/auth/*`
4. Click on the failed request
5. Check:
   - **Status:** Should show the HTTP status code (500, 400, etc.)
   - **Response:** Click "Response" tab to see server error message
   - **Payload:** Click "Payload" tab to see what was sent

#### Step 3: Check Server Logs

The browser console shows client-side errors, but the **actual server error** is in your terminal where Next.js is running:

```bash
# Look for errors like:
[Auth] POST /api/auth/sign-up failed [Error details]
```

### Common Error Patterns

#### "Signup error: unknown"

- **Cause:** Error object structure not recognized
- **Fix:** Check Network tab → Response tab for actual error
- **Check:** Server terminal logs for full stack trace

#### 500 Internal Server Error

- **Cause:** Server-side error (database, auth service, etc.)
- **Debug:**
  1. Check server terminal for full error
  2. Check Network tab → Response for error message
  3. Verify database connection
  4. Check environment variables

#### Network Error

- **Cause:** Server not reachable or CORS issue
- **Debug:**
  1. Verify server is running (`devenv up`)
  2. Check server URL in Network tab
  3. Verify CORS configuration

### Using Sentry for Error Tracking

#### Viewing Errors in Sentry

1. **Event ID in Console:**

   ```
   [Sentry] ✅ Event captured with ID: c42d2df724ab48d2b73cdc9d9d104bd1
   ```

2. **Find in Sentry Dashboard:**
   - Go to your Sentry project
   - Search for the event ID
   - View full error details, stack trace, and context

#### Sentry Context

Our error logger automatically includes:

- **Tags:** `auth_flow`, `error_code`, `http_status`
- **Extra Context:** `email`, `error_message`, `error_data`, `full_result`
- **User Context:** Email (if available)

### Debugging Tips

#### 1. Enable Verbose Logging

The error logger already logs comprehensive details. Check console for:

- Full error objects
- Error codes and messages
- HTTP status codes
- Request/response data

#### 2. Use Breakpoints

In Firefox Console:

```javascript
// Pause on all errors
debugger; // Add this in your code to pause execution
```

Or use Firefox's built-in breakpoint feature:

1. Open Debugger tab
2. Find your file (e.g., `SignIn.tsx`)
3. Click line number to set breakpoint
4. Trigger the action (signup/signin)
5. Step through code execution

#### 3. Inspect Network Requests

For auth requests, check:

- **Request URL:** Should be `/api/auth/sign-up` or `/api/auth/sign-in`
- **Request Method:** Should be `POST`
- **Request Headers:** Check for `Content-Type: application/json`
- **Request Payload:** Should include `email`, `password`, etc.
- **Response Status:** 200 = success, 4xx/5xx = error
- **Response Body:** Contains error details

#### 4. Check Application State

In Console, you can inspect:

```javascript
// Check if Sentry is initialized
window.__SENTRY__;

// Check current session (if available)
localStorage.getItem("session");
```

### Quick Debugging Checklist

When debugging auth errors:

- [ ] Check browser console for error messages
- [ ] Check Network tab for failed requests
- [ ] Check server terminal for server-side errors
- [ ] Verify database connection (`devenv up`)
- [ ] Check environment variables are set
- [ ] Look for Sentry event ID in console
- [ ] Check Sentry dashboard for full error details
- [ ] Verify request payload in Network tab
- [ ] Check response body in Network tab

### Firefox-Specific Features

#### 1. Responsive Design Mode

- `Ctrl+Shift+M` - Test on different screen sizes
- Useful for mobile debugging

#### 2. Accessibility Inspector

- Check form labels and ARIA attributes
- Useful for accessibility debugging

#### 3. Performance Monitor

- Monitor JavaScript performance
- Identify slow operations

### Getting Help

When reporting errors, include:

1. **Console output:** Copy the full error from console
2. **Network request:** Screenshot of failed request (Status, Response tabs)
3. **Server logs:** Copy error from terminal
4. **Sentry Event ID:** If available
5. **Steps to reproduce:** What you did before the error
