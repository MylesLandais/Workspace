# Architectural Refactoring Plan

This document outlines the plan to refactor the repository into a more modular, scalable, and maintainable architecture.

## Phase 1: Establish Modular `src` Architecture & Refactor Providers

- [x] Create the `src` directory structure.
  - [x] `src/providers/asr/`
  - [x] `src/providers/vlm/`
  - [x] `src/datasets/`
  - [x] `src/infra/`
  - [x] `src/leaderboard/`
- [x] Move the existing ASR evaluation logic from `asr_evaluation/` into `src/providers/asr/`.
- [x] Consolidate the various ASR comparison scripts (`compare_asr_models_fixed.py`, `fast_asr_comparison.py`, etc.) into the main `asr_leaderboard.py` script.
- [x] Archive the old `asr_evaluation/` directory and redundant ASR scripts into `scripts/archive/`.

## Phase 2: Implement Hugging Face-Integrated Dataset Module

- [x] Create a `DatasetManager` class in `src/datasets/manager.py`.
- [x] Implement a `GophersHandler` to fetch and use the `landam/gogophers` dataset from the Hugging Face Hub.
- [x] Implement a `VaporeonHandler` that checks for a local audio file and downloads it with `yt-dlp` if missing.
- [x] Create a new top-level `dataset.py` script to provide a CLI for the `DatasetManager`.
- [x] Archive the old dataset-related scripts (`setup_dataset.py`, `manage_dataset.py`, etc.) into `scripts/archive/`.

## Phase 3: Reorganize Notebooks & Implement RunPod Scripting Layer

- [ ] Reorganize the `notebooks/` directory into subdirectories:
  - [ ] `notebooks/runpod_deployments/`
  - [ ] `notebooks/media_processing/`
- [ ] Archive vendor documentation for RunPod in `vendor/docs/runpod/`.
- [ ] Create a scripting layer in `scripts/runpod/` for wrapping `runpodctl` commands.
- [ ] Implement a `run_comfy_workflow.py` script to automate running workflows on a ComfyUI pod.
- [ ] Archive the old Python RunPod scripts into `scripts/archive/`.

## Phase 4: Implement Developer Tooling (Emoji Stripper Pre-Commit Hook)

- [ ] Create an emoji stripper script in `scripts/pre-commit-hooks/remove_emojis.py`.
- [ ] Create a `.pre-commit-config.yaml` file to configure the hook.
- [ ] Update `CONTRIBUTING.md` with instructions for setting up `pre-commit`.
