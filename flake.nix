{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/release-23.11";

    flake-utils.url = "github:numtide/flake-utils";
    
    poetry2nixFlake.url = "github:nix-community/poetry2nix";
    poetry2nixFlake.inputs.nixpkgs.follows = "nixpkgs";
    poetry2nixFlake.inputs.flake-utils.follows = "flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils, poetry2nixFlake }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs { inherit system; };
      poetry2nix = poetry2nixFlake.lib.mkPoetry2Nix { inherit pkgs; };
      poetryEnv = poetry2nix.mkPoetryEnv {
        python = pkgs.python311;
        projectDir = self;
        editablePackageSources = {
          ical_rpt = ./src;
        };
      };
    in {
      apps = {
        default = {
          type = "app";
          program = "${poetryEnv}/bin/ical-rpt";
        };
      };
      devShells = {
        maintenance = pkgs.mkShell {
          buildInputs = [ pkgs.poetry poetry2nix.cli ];
        };
        default = poetryEnv.env.overrideAttrs (oldAttrs: {
          buildInputs = (if oldAttrs ? buildInputs then oldAttrs.buildInputs else []) ++ [
            pkgs.poetry
            poetry2nix.cli
          ];
          shellHook = (if oldAttrs ? shellHook then oldAttrs.shellHook else "") + ''
            export PYTHONPATH=$PWD/src
            for d in ${poetryEnv}/lib/python*/site-packages/; do
              PYTHONPATH=$PYTHONPATH:''${d%/}
            done
          '';
        });
      };
    });
}
