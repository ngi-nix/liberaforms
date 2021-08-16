{ config, lib, pkgs, ... }:

with lib;
let
  gunicorn = pkgs.python3Packages.gunicorn;
  liberaforms = pkgs.liberaforms;
  flask = pkgs.python3Packages.flask;
  python = pkgs.python3Packages.python;
  cfg = config.services.liberaforms;
  user = "liberaforms";
  group = "liberaforms";
  default_home = "/var/lib/liberaforms";
  default_logs = "var/log/liberaforms";
in
{

  options.services.liberaforms = with types; {
    enable = mkEnableOption "LiberaForms server";

    rootEmail = mkOption {
      type = types.str;
      description = ''
        Email address used for root user of LiberaForms.
      '';
      example = "admin@example.org";
      default = "";
    };

    defaultLang = mkOption {
      type = types.str;
      description = ''
        Default language of LiberaForms.
      '';
      example = "fr";
      default = "en";
    };

    dbHost = mkOption {
      type = types.str;
      description = ''
        Hostname of postgres database.
      '';
      example = "";
      default = "localhost";
    };

    bind = mkOption {
      type = types.str;
      description = ''
        Bind address to be used by gunicorn.
      '';
      example = "0.0.0.0:5000";
      default = "127.0.0.1:5000";
    };

    #Not configured anywhere...
    #    uploadsDir = mkOption {
    #      type = types.str;
    #      description = ''
    #        Path to the directory where the uploads will be saved to
    #      '';
    #      default = default_home + "/uploads";
    #    };

    extraConfig = mkOption {
      type = types.lines;
      description = ''
        Extra configuration for LiberaForms to be appended on the
        configuration.
        see https://gitlab.com/liberaforms/liberaforms/-/blob/develop/dotenv.example 
        for all options.
      '';
      default = "";
      example = ''
        ENABLE_REMOTE_STORAGE=True
        MAX_MEDIA_SIZE=512000
      '';
    };

    secretKey = mkOption {
      type = types.str;
      description = ''
        server secret for safe session cookies, must be set.
        Created with `openssl rand -base64 32`.
        Warning: this secret is stored in the WORLD-READABLE Nix store!
        It's recommended to use <option>secretKeyFile</option>
        which takes precedence over <option>secretKey</option>.
      '';
      default = "";
    };

    secretKeyFile = mkOption {
      # type = types.nullOr types.str;
      type = types.str;
      default = ""; # null
      description = ''
        A file that contains the server secret for safe session cookies, must be set.
        Created with `openssl rand -base64 32`.
        <option>secretKeyFile</option> takes precedence over <option>secretKey</option>.
        Warning: when <option>secretKey</option> is non-empty <option>secretKeyFile</option>
        defaults to a file in the WORLD-READABLE Nix store containing that secret.
      '';
    };

    dbPasswordFile = mkOption {
      type = types.str;
      default = "";
      description = ''    
        A file that contains a password for the liberaforms user in postgres, must be set.
        Use a strong password.
      '';
    };

    cryptoKeyFile = mkOption {
      type = types.str;
      default = "";
      description = ''    
        A file that contains a key to encrypt files uploaded to liberaforms.
        Key is generated after initial install using `flask cryptokey create`.
      '';
    };

    sessionType = mkOption {
      type = types.str;
      description = ''
        Session management backend (see docs/INSTALL).
      '';
      example = "memcached";
      default = "filesystem";
    };

    workDir = mkOption {
      type = types.str;
      description = ''
        Path to the working directory (used for config and pidfile).
      '';
      default = default_home;
    };

    workers = mkOption {
      type = types.int;
      default = 3;
      example = 10;
      description = ''
        The number of gunicorn worker processes for handling requests.
      '';
    };

    #config = {
    #  secretKeyFile = mkDefault (
    #    if config.secretKey != ""
    #    then
    #      toString
    #        (pkgs.writeTextFile {
    #          name = "liberaforms-secret-key";
    #          text = config.secretKey;
    #        })
    #    else null
    #  );
    #};
  };

  config = mkIf cfg.enable {

    systemd.services.liberaforms = {
      description = "LiberaForms server";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" "postgresql.service" ];
      restartIfChanged = true;

      environment =
        let
          penv = python.buildEnv.override {
            extraLibs = [ pkgs.liberaforms ];
          };
        in
        {
          # LIBERAFORMS_CONFIG = "${workDir}/.env";
          PYTHONPATH = "${penv}/${python.sitePackages}/";
        };

      serviceConfig = {
        Type = "simple";
        PrivateTmp = true;
        ExecStartPre = pkgs.writeScript "liberaforms-init" ''
          #!/bin/sh
          mkdir -p "${cfg.workDir}"
          mkdir -p "${default_logs}"
          chown ${user}:${group} "${cfg.workDir}" "${default_logs}"
          cat > ${cfg.workDir}/.env <<EOF
          # Do not edit this file, it is automatically generated by liberaforms.service

          SECRET_KEY="$(cat "${cfg.secretKeyFile}")"
          
          ROOT_USERS = ['${cfg.rootEmail}']
          DEFAULT_LANGUAGE = '${cfg.defaultLang}'
          TMP_DIR = '/tmp'
          
          ## Database
          DB_HOST=${cfg.dbHost}
          DB_NAME=liberaforms
          DB_USER=liberaforms
          DB_PASSWORD="$(cat "${cfg.dbPasswordFile}")"

          # Maximum valid age for password resets, invitations, ..
          # 86400 seconds = 24h
          TOKEN_EXPIRATION = 604800

          CRYPTO_KEY=$(cat "${cfg.cryptoKeyFile}")

          # Session management (see docs/INSTALL)
          SESSION_TYPE="$cfg.{sessionType}"

          # Directory where logs will be saved
          LOG_DIR=${default_logs}

          # see assets/timezones.txt for valid options
          DEFAULT_TIMEZONE="${config.time.timeZone}"

          # LiberaForms on NixOS can currently only be run in production mode
          # See issue for more details: TODO

          # FLASK_ENV
          # this sets the Flask running mode
          # can be 'production' or 'development'
          FLASK_ENV=production

          # FLASK_CONFIG
          # this sets the config to use (see config.py)
          # can be 'production' or 'development'
          FLASK_CONFIG=production

          # To enable these options, use services.liberforms.extraConfig
          # See docs/upload.md for more info
          # ENABLE_UPLOADS=True
          # ENABLE_REMOTE_STORAGE=False
          # 1024 * 500 = 512000 = 500 KiB
          # MAX_MEDIA_SIZE=512000
          # 1024 * 1024 * 1.5 = 1572864 = 1.5 MiB
          # MAX_ATTACHMENT_SIZE=1572864
           
          ${extraConfig}
          EOF
          cat > ${cfg.workDir}/gunicorn.py <<EOF
          # Do not edit this file, it is automatically generated by liberaforms.service
          from dotenv import load_dotenv
          load_dotenv(dotenv_path=".env")
          pythonpath = '${cg.workDir}'
          command = '${gunicorn}/bin/gunicorn'
          bind = '${cfg.bind}'
          workers = ${workers}
          user = '${user}'
          EOF
        '';
        ExecStart = ''${gunicorn}/bin/gunicorn \
              -c ${cfg.workDir}/gunicorn.py 'wsgi:create_app()'
            '';
        ExecReload = "${pkgs.coreutils}/bin/kill -HUP $MAINPID";
        User = "${user}";
        Group = "${group}";
        WorkingDirectory = "${cfg.workDir}";
        KillMode = "mixed";
        TimeoutStopSec = "5";
      };
    };

    #users.users.${user} =
    #  {
    #    uid = config.ids.uids.liberaforms;
    #    group = group;
    #    home = default_home;
    #  };
    #
    #users.groups.${group}.gid = config.ids.gids.liberaforms;
  };
}
