{
  pkgs ? import <nixpkgs> { },
  config,
}:
let
  all_custom_packages = [
    container_build
    go_test
  ];
  container_build = pkgs.writeShellApplication {
    name = "container_build";
    text = ''
      nix build .#containerImage
    '';
    meta = {
      description = "Build the Docker container image using Nix";
    };
  };
  go_test = pkgs.writeShellApplication {
    name = "go_test";
    text = ''
      go test -v ./...
    '';
    meta = {
      description = "Run Go tests with verbose output";
    };
  };

  packageInfo = map (pkg: "${pkg.name}: ${pkg.meta.description}") all_custom_packages;

  devhelp = pkgs.writeScriptBin "devhelp" ''
    echo "The following subcommands are available through this shell:"
    ${pkgs.lib.concatStringsSep "\n" (map (info: "echo \"${info}\"") packageInfo)}
    echo "devhelp: runs this command"
  '';
in
pkgs.mkShell {
  shellHook = ''
    ${config.pre-commit.shellHook}
    devhelp
  '';
  packages = config.pre-commit.settings.enabledPackages;
  buildInputs = [
    pkgs.go
    pkgs.statix
    pkgs.golangci-lint
    devhelp
  ]
  ++ all_custom_packages;
}
