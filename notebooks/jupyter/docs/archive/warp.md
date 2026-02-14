# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

This repository is an **ASR (Automatic Speech Recognition) evaluation system** and **media processing toolkit** built for:
- Benchmarking multiple ASR models (Whisper variants, Canary-Qwen, OLMoASR, etc.)
- Processing video/audio content with subtitle generation and synchronization
- Managing evaluation datasets with Hugging Face integration
- Running distributed GPU workloads on RunPod cloud infrastructure

The system supports both containerized development (Docker/JupyterLab) and various deployment modes (full evaluation, fast GPU-optimized, minimal CPU-only).

## Key Commands

### Development Environment

**Start containerized environment:**
```bash
./start.sh                    # Start Docker Compose services with auto-token retrieval
docker compose up --build -d  # Manual Docker Compose startup
```

**Access the environment:**
```bash
docker compose exec jupyterlab bash  # Shell into container as jovyan user
# Work directory: /home/jovyan/workspaces
```

### Testing and Evaluation

**Run ASR model tests:**
```bash
python run_tests.py           # Basic model availability test
python run_tests.py --full    # Full pytest suite with coverage
```

**Run ASR model evaluations:**
```bash
python asr_leaderboard.py                           # Full comprehensive evaluation
python asr_leaderboard.py --mode fast              # GPU-optimized fast evaluation  
python asr_leaderboard.py --mode minimal           # CPU-only minimal evaluation
python asr_leaderboard.py --debug                  # Enable detailed logging
```

### Dataset Management

**Manage evaluation datasets:**
```bash
python dataset.py list                             # List available datasets
python dataset.py info vaporeon                    # Get dataset information
python dataset.py get vaporeon --path datasets/    # Download/verify dataset
```

## Architecture Overview

### Core Components

**ASR Evaluation System (`src/providers/asr/`):**
- `core/interfaces.py` - Abstract base classes (`ASRModelAdapter`, `TranscriptionResult`, `ModelInfo`)
- `adapters/` - Model-specific implementations:
  - `faster_whisper_adapter.py` - Local Whisper via faster-whisper
  - `canary_qwen_adapter.py` - NVIDIA Canary-Qwen models via transformers
  - `olmoasr_adapter.py` - Allen AI OLMoASR models
- `core/config.py` - Configuration management (`ConfigManager` loads from `config/asr_models.yaml`)
- `storage/postgres_storage.py` - PostgreSQL result persistence

**Dataset Management (`src/datasets/`):**
- `manager.py` - Auto-discovery system for dataset handlers
- `base_handler.py` - Abstract dataset handler interface
- `handlers/` - Dataset-specific handlers (vaporeon, gophers, etc.)

**Media Processing (`src/`):**
- `subtitle_processor.py` - Subtitle generation and formatting
- `video_remuxer.py` - Video container operations
- `process_wmv_files.py` - Windows Media Video processing

**Infrastructure (`src/infra/`):**
- `runpod_manager.py` - RunPod GPU cloud management

### Configuration System

The system uses a hierarchical configuration approach:

1. **Model Configuration (`config/asr_models.yaml`):**
   - Defines all supported ASR models with performance targets
   - Specifies device requirements, use cases, and fallback chains
   - Supports model selection by use case: `highest_accuracy`, `fastest_processing`, `multilingual`, `transparent`

2. **Environment Variables (`.env`):**
   - API keys: `OPENROUTER_API_KEY`, `CLAUDE_API_TOKEN`, `RUNPOD_API_KEY`
   - Hugging Face: `HF_TOKEN`, `HF_USERNAME`
   - Database: `POSTGRES_*` settings

3. **Runtime Configuration:**
   - Models auto-discovered via `ConfigManager.get_models_by_use_case()`
   - Fallback chains ensure graceful degradation
   - Processing modes: transcript_only, subtitles, diarization, real_time

### Evaluation Flow

1. **Model Registration:** `ConfigManager` loads model configs from YAML
2. **Adapter Creation:** Factory pattern creates appropriate `ASRModelAdapter` instances
3. **Benchmarking:** `asr_leaderboard.py` runs models against reference datasets
4. **Metrics Calculation:** WER/CER computed via Levenshtein distance
5. **Result Storage:** Optional PostgreSQL persistence for historical analysis

## Development Patterns

### Adding New ASR Models

1. **Create adapter** in `src/providers/asr/adapters/new_model_adapter.py`:
   - Inherit from `ASRModelAdapter`
   - Implement `transcribe()`, `get_model_info()`, `is_available()`

2. **Add configuration** in `config/asr_models.yaml`:
   - Define model metadata, parameters, device requirements
   - Add to appropriate use case categories

3. **Register in evaluation** (`asr_leaderboard.py`):
   - Add to `models_to_test` list with factory function

### Adding New Datasets

1. **Create handler** in `src/datasets/handlers/dataset_name_handler.py`:
   - Inherit from `BaseDatasetHandler`
   - Implement `get()`, `info()`, `verify()`

2. **Auto-discovery:** `DatasetManager` will automatically detect and register the handler

## Important Rules and Constraints

### Security Requirements
- **Talisman pre-commit hook is mandatory** - scans for secrets/sensitive data
- **Never commit API keys** - use `.env` file with environment variables
- **No emojis** in code or documentation (organization policy)

### Development Environment
- **Use Docker containers** for development to avoid system package conflicts
- **Work as `jovyan` user** inside containers (`/home/jovyan/workspaces`)
- **GPU support enabled** in Docker Compose for CUDA models

### Code Quality
- **Run tests before commits:** `python run_tests.py --full`
- **Follow Python conventions:** snake_case, type hints
- **Security-first approach:** Talisman will block unsafe commits

### Model Performance Targets
Reference from `config/asr_models.yaml`:
- **Excellent WER:** < 5% (canary-qwen-2.5b targets 5.63%)
- **Good WER:** < 10% (faster-whisper-base targets 9.2%)
- **Acceptable WER:** < 20%

### Hardware Considerations
- **VRAM requirements vary:** tiny models (1GB) to large models (16GB+)
- **Fallback chains defined** for when preferred models unavailable
- **CPU/GPU mode selection** automatic based on hardware availability

## File Structure Notes

- **Notebooks in `notebooks/`** are git-tracked for reproducible experiments
- **Configuration in `config/`** centralized for model and evaluation settings
- **Tests in `tests/`** with pytest configuration in `pytest.ini`
- **Docker setup** supports both minimal (`Dockerfile.minimal`) and full (`Dockerfile`) environments
- **Media processing logs** go to `.log` files (gitignored for sensitive data)
