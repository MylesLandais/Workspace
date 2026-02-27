{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.git
    pkgs.gnumake
    pkgs.postgresql_16
    pkgs.docker-compose
    pkgs.nodejs
    pkgs.uv
    pkgs.libsndfile
    pkgs.sox
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.ffmpeg
    pkgs.awscli2
    pkgs.yt-dlp
    pkgs.ripgrep  # for Maya memory_recall
  ];

  shellHook = ''
    export LD_LIBRARY_PATH=/run/opengl-driver/lib:${pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.libsndfile
      pkgs.sox
      pkgs.cudaPackages.cudatoolkit
    ]}:$LD_LIBRARY_PATH
    
    echo "========================================================================"
    echo "Nix shell with LD_LIBRARY_PATH configured for ML dependencies."
    echo "========================================================================"
  '';
}
