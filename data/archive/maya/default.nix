{
  lib,
  pkgs,
}:

let
  version = "0.1.0";
  inherit (pkgs) buildGoModule dockerTools;
  maya = buildGoModule {
    pname = "maya";
    inherit version;

    src = ./.;

    vendorHash = null;

    meta = {
      homepage = "https://github.com/System-Nebula/maya";
      description = "Discord bot with streaming capabilities";
    };
  };
  containerImage = dockerTools.buildLayeredImage {
    name = "maya";
    tag = version;
    contents = [
      pkgs.cacert
      pkgs.openssl
    ];
    config = {
      Cmd = [ "${maya}/bin/maya" ];
    };
  };
in
{
  inherit maya containerImage;
}
