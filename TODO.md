# Infrastructure as Code (IaC) TODO

## Current State

RunPod deployment is **manually configured** via the RunPod console. This document tracks automation improvements.

## High Priority

### 1. RunPod Endpoint Configuration as Code

**Goal:** Automate endpoint creation/updates via Infrastructure as Code

**Options:**
- [ ] Terraform provider for RunPod (if available)
- [ ] Pulumi with RunPod API/SDK
- [ ] Custom Python script using RunPod GraphQL API

**Configuration to automate:**
- [ ] Endpoint name and type (Queue-based serverless)
- [ ] GitHub repository connection (repo, branch, Dockerfile path)
- [ ] GPU selection (32GB PRO, 24GB PRO with fallback)
- [ ] CUDA version filter (>=12.4)
- [ ] Worker scaling (active, max, GPUs per worker)
- [ ] Auto-scaling type and thresholds
- [ ] Lifecycle timeouts (idle, execution, TTL)
- [ ] Network volume attachment
- [ ] Environment variables (`GOOGLE_API_KEY`)

**Reference:** [RunPod Endpoint Settings Docs](https://docs.runpod.io/serverless/endpoints/endpoint-configurations)

### 2. Secrets Management

**Current:** Manual entry in RunPod console

**Target:**
- [ ] Store `GOOGLE_API_KEY` in GitHub Secrets
- [ ] Use GitHub Actions to inject secrets via RunPod API
- [ ] Or: Use RunPod's secret management (if available)
- [ ] Or: Use external secret manager (AWS Secrets Manager, HashiCorp Vault, etc.)

### 3. Network Volume Provisioning

**Current:** Manual creation and attachment

**Target:**
- [ ] Automate network volume creation
- [ ] Volume size configuration
- [ ] Datacenter selection
- [ ] Auto-attach to endpoint
- [ ] Volume lifecycle management (backup, cleanup)

### 4. Branch/Release Automation

**Current:** GitHub Actions creates releases, RunPod watches releases

**Improvements:**
- [ ] Validate release triggers rebuild (test loop)
- [ ] Add release versioning strategy (semver vs timestamp)
- [ ] Rollback mechanism (revert to previous release)
- [ ] Release notes generation from commits

### 5. Multi-Environment Support

**Goal:** Separate dev/staging/prod endpoints

- [ ] Environment-specific configurations
- [ ] Separate GitHub branches per environment
- [ ] Environment-specific secrets
- [ ] Cost tracking per environment

## Medium Priority

### 6. Build Validation Pipeline

**Current:** Basic Dockerfile validation in GitHub Actions

**Enhancements:**
- [ ] Test Docker image build locally before release
- [ ] Validate custom node installations
- [ ] Test handler.py with sample workflows
- [ ] Image size optimization checks
- [ ] Security scanning (trivy, Snyk)

### 7. Monitoring and Alerting

- [ ] Integration with RunPod monitoring script (`scripts/runpod_monitor.py`)
- [ ] GitHub Actions workflow to check build status
- [ ] Slack/Discord notifications for build failures
- [ ] Cost monitoring alerts
- [ ] Endpoint health checks

### 8. Documentation Automation

- [ ] Auto-generate deployment docs from IaC config
- [ ] Keep `RUNPOD_DEPLOYMENT.md` in sync with actual config
- [ ] Version-controlled endpoint configurations

## Low Priority

### 9. Cost Optimization

- [ ] Analyze GPU usage patterns
- [ ] Optimize worker scaling thresholds
- [ ] Right-size network volumes
- [ ] Idle timeout tuning

### 10. Disaster Recovery

- [ ] Automated backup of endpoint configurations
- [ ] Recovery playbooks
- [ ] Endpoint state export/import

## Implementation Notes

### RunPod API Access

RunPod uses GraphQL API. Need to:
1. Get API key from RunPod console
2. Store as GitHub Secret `RUNPOD_API_KEY`
3. Use in automation scripts

**Reference:** [RunPod GraphQL Spec](https://docs.runpod.io/reference/graphql-spec)

### Current Manual Settings (for reference)

See `RUNPOD_DEPLOYMENT.md` for current manual configuration values that need to be codified.

## Related Files

- `RUNPOD_DEPLOYMENT.md` - Manual deployment guide
- `.github/workflows/runpod-build.yml` - Current CI/CD workflow
- `scripts/runpod_monitor.py` - Build monitoring script
- `Dockerfile.runpod` - Container build definition

