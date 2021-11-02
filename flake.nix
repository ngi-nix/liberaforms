{
  description =
    "Liberaforms — An open source form server";

  inputs.nixpkgs = {
    type = "github";
    owner = "cleeyv";
    repo = "nixpkgs";
    ref = "pytest-dotenv";
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

      # Postgres setup script for tests.
      initPostgres = ./nix/initPostgres.sh;

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

          # The default version of the pypi dependencies db that is updated with every mach-nix release
          # might not be sufficient for newer releases of liberaforms. Edit here to pin to specific commit.
          # The corresponding sha256 hash can be obtained with:
          # $ nix-prefetch-url --unpack https://github.com/DavHau/pypi-deps-db/tarball/<pypiDataRev>
          pypiDataRev = "020c5fbad4b0a6a9317646ed377631123730031c";
          pypiDataSha256 = "14a0b5gn3rhd10yhg7a5m3mx9ans1v105iy0xdxik8v4zyjw3hmd";
        });

    in
    {
      # A Nixpkgs overlay.
      overlay = final: prev:
        with final.pkgs; {

          # Adding cffi to the requirements list was necessary for the cryptography package to build properly.
          # The cryptography build also logged a message about the "packaging" package so it was added as well.
          liberaforms-env = machnixFor.${system}.mkPython {
            requirements = builtins.readFile (liberaforms-src + "/requirements.txt")+ "\ncffi>=1.14.5" + "\npackaging>=20.9";
          };

          liberaforms = stdenv.mkDerivation {
            inherit version;
            name = "liberaforms-${version}";
            src = liberaforms-src;
            dontConfigure = true; # do not use ./configure
            propagatedBuildInputs = [ liberaforms-env python38Packages.flask_migrate postgresql ];

            installPhase = ''
              cp -r . $out
            '';
          };
        };

      # Provide a nix-shell env to work with liberaforms.
      devShell = forAllSystems (system:
        with nixpkgsFor.${system};
        mkShell {
          buildInputs = [ liberaforms ];
        });

      # Provide some packages for selected system types.
      packages = forAllSystems
        (system: { inherit (nixpkgsFor.${system}) liberaforms; });

      # The default package for 'nix build'.
      defaultPackage =
        forAllSystems (system: self.packages.${system}.liberaforms);

      nixosConfigurations.liberaforms = nixpkgs.lib.nixosSystem
        {
          system = "x86_64-linux";
          modules =
            [
              ({ pkgs, lib, ... }: {

                imports = [ ./nix/module.nix ];

                boot.isContainer = true;
                networking.useDHCP = false;

                networking.hostName = "liberaforms";

                # A timezone must be specified for use in the LiberaForms config file
                time.timeZone = "America/Montreal";

                services.liberaforms = {
                  enable = true;
                  enablePostgres = true;
                  enableNginx = true;
                  #enableHTTPS = true;
                  #domain = "forms.example.org";
                  enableDatabaseBackup = true;
                  rootEmail = "ADMIN@EXAMPLE.ORG";
                };

                # Let 'nixos-version --json' know about the Git revision of this flake.
                system.configurationRevision = nixpkgs.lib.mkIf (self ? rev) self.rev;

                nixpkgs.overlays = [ self.overlay ];

              })
            ];
        };

      # Tests run by 'nix flake check' and by Hydra.
      checks = forAllSystems
        (system: {
          inherit (self.packages.${system}) liberaforms;
          liberaforms-test = with nixpkgsFor.${system};
            stdenv.mkDerivation {
              name = "${liberaforms.name}-test";

              src = liberaforms-src;

              buildInputs = [ liberaforms ];

              buildPhase = ''
                source ${initPostgres}
                initPostgres $(pwd)
              '';

              doCheck = true;

              checkInputs = with pkgs.python38Packages; [ pytest pytest-dotenv];

              checkPhase = ''
                # Run pytest on the installed version. A running postgres database server is needed.
                (cd tests && cp test.ini.example test.ini && pytest)
              '';

              installPhase =
                "mkdir -p $out"; # make this derivation return success
            };
        });
    };
}
