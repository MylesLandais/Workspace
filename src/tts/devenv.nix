{ pkgs, config, ... }:

let
  python-pkgs = pkgs.python311.withPackages (ps: with ps; [
    # TTS / Audio (CPU fallback for testing build)
    (torch.override { cudaSupport = false; })
    torchaudio
    transformers
    soundfile
    accelerate
    bitsandbytes
    numpy
    huggingface-hub

    # Development / Testing
    pytest
  ]);
in
{

  packages = [
    pkgs.git
    pkgs.ffmpeg
    pkgs.libsndfile
    pkgs.sox
    pkgs.pkg-config

    python-pkgs
    pkgs.uv
  ];

  enterShell = ''
    echo "MOSS-TTS development environment"
    echo "  Python: $(python --version)"
    echo "  uv: $(uv --version)"
    echo ""
    echo "Verify CUDA: python -c \"import torch; print(torch.cuda.is_available())\""
    echo "Run test:    python test_moss.py"
  '';
}
