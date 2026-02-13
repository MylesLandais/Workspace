# Nebula Jupyter System

> !Important: Organization is no longer accepting pull requests to be made with any emojis, please keep this in mind before submitting to code review channels
> Please read `CONTRIBUTING.md` for more information on getting involved with the project
> For a summary of our project's evolution, see the `HISTORY.md` file.

## ASR Hearing Benchmark Roadmap

### Phase 1: Foundation (Completed)
- [x] Core ASR evaluation framework
- [x] Model adapter architecture (FasterWhisper, OLMoASR)
- [x] Basic metrics calculation (WER, CER, processing time)
- [x] PostgreSQL storage and leaderboard system
- [x] Docker development environment

### Phase 2: Production Readiness Testing (Next 2-4 weeks)
- [ ] **Robustness Testing**
  - Audio quality degradation tests (noise, compression, distortion)
  - Multiple speaker scenarios and accent variations
  - Real-world audio conditions (background noise, reverb, etc.)
  
- [ ] **Performance Benchmarking**
  - Latency requirements for real-time applications
  - Memory usage and resource consumption analysis
  - Concurrent processing capabilities
  - Batch processing optimization

- [ ] **Model Coverage Expansion**
  - OpenAI Whisper API integration via OpenRouter
  - Additional open-source models (Wav2Vec2, SpeechT5)
  - Specialized domain models (medical, legal, technical)

### Phase 3: Advanced Evaluation Metrics (4-6 weeks)
- [ ] **Semantic Understanding**
  - Key phrase detection accuracy
  - Intent recognition in transcribed text
  - Domain-specific terminology handling
  
- [ ] **Production Scenarios**
  - Meeting transcription accuracy
  - Phone call quality audio processing
  - Streaming vs batch processing comparison
  - Multi-language support evaluation

### Phase 4: Automated Testing Pipeline (6-8 weeks)
- [ ] **Continuous Integration**
  - Automated model regression testing
  - Performance monitoring and alerting
  - A/B testing framework for model updates
  
- [ ] **Dataset Management**
  - Synthetic audio generation for edge cases
  - Privacy-compliant test dataset creation
  - Benchmark dataset standardization

### Phase 5: Production Deployment Support (8-10 weeks)
- [ ] **Model Selection Framework**
  - Cost vs accuracy optimization
  - Deployment environment recommendations
  - Model switching and fallback strategies
  
- [ ] **Monitoring and Observability**
  - Real-time performance tracking
  - Error pattern analysis
  - User feedback integration

## Current System Components

### ASR Evaluation Framework
- **Model Adapters**: Unified interface for different ASR models
- **Metrics Engine**: WER, CER, BLEU score calculation
- **Leaderboard System**: PostgreSQL-backed ranking and comparison
- **Test Suite**: Comprehensive model availability and functionality testing

### Development Tools
- **Docker DevContainers**: Isolated, reproducible development environment with CUDA support
- **Secret Scanning**: Talisman pre-commit hooks for security
- **Spec-Driven Development**: Kiro AI assistant integration for structured development

## Legacy Components

- cleanup runpod instances
- init runpod ollama
- openrouter_tool_use
- dataset_pipeline
    - Workflows for creating/updating and tracking datasets across versioning
- Finetune_Wan22
- Finetune_QwenImg
- bench_eval_vlm_responses
    - used for shooting out different language models across open router or local/ollama+hf data

## Environment Configuration

Create a `.env` file from `.env.example` and configure the following:

```bash
RUNPOD_API_KEY=rpa_....
OPENROUTER_API_KEY=sk-or-v1-..........
FINNHUB_API_KEY=....
HUGGINGFACE_TOKEN=hf_your_huggingface_token_here
```

**Additional Services**: HuggingFace, Github, and Runpod all leverage shared SSH keys for system access.

**Completed Items**:
- JSON configuration loading
- HuggingFace token configuration
- Dynamic dataset path resolution
- Model capability flags

