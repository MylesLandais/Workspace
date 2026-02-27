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
