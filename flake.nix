{

  # This file is adapted from https://github.com/ngi-nix/vulnerablecode/blob/main/etc/nix/flake.nix

  description =
    "Liberaforms — An open source form server";

  inputs.nixpkgs = {
    type = "github";
    owner = "NixOS";
    repo = "nixpkgs";
    ref = "nixos-unstable";
  };

  inputs.machnix = {
    type = "github";
    owner = "DavHau";
    repo = "mach-nix";
    ref = "3.3.0";
  };

  outputs = { self, nixpkgs, machnix }:
    let

      liberaforms-src = ./.;

      # Extract version from VERSION.txt.
      remove-newline = string: builtins.replaceStrings [ "\n" ] [ "" ] string;
      version = remove-newline (builtins.readFile (liberaforms-src + "/VERSION.txt"));

      # Common shell code.
      # libSh = ./lib.sh;

      # System types to support.
      supportedSystems = [ "x86_64-linux" ];

      # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
      forAllSystems = f:
        nixpkgs.lib.genAttrs supportedSystems (system: f system);

      # Nixpkgs instantiated for supported system types.
      nixpkgsFor = forAllSystems (system:
        import nixpkgs {
          inherit system;
          overlays = [ self.overlay ];
        });

      # mach-nix instantiated for supported system types.
      machnixFor = forAllSystems (system:
        import machnix {
          pkgs = (nixpkgsFor.${system}).pkgs;
          python = "python38";

          # Pin pypi repo to a specific commit which includes all necessary
          # Python deps. The default version is updated with every mach-nix
          # release might be be sufficient for newer releases.
          # The corresponding sha256 hash can be obtained with:
          # $ nix-prefetch-url --unpack https://github.com/DavHau/pypi-deps-db/tarball/<pypiDataRev>
          # pypiDataRev = "c86b4490a7d838bd54a2d82730455e96c6e4eb14";
          # pypiDataSha256 =
          #  "0al490gi0qda1nkb9289z2msgpc633rv5hn3w5qihkl1rh88dmjd";
        });

    in
    {
      # A Nixpkgs overlay.
      overlay = final: prev:
        with final.pkgs; {

          # Adding cffi to the requirements list was necessary for the cryptography package to build properly.
          # The cryptography build also gave a similar warning about the "packaging" package so I added it as well.
          pythonEnv = machnixFor.${system}.mkPython {
            requirements = builtins.readFile (liberaforms-src + "/requirements.txt") + "\ncffi>=1.14.5" + "\npackaging>=20.9";
          };

          liberaforms = stdenv.mkDerivation {
            inherit version;
            name = "liberaforms-${version}";
            src = liberaforms-src;
            dontConfigure = true; # do not use ./configure
            propagatedBuildInputs = [ pythonEnv ];

            postPatch = ''
              # Make sure the pycodestyle binary in $PATH is used.
              # substituteInPlace tests/functional/*.py \
              #  --replace 'join(bin_dir, "pycodestyle")' '"pycodestyle"'
            '';

            installPhase = ''
              cp -r . $out
            '';
          };

        };

      # Provide a nix-shell env to work with liberaforms.
      devShell = forAllSystems (system:
        with nixpkgsFor.${system};
        mkShell {
          # will be available as env var in `nix develop` / `nix-shell`.
          LIBERAFORMS_INSTALL_DIR = liberaforms;
          buildInputs = [ liberaforms ];
          #shellHook = ''
          #  alias vulnerablecode-manage.py=${vulnerablecode}/manage.py
          #'';
        });

      # Provide some packages for selected system types.
      packages = forAllSystems
        (system: { inherit (nixpkgsFor.${system}) liberaforms; });

      # The default package for 'nix build'.
      defaultPackage =
        forAllSystems (system: self.packages.${system}.liberaforms);

      nixosConfigurations.container = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules =
          [
            ({ pkgs, ... }: {

              imports = [ ./nix/module.nix ];

              boot.isContainer = true;

              # Let 'nixos-version --json' know about the Git revisiof this flake.
              system.configurationRevision = nixpkgs.lib.mkIf (self ? rev) self.rev;

              nixpkgs.overlays = [ self.overlay ];
              environment.systemPackages = [ pkgs.liberaforms ];

              services.liberaforms = {
                enable = true;
                rootEmail = "cleeyv@riseup.net";
                secretKeyFile = "/home/cleeyv/dev/keys/liberaforms-secret.key";
                dbPasswordFile = "/home/cleeyv/dev/keys/liberaforms-db-password.key";
              };
            })
          ];

        #nixosModule = self.nixosModules.liberaforms;
        #
        #nixosModules =
        #  {
        #    liberaforms = import /home/cleeyv/dev/liberaforms/nix/module.nix;
        #  };



        # nixosModules.liberaforms = import ./nix/module.nix self.overlay;



        # For now I'm using a postgres.nix in my system-wide NixOS config.
        # A NixOS module.
        #nixosModules.liberaforms =
        #  { pkgs, ... }:
        #  {
        #    nixpkgs.overlays = [ self.overlay ];

        #    services.postgresql.enable = true;
        #    services.postgresql.package = pkgs.postgresql_11;
        #  };

        # Tests run by 'nix flake check' and by Hydra.
        #      checks = forAllSystems
        #        (system: {
        #          inherit (self.packages.${system}) liberaforms;
        #
        #  liberaforms-test = with nixpkgsFor.${system};
        #    stdenv.mkDerivation {
        #      name = "${liberaforms.name}-test";
        #
        #      buildInputs = [ wget liberaforms ];
        #
        #      # Used by pygit2.
        #      # See https://github.com/NixOS/nixpkgs/pull/72544#issuecomment-582674047.
        #      SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
        #
        #      unpackPhase = "true";
        #
        #      buildPhase = ''
        #        source ${libSh}
        #        initPostgres $(pwd)
        #        export DJANGO_DEV=1
        #        ${vulnerablecode}/manage.py migrate
        #      '';
        #
        #      doCheck = true;
        #      checkPhase = ''
        #        # Run pytest on the installed version. A running postgres
        #        # database server is needed.
        #        (cd ${vulnerablecode} && pytest)
        #
        #         # Launch the webserver and call the API.
        #         ${vulnerablecode}/manage.py runserver &
        #        sleep 2
        #        wget http://127.0.0.1:8000/api/
        #        kill %1 # kill background task (i.e. webserver)
        #      '';
        #
        #        installPhase =
        #        "mkdir -p $out"; # make this derivation return success
        #    };
        #});
      };
    };
}
