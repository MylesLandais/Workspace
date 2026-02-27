{ pkgs, ... }:

let
  python-pkgs = pkgs.python311.withPackages (ps: with ps; [
    # Core dependencies
    google-genai
    google-adk
    litellm
    typing-extensions
    pydantic-core
    requests
    python-dotenv
    pillow
    numpy
    pandas
    neo4j
    redis
    minio
    boto3
    beautifulsoup4
    feedparser

    # Additional HTTP/API
    aiohttp

    # IMDB
    cinemagoer

    # Image processing
    imagehash
    pytesseract
    insightface # Note: May require manual Nix overlay if standard is not available

    # Async
    asyncio-mqtt

    # Data Science / ML
    pyarrow
    sentence-transformers
    onnxruntime # Using non-GPU version for portability
    onnx
    huggingface-hub
    timm
    matplotlib
    seaborn

    # Web/API
    fastapi
    uvicorn
    pydantic-settings
    python-multipart # For uvicorn[standard]

    # Crawler / Data Engineering
    pybloom-live
    mysql-connector-python
    polars
    tenacity

    # Task Scheduler (Celery + PostgreSQL)
    celery
    flower
    psycopg2
    python-dateutil
    typer
    tabulate

    # Development / Testing
    pytest
    pytest-asyncio

    # Jupyter
    jupyterlab
    notebook
    # Prompt Building
    pyyaml
    jinja2
  ]);
in
{
  # Explicitly set the Python interpreter for the shell
  languages.python.enable = true;
  languages.python.version = "3.11"; 

  # Essential system packages
  packages = [
    pkgs.git
    pkgs.make
    pkgs.docker-compose # Using docker compose (with space) as per environment
    pkgs.nodejs
    pkgs.tesseract
    pkgs.pkg-config
    pkgs.opencv-python
    pkgs.yt-dlp
    pkgs.ffmpeg
    pkgs.libsndfile
    pkgs.sox

    # Database systems
    pkgs.postgresql_16  # PostgreSQL for task scheduler

    # Python environment
    python-pkgs

    # Add uv for Python dependency management
    pkgs.uv
  ];

  # Commands to run on entering the shell
  enterShell = ''
    # CUDA driver + libstdc++ for PyTorch cu128 wheels on NixOS
    export LD_LIBRARY_PATH="/run/opengl-driver/lib:${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
    export TORCH_CUDA_ARCH_LIST="8.6"

    echo "========================================================================"
    echo "Welcome to jupyter-workspace Nix development environment!"
    echo "========================================================================"
    echo ""
    echo "CUDA Environment:"
    echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'Not detected')"
    echo "  Driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null || echo 'N/A')"
    echo ""
    echo "Versions:"
    echo "  Python: $(python --version)"
    echo "  Node: $(node --version)"
    echo "  uv: $(uv --version)"
    echo "  PostgreSQL: $(postgres --version)"
    echo ""
    echo "Services:"
    echo "  JupyterLab: http://localhost:8888"
    echo "  PostgreSQL: localhost:5432"
    echo "  Task Scheduler: See docker-compose.yml for Celery services"
    echo ""
    echo "Quick start:"
    echo "  1. docker compose up -d  # Start Docker services (Neo4j, Redis, MinIO, etc.)"
    echo "  2. uv sync               # Install Python dependencies"
    echo "  3. psql -U scheduler -d feed_scheduler -h localhost  # Connect to PostgreSQL"
    echo ""
    echo "TTS Evaluation:"
    echo "  LD_LIBRARY_PATH is set for CUDA"
    echo "  Run: uv run src/tts/eval_loop.py"
    echo ""
    echo "========================================================================"
  '';

  # Services managed by devenv
  services.jupyterlab = {
    enable = true;
    port = 8888;
    # Uses the command from your Dockerfile to run JupyterLab
    command = "${pkgs.python311}/bin/jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''";
  };

  # PostgreSQL development service (optional, can also use Docker)
  # Uncomment to run PostgreSQL in devenv instead of Docker
  # services.postgres = {
  #   enable = true;
  #   package = pkgs.postgresql_16;
  #   port = 5432;
  #   initdbArgs = "--encoding=UTF8";
  #   settings = {
  #     port = 5432;
  #     max_connections = 100;
  #   };
  # };
}

