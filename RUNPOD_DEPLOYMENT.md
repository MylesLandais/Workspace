# RunPod Serverless Deployment Guide

## Overview

This document describes the manual deployment configuration for RunPod Serverless endpoints using the `feature/runpod-worker` branch.

**Note:** Future automation via Terraform/Pulumi is planned. See `TODO.md` for IaC roadmap.

## GitHub Repository Configuration

| Setting | Value |
|---------|-------|
| **Repository** | `MylesLandais/ComfyUI` |
| **Branch** | `feature/runpod-worker` |
| **Dockerfile Path** | `Dockerfile.runpod` |
| **Build Context** | `.` |
| **Credentials** | No Credentials (public repo) |

## Endpoint Settings

### GPU Configuration

- **Primary:** `32 GB PRO` (4090) - $0.00044/s flex, $0.00031/s active
- **Fallback:** `24 GB PRO` - $0.00031/s flex, $0.00021/s active

Multiple selections improve availability during high demand.

### CUDA Version Filter

**Select:** `12.4` and all newer versions (`12.5`, `12.6`, `12.7`, `12.8`)

The Dockerfile uses CUDA 12.8.1, but selecting all compatible versions increases available hardware pool. CUDA is backward compatible, so workers with newer drivers can run older CUDA containers.

**Reference:** [RunPod CUDA Version Selection Docs](https://docs.runpod.io/serverless/endpoints/endpoint-configurations#cuda-version-selection)

### Worker Scaling

| Setting | Recommended Value |
|---------|-------------------|
| **Active Workers** | `0` (or `1` to eliminate cold starts) |
| **Max Workers** | `2` (adjust based on expected load + 20% buffer) |
| **GPUs per Worker** | `1` |
| **Auto-scaling Type** | `Queue delay` (default 4s threshold) |

### Lifecycle Settings

| Setting | Value |
|---------|-------|
| **Idle Timeout** | `5s` (default) |
| **Execution Timeout** | `600s` (10 minutes, max 24h) |
| **Job TTL** | `24h` (default) |

### Advanced Settings

#### Network Volumes

**Required:** Attach your network volume ID for persistent model storage.

**Warning:** Network volumes introduce latency and restrict workers to specific datacenters. Only use if your workload requires shared persistence or datasets larger than container limits.

#### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | **Yes** | Required for Nano Banana node (Gemini API access) |

#### Data Centers

**Recommended:** Allow all datacenters for maximum availability.

#### Expose HTTP/TCP Ports

**Not required** for standard serverless handler. Only enable if using WebSockets or persistent connections.

## Deployment Flow

### Automatic (via GitHub Releases)

1. Push commits to `feature/runpod-worker` branch
2. GitHub Actions workflow validates Dockerfile and creates release
3. RunPod detects release and automatically rebuilds endpoint
4. Monitor build status in RunPod console

### Manual Release (if needed)

```bash
# Create release manually via GitHub CLI
gh release create runpod-$(date +%Y%m%d-%H%M%S) \
  --branch feature/runpod-worker \
  --title "RunPod Build - $(date +%Y%m%d-%H%M%S)" \
  --notes "Manual deployment"
```

## Build Verification

After release is created:

1. Check RunPod console → Serverless → Endpoints
2. Navigate to your endpoint
3. View build logs for new build
4. Verify build completes successfully
5. Test endpoint with workflow execution

## Troubleshooting

### Build Fails: "CUDA image not found"

- Verify CUDA version tag exists: https://hub.docker.com/r/nvidia/cuda/tags
- Check Dockerfile.runpod `BASE_IMAGE` ARG matches available tags
- Current: `nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04`

### Missing Custom Node Errors

- Verify node is installed in `Dockerfile.runpod` (see lines 84-92)
- Check node repository URL is correct
- Review build logs for installation errors

### Network Volume Not Mounted

- Verify volume ID in endpoint configuration
- Check volume exists and is in correct datacenter
- Ensure endpoint datacenter matches volume location

## References

- [RunPod Serverless Documentation](https://docs.runpod.io/serverless)
- [RunPod Endpoint Settings](https://docs.runpod.io/serverless/endpoints/endpoint-configurations)
- [CUDA Version Selection](https://docs.runpod.io/serverless/endpoints/endpoint-configurations#cuda-version-selection)
- [GitHub Integration](https://docs.runpod.io/serverless/workers/github-integration)

