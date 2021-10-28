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
          #pypiDataRev = "c86b4490a7d838bd54a2d82730455e96c6e4eb14";
          #pypiDataSha256 = "0al490gi0qda1nkb9289z2msgpc633rv5hn3w5qihkl1rh88dmjd";
        });

    in
    {
      # A Nixpkgs overlay.
      overlay = final: prev:
        with final.pkgs; {

          # Adding cffi to the requirements list was necessary for the cryptography package to build properly.
          # The cryptography build also gave a similar warning about the "packaging" package so I added it as well.
          liberaforms-env = machnixFor.${system}.mkPython {
            requirements = builtins.readFile (liberaforms-src + "/requirements.txt") + "\ncffi>=1.14.5" + "\npackaging>=20.9" + "\npytest-dotenv>=0.5.2";
          };

          liberaforms = stdenv.mkDerivation {
            inherit version;
            name = "liberaforms-${version}";
            src = liberaforms-src;
            dontConfigure = true; # do not use ./configure
            propagatedBuildInputs = [ liberaforms-env python38Packages.flask_migrate ];

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
                  enableTests = true;
                  rootEmail = "cleeyv@riseup.net";
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

              buildInputs = [ liberaforms ];

              buildPhase = ''
              '';

              doCheck = true;
              checkPhase = ''
                # Run pytest on the installed version. A running postgres
                # database server is needed.
                # TODO: figure out location pytest run can at build/check time, with custom test.ini
                (cd .../tests && pytest)
              '';

              installPhase =
                "mkdir -p $out"; # make this derivation return success
            };
        });
    };
}
