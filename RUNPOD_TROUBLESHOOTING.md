# RunPod Deployment Troubleshooting Guide

This guide documents common deployment issues, their symptoms, and resolution steps.

## Table of Contents

- [Registry Push Failure (RISK-001)](#registry-push-failure-risk-001)
- [Layer Locking Errors (RISK-002)](#layer-locking-errors-risk-002)
- [Missing Git in Build Context (RISK-010)](#missing-git-in-build-context-risk-010)
- [Incident Reporting](#incident-reporting)

---

## Registry Push Failure (RISK-001)

### Symptoms

- Build completes successfully ("Build complete.")
- Layer locking errors observed during export phase
- Registry push fails immediately after build completion:
  ```
  Error: neither /app/registry-push/output.tar found nor /app/registry-push/.output-image/index.json present
  Image push finished with wrong exit code
  ```

### Immediate Diagnostic Steps

1. **Check build logs for layer locking patterns**
   ```bash
   grep -E "(layer.*locked|registry-push)" build-logs-*.txt
   ```

2. **Identify specific layer hash causing issues**
   - Look for: `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef`
   - Note lock duration (typically 760ms - 1.3s)

3. **Verify build completion**
   - Confirm "Build complete." message exists
   - Check that all Docker build steps completed successfully

4. **Document build ID and timestamp**
   - Required for RunPod support escalation

### Immediate Actions

1. **Manual Retry**
   - Go to RunPod Console → Serverless → Your Endpoint
   - Click "Rebuild" or trigger new release
   - **Wait 5-10 minutes** between retries to avoid infrastructure contention

2. **Check for Pattern Recurrence**
   - If this is the 2nd+ occurrence, document pattern
   - Note if specific layer hash consistently fails

3. **Monitor Next Build**
   - Watch for layer locking errors during export
   - Time the lock duration
   - Check if push failure follows locking errors

### Escalation Criteria

**Contact RunPod Support if:**
- Build fails 3+ times consecutively
- Same layer hash fails in multiple builds
- Lock duration exceeds 2 seconds
- Builds consistently fail during registry push phase

**Required Information for Support:**
- Build ID(s) from failed builds
- Timestamp of failures
- Layer hash that consistently locks: `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef`
- Lock duration metrics
- Frequency of occurrence
- Error message: `"Error: neither /app/registry-push/output.tar found nor /app/registry-push/.output-image/index.json present"`

---

## Layer Locking Errors (RISK-002)

### Symptoms

Multiple RPC errors during Docker layer export:
```
ERROR: (*service).Write failed: rpc error: code = Unavailable desc = 
ref layer-sha256:... locked for Xµs/ms: unavailable
```

### Severity Assessment

- **Low (< 100ms)**: Normal infrastructure contention, typically resolves
- **Medium (100ms - 1s)**: Monitor, may indicate resource pressure
- **High (> 1s)**: Correlated with registry push failures (RISK-001)

### Actions by Severity

**Low (< 100ms):**
- No action required
- Build typically completes successfully

**Medium (100ms - 1s):**
- Monitor for pattern
- Document if recurring
- Check if push succeeds despite locking

**High (> 1s):**
- **High correlation with RISK-001**
- Document layer hash and lock duration
- Prepare for potential push failure
- Consider retry with delay after completion

### Correlation with RISK-001

When layer locking errors occur with duration > 1 second, there is a high correlation with subsequent registry push failures. The specific layer `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` has been observed to lock consistently before push failures.

**Action:** If this layer hash appears with >1s lock duration, expect push failure and prepare retry strategy.

---

## Missing Git in Build Context (RISK-010)

### Symptoms

Build logs show warning message:
```
WARNING: current commit information was not captured by the build: git was not found in the system: exec: "git": executable file not found in $PATH
```

### Understanding the Warning

**This is an informational warning, NOT an error.** The build will complete successfully despite this warning.

**What's happening:**
- RunPod's build system attempts to capture git commit information before the Docker build starts
- Git is not available in RunPod's build context (the environment where they prepare the build)
- This is a RunPod infrastructure limitation, not a code issue

**Important distinction:**
- Git is **correctly installed** in the Docker container (line 21 of `Dockerfile.runpod`)
- Git is used inside the container for custom node installations (e.g., cloning repositories)
- The missing git is only in RunPod's pre-build context where they try to capture commit metadata

### Impact Assessment

**Severity:** LOW (Informational only)

- Builds complete successfully
- No functional impact on deployment
- Only affects build metadata tracking
- Does not block or delay builds

### Actions

**No action required** - this is expected behavior due to RunPod infrastructure limitations.

**Alternative tracking methods:**
- Use GitHub release tags (already implemented in CI/CD workflow)
- Reference build IDs for build tracking
- Commit information available in GitHub Actions workflow logs

### Related Information

- **Risk:** RISK-010 (see `RISK_REGISTRY.md`)
- **Dockerfile:** Git correctly installed on line 21 for container use
- **CI/CD:** GitHub releases provide commit tracking via workflow

---

## Incident Reporting

### When to Create Incident Report

- RISK-001 occurs 2+ times
- Pattern of layer locking + push failure observed
- Build failures block critical deployments
- Support escalation required

### Incident Report Template

```markdown
## RunPod Build Failure Incident Report

**Date:** YYYY-MM-DD HH:MM UTC
**Build ID(s):** 
- Build ID 1: `xxxxx-xxxxx-xxxxx-xxxxx`
- Build ID 2: `xxxxx-xxxxx-xxxxx-xxxxx`

**Error Type:** Registry Push Failure (RISK-001)

### Timeline
- Build started: YYYY-MM-DD HH:MM UTC
- Build completed: YYYY-MM-DD HH:MM UTC
- Push failed: YYYY-MM-DD HH:MM UTC

### Error Details
```
Error: neither /app/registry-push/output.tar found nor /app/registry-push/.output-image/index.json present
Image push finished with wrong exit code
```

### Layer Locking Pattern
- Layer hash: `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef`
- Lock duration: Xms to Yms
- Frequency: N occurrences before push failure

### Build Details
- Dockerfile: `Dockerfile.runpod`
- Branch: `feature/runpod-worker`
- Commit: `xxxxx`
- Image size: ~X GB

### Attempted Resolutions
- [ ] Manual retry #1: Result
- [ ] Manual retry #2: Result
- [ ] Delayed retry (10min): Result

### Impact
- Deployments blocked: Yes/No
- Build time wasted: ~X minutes
- Endpoint state: READY/BUILDING/FAILED

### Supporting Evidence
- Build logs attached: Yes/No
- Pattern observed in previous builds: Yes/No
- Related risk: RISK-001, RISK-002
```

### Escalation Path

1. **Internal Documentation**
   - Update `RISK_REGISTRY.md` with new occurrence
   - Document in worklog session
   - Update this troubleshooting guide if new patterns emerge

2. **RunPod Support**
   - Use incident report template above
   - Include all build IDs and timestamps
   - Provide layer hash and lock duration metrics
   - Request infrastructure investigation

3. **Monitor Resolution**
   - Track if RunPod addresses issue
   - Document any workarounds or fixes provided
   - Update risk registry with resolution status

---

## Quick Reference

### Common Commands

```bash
# Check RunPod endpoint status
python scripts/runpod_monitor.py status

# Wait for build completion
python scripts/runpod_monitor.py wait

# Analyze build logs for patterns
grep -E "(registry-push|layer.*locked)" build-logs-*.txt

# Extract layer hash from logs
grep "layer-sha256:" build-logs-*.txt | cut -d: -f3 | sort -u
```

### Related Documents

- `RISK_REGISTRY.md` - Comprehensive risk tracking
- `RUNPOD_DEPLOYMENT.md` - Deployment configuration guide
- `scripts/runpod_monitor.py` - Build monitoring tool
- Worklogs in `251218-worklog.md` - Session-specific error details

---

*Last Updated: 2025-12-19 (Added RISK-010: Missing Git in Build Context)*

