{
  description = "Maya flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    git-hooks.url = "github:cachix/git-hooks.nix";
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-parts,
      git-hooks,
      ...
    }@inputs:
    let
      system = builtins.currentSystem;
      pkgs = import nixpkgs {
        inherit system;
      };
    in
    flake-parts.lib.mkFlake
      {
        inherit inputs;
      }
      {
        imports = [
          inputs.git-hooks.flakeModule
        ];
        systems = [
          "x86_64-linux"
          "aarch64-linux"
          "x86_64-darwin"
          "aarch64-darwin"
        ];
        perSystem =
          {
            system,
            inputs',
            config,
            pkgs,
            lib,
            ...
          }:
          {
            pre-commit.settings.hooks = {
              gofmt.enable = true;
              golangci-lint.enable = true;
              statix.enable = true;
            };
            packages =
              let
                packages = pkgs.callPackage ./default.nix { inherit lib pkgs; };
              in
              {
                default = packages.maya;
                inherit (packages) containerImage maya;
              };
            devShells.default = import ./shell.nix { inherit pkgs config; };
          };
      };

}
