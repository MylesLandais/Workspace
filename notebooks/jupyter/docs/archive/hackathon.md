# Hackathon: Discord + ComfyUI Virtual Try-On — 8-12 hour plan

This document consolidates the 3-phase hackathon plan and "vibe coding" guidance for rapid prototyping a Discord bot that integrates ComfyUI for virtual try-on image generation.

Goal: Build a minimal, demo-ready Discord bot that accepts user images (person + garment), runs a ComfyUI workflow to apply the garment, and returns results in the Discord channel.

Phases (high level)

1. Architecture & Modular Design (2-3 hours)
2. Testing Implementation (3-4 hours)
3. Continuous Improvement (2-3 hours)

---

## Phase 1 — Architecture & Modular Design (2-3 hours)

Objectives
- Outline the architecture and project structure.
- Configure a reproducible devcontainer and Dockerfile.
- Prototype a ComfyUI workflow in a notebook.

Tasks
- Create branch: `hackathon/tryon` and skeleton directories: `src/bot/`, `src/comfyui/`, `notebooks/`, `scripts/`.
- Devcontainer: ensure `.devcontainer/devcontainer.json` forwards ports 8888 (Jupyter) and 8188 (ComfyUI), and Dockerfile pins key CLIs (e.g. `runpodctl` pinned or vendored).
- Notebook prototype: `notebooks/comfyui-workflow.ipynb` — build a ComfyUI graph for: LoadPerson -> LoadGarment -> ImageStitch -> QwenImageEdit -> KSampler -> Save.

Deliverables
- Devcontainer builds locally and in CI.
- Prototype notebook that executes headless ComfyUI workflow against sample images.

Vibe-coding tips
- Use GitHub Copilot Chat in VS Code to generate scaffolding comments, then refine.
- Keep prompts short and goal-focused: e.g. "Generate a ComfyUI node JSON that resizes and stitches two images." 

---

## Phase 2 — Testing Implementation (3-4 hours)

Objectives
- Implement the Discord bot and integration.
- Test end-to-end with sample images using notebooks.

Tasks
- Implement `src/bot/main.py` (Pycord) with `/tryon` slash command.
- Add a queue worker `src/bot/worker.py` to handle job processing and return messages.
- Implement `src/comfyui/client.py` for WebSocket/HTTP interactions with ComfyUI.
- Add `notebooks/bot-integration.ipynb` with test runs and VRAM profiling.

Deliverables
- Working slash command in a local dev environment.
- Notebook demonstrating end-to-end processing and sample outputs.

Vibe-coding tips
- Break tasks into single-responsibility prompts (e.g. "Download Discord attachment to /tmp and return saved path").
- Review generated code for security (no secret leaks), concurrency issues, and VRAM assumptions.

---

## Phase 3 — Continuous Improvement (2-3 hours)

Objectives
- Deploy the MVP to RunPod and optimize.
- Add profiling, cost controls, and fallback strategies.

Tasks
- Create idempotent scripts under `scripts/runpod/` to favorite templates and create/delete deployments.
- Document cost vs accuracy tradeoffs and VRAM recommendations.
- Implement autoscale/preview mode: lower steps/resolution for quick previews and high-quality for final renders.

Deliverables
- Deployable script and documented RunPod template choices.
- Optimized notebooks and profiling metrics.

Vibe-coding tips
- Use Copilot to generate deployment script templates, but pin versions (e.g. `RUNPODCTL_VERSION=v1.14.4`) for reproducibility.

---

## Vibe Coding Best Practices (Short)
- Use natural-language prompts in the code file or Copilot Chat; iterate on the result.
- Keep tasks small: prefer many small prompts rather than one large one.
- Always review AI-generated code for correctness and security.
- Save reusable prompts in `.github/prompts/`.

---

## Quick Start (for the hackathon)
1. Create branch and skeleton:
```bash
git checkout -b hackathon/tryon
mkdir -p src/bot src/comfyui notebooks scripts/runpod
git add .
```
2. Open in VS Code and reopen in devcontainer (if using DevContainer).
3. Start with `notebooks/comfyui-workflow.ipynb` to validate ComfyUI graph before implementing bot code.

---

## Links & References
- ComfyUI docs and nodes
- RunPod docs
- GitHub Copilot best practices

---

Commit your work frequently and keep the notebooks in `notebooks/` for reproducibility.