**Remaining TODO Items**:
- Model adapter implementations (GraniteSpeech, ParakeetTDT, WhisperTurbo)
- GPU memory management optimization
- Pre-commit hook setup
- Notebook reorganization
- RunPod Instance/Backup -- try-again/Restore loops for runpod (occasionally our spot instances break and we're too poor & budget to restart)

## About

This repository serves as a comprehensive development and testing environment for AI/ML workflows, with a primary focus on **ASR (Automatic Speech Recognition) model evaluation and benchmarking**. The system provides tools for evaluating, comparing, and selecting ASR models for production deployment.

### Core Focus: ASR Model Evaluation
The primary objective is building a robust evaluation framework for "hearing" systems - testing ASR models for production readiness across various real-world scenarios, audio conditions, and performance requirements.

### Key Services and Libraries:
- **ASR Models**: FasterWhisper, OLMoASR, OpenAI Whisper (via OpenRouter)
- **Evaluation Metrics**: WER, CER, BLEU scores, processing time analysis
- **Storage**: PostgreSQL with pgvector for results and leaderboards
- **Infrastructure**: Docker containers with CUDA support
- **Cloud Services**: RunPod GPU instances, OpenRouter API access
- **Development**: JupyterLab environment with VS Code integration

## Development Environment Setup

This project uses a containerized development environment with JupyterLab and PostgreSQL with pgvector extension. The containerized approach eliminates system package conflicts and ensures reproducible development across different machines and operating systems.

### Prerequisites

- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Install [Visual Studio Code](https://code.visualstudio.com/) (recommended)
- Install the [VS Code Remote Development extension pack](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)

### Method 1: VS Code Dev Container (Recommended)

Docker DevContainers provide the optimal development experience by avoiding conflicts with system packages and ensuring complete reproducibility across different environments. This approach offers full IDE integration with isolated dependencies:

1. **Clone and setup environment**:
   ```bash
   git clone <your-repo-url>
   cd <project-directory>
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

2. **Open in VS Code Dev Container**:
   - Open the project folder in VS Code
   - VS Code will detect the dev container configuration
   - Click "Reopen in Container" when prompted, or use Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) → **"Dev Containers: Reopen in Container"**
   - VS Code will automatically build and start all services

3. **Access services**:
   - **Terminal**: Use VS Code's integrated terminal (already inside container)
   - **JupyterLab**: Available at `http://localhost:8888` (token auto-configured)
   - **PostgreSQL**: Available at `localhost:5432`

### Method 2: Docker Compose (Manual)

For users who prefer command-line workflow or cannot use VS Code DevContainers. While functional, this method requires more manual container management:

1. **Clone and setup environment**:
   ```bash
   git clone <your-repo-url>
   cd <project-directory>
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

2. **Start the development environment**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   The script will:
   - Build and start all Docker services
   - Display the JupyterLab URL with access token
   - Show helpful commands for management

3. **Access the container shell**:
   ```bash
   # Get container shell for running Python scripts
   docker compose exec jupyterlab bash
   
   # Or use the container ID directly
   docker exec -it $(docker compose ps -q jupyterlab) bash
   ```

### Project Structure

```
jupyter/
├── .devcontainer/            # VS Code dev container configuration
├── .kiro/                    # Kiro AI assistant specs and configurations
│   └── specs/asr-model-evaluation-system/  # ASR evaluation spec
├── asr_evaluation/           # Core ASR evaluation framework
│   ├── adapters/            # Model adapters (FasterWhisper, OLMoASR)
│   ├── core/                # Interfaces and configuration
│   ├── metrics/             # Evaluation metrics calculation
│   ├── storage/             # PostgreSQL integration
│   └── utils/               # Utility functions
├── tests/                   # Comprehensive test suite
├── transcriptions/          # Evaluation datasets (Vaporeon copypasta)
├── notebooks/               # Jupyter notebooks (git tracked)
├── docker-compose.yml       # Multi-service container setup
├── start.sh                # Development environment setup
├── asr_leaderboard.py      # Main leaderboard generation script
└── README.md
```

### Services

- **JupyterLab**: Available at `http://localhost:8888` (token provided by start.sh)
- **PostgreSQL + pgvector**: Available at `localhost:5432`
  - Database: `jupyter-dev`
  - User: `postgres`
  - Password: `password` (change in production)

### Development Workflow

#### VS Code Dev Container Users
- **Terminal**: Use VS Code's integrated terminal (automatically inside container as `jovyan` user)
- **Python Scripts**: Run directly from terminal: `python asr_leaderboard.py`
- **Jupyter Notebooks**: Create in `notebooks/` directory, accessible via VS Code or browser
- **File Editing**: Full VS Code experience with extensions and IntelliSense

#### Docker Compose Users
```bash
# Access container shell
docker compose exec jupyterlab bash

# Run Python scripts inside container
docker exec -it $(docker compose ps -q jupyterlab) python /home/jovyan/workspaces/asr_leaderboard.py

# View logs
docker compose logs -f

# Stop services
docker compose down

# Restart services
docker compose restart
```

#### Common Commands (Both Methods)
```bash
# Inside container (as jovyan user):
whoami                    # Should show: jovyan
pwd                      # Should show: /home/jovyan/workspaces
python asr_leaderboard.py # Run ASR evaluation
python run_tests.py      # Run test suite
jupyter lab --ip=0.0.0.0 # Start JupyterLab (if not running)
```

### Git Integration

Notebooks created in the `notebooks/` directory are automatically available on your host machine and can be committed to git normally. This allows for proper version control of your work.

## ASR Evaluation Quick Start

### Running the Leaderboard System

#### VS Code Dev Container Method
1. **Open project in VS Code Dev Container** (see setup above)
2. **Use integrated terminal** to run commands directly:
   ```bash
   python asr_leaderboard.py
   ```

#### Docker Compose Method
1. **Start the development environment**:
   ```bash
   ./start.sh
   ```

2. **Run ASR model evaluation**:
   ```bash
   # Method 1: Exec into container
   docker compose exec jupyterlab bash
   python asr_leaderboard.py
   
   # Method 2: Direct execution
   docker exec -it $(docker compose ps -q jupyterlab) python /home/jovyan/workspaces/asr_leaderboard.py
   ```

3. **View results**:
   - Console output shows real-time evaluation progress
   - Results saved to `results/transcriptions/` directory
   - Database leaderboard accessible via PostgreSQL

### Testing Individual Models

#### VS Code Dev Container
```bash
# In VS Code integrated terminal:
python test_olmoasr.py      # Test OLMoASR adapter
python run_tests.py         # Run comprehensive test suite
```

#### Docker Compose
```bash
# Access container shell first
docker compose exec jupyterlab bash

# Then run tests
python test_olmoasr.py      # Test OLMoASR adapter
python run_tests.py         # Run comprehensive test suite
```

### Current Evaluation Dataset

The system includes the **Vaporeon Copypasta Dataset** for initial testing:
- 164 seconds of clear English speech
- Known reference transcription for WER/CER calculation
- Challenging content with internet meme terminology
- Located in `transcriptions/` directory

### Model Performance (Latest Results)

| Model | WER | Processing Time | Status |
|-------|-----|----------------|---------|
| faster-whisper-base | ~15-25% | ~2-3s | Working |
| faster-whisper-small | ~20-30% | ~1-2s | Working |
| hf-whisper-base | ~15-25% | ~3-4s | Working |
| hf-whisper-tiny | ~40-50% | ~0.7s | Working (limited accuracy) |

*Results may vary based on hardware and model availability*