{ config, lib, pkgs, ... }:

with lib;
let
  gunicorn = pkgs.python3Packages.gunicorn;
  dotenv = pkgs.python3Packages.python-dotenv;
  liberaforms = pkgs.liberaforms;
  flask = pkgs.python3Packages.flask;
  python = pkgs.python3Packages.python;
  cfg = config.services.liberaforms;
  user = "liberaforms";
  group = "liberaforms";
  default_home = "/var/lib/liberaforms";
  default_logs = "/var/log/liberaforms";
  penv = pkgs.liberaforms-env;
in
{

  options.services.liberaforms = with types; {
    enable = mkEnableOption "LiberaForms server";

    enablePostgres = mkEnableOption "Postgres database";

    enableNginx = mkEnableOption "Nginx reverse proxy web server";

    enableHTTPS = mkEnableOption "HTTPS for connections to nginx";

    domain = mkOption {
      type = types.str;
      description = ''
        Domain for LiberaForms instance.
      '';
      example = "forms.example.org";
      default = "localhost";
    };


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
      type = types.nullOr types.str;
      # type = types.str;
      default = null;
      description = ''
        A file that contains the server secret for safe session cookies, must be set.
        Created with `openssl rand -base64 32`.
        <option>secretKeyFile</option> takes precedence over <option>secretKey</option>.
        Warning: when <option>secretKey</option> is non-empty <option>secretKeyFile</option>
        defaults to a file in the WORLD-READABLE Nix store containing that secret.
      '';
    };

    dbPasswordFile = mkOption {
      type = types.nullOr types.str;
      default = null;
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

    systemd.tmpfiles.rules =
      [
        "d /var/lib/liberaforms 755 liberaforms"
        "d /var/log/liberaforms 755 liberaforms"
      ];

    systemd.services.liberaforms = {
      description = "LiberaForms server";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" "postgresql.service" ];
      requires = [ "postgresql.service" ];
      restartIfChanged = true;
      path = with pkgs; [ postgresql_11 liberaforms-env ];

      serviceConfig = {
        Type = "simple";
        PrivateTmp = true;
        ExecStartPre = assert cfg.secretKeyFile != null; pkgs.writeScript "liberaforms-init" ''
          #!/bin/sh
          set -x
          mkdir -p ${cfg.workDir}
          cat > ${cfg.workDir}/.env <<EOF
          # Do not edit this file, it is automatically generated by liberaforms.service

          SECRET_KEY="$(cat ${cfg.secretKeyFile})"

          ROOT_USERS = ['${cfg.rootEmail}']
          DEFAULT_LANGUAGE = '${cfg.defaultLang}'
          TMP_DIR = '/tmp'

          ## Database
          DB_HOST=${cfg.dbHost}
          DB_NAME=liberaforms
          DB_USER=liberaforms
          DB_PASSWORD="$(cat ${cfg.dbPasswordFile})"

          # Maximum valid age for password resets, invitations, ..
          # 86400 seconds = 24h
          TOKEN_EXPIRATION = 604800

          CRYPTO_KEY=$(cat "${cfg.cryptoKeyFile}")

          # Session management (see docs/INSTALL)
          SESSION_TYPE="${cfg.sessionType}"

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
          ENABLE_UPLOADS=FALSE
          ENABLE_REMOTE_STORAGE=False
          # 1024 * 500 = 512000 = 500 KiB
          MAX_MEDIA_SIZE=512000
          # 1024 * 1024 * 1.5 = 1572864 = 1.5 MiB
          MAX_ATTACHMENT_SIZE=1572864

          # ENABLE_PROMETHEUS_METRICS
          # this activates Prometheus' /metrics route and metrics generation
          ENABLE_PROMETHEUS_METRICS=False

          ${cfg.extraConfig}
          EOF

          cat > ${cfg.workDir}/gunicorn.py <<EOF
          # Do not edit this file, it is automatically generated by liberaforms.service
          from dotenv import load_dotenv
          load_dotenv(dotenv_path="/var/lib/liberaforms/.env")
          # pythonpath = '${liberaforms}'
          command = '${penv}/bin/gunicorn'
          bind = '${cfg.bind}'
          workers = ${toString cfg.workers}
          user = '${user}'
          EOF

          cd ${cfg.workDir}
          ln -sf ${liberaforms}/* .
          # wsgi.py cannot be symlink because its location determines working dir of gunicorn/flask.
          rm ./wsgi.py
          cp ${liberaforms}/wsgi.py ./wsgi.py
          rm -r ./uploads
          cp -rL ${liberaforms}/uploads .
          chmod -R +w uploads

          # "${cfg.workDir}/liberaforms/commands/postgres.sh create-db"
          # psql commands from create-db script rewritten here to include -U postgres
          psql -U postgres -c "CREATE USER liberaforms WITH PASSWORD '$(cat ${cfg.dbPasswordFile})'"
          psql -U postgres -c "CREATE DATABASE liberaforms ENCODING 'UTF8' TEMPLATE template0"
          psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE liberaforms TO liberaforms"

          flask db upgrade
        '';
        ExecStart = "${penv}/bin/gunicorn -c ${cfg.workDir}/gunicorn.py 'wsgi:create_app()'";
        ExecReload = "${pkgs.coreutils}/bin/kill -HUP $MAINPID";
        User = "${user}";
        #Group = "${group}";
        WorkingDirectory = "${cfg.workDir}";
        KillMode = "mixed";
        TimeoutStopSec = "5";
      };
    };

    users.users.${user} =
      {
        #uid = config.ids.uids.liberaforms;
        #group = group;
        home = default_home;
        isSystemUser = true;
      };
    #users.groups.${group}.gid = config.ids.gids.liberaforms;

    services.postgresql = mkIf cfg.enablePostgres {
      enable = true;
      package = pkgs.postgresql_11;
      authentication = lib.mkForce ''
        # TYPE  DATABASE         USER            ADDRESS          METHOD
        local   postgres         postgres                         trust
        local   liberaforms      liberaforms                      trust
        host    liberaforms      liberaforms     127.0.0.1/32     trust
        host    liberaforms      liberaforms     ::1/128          trust
      '';
    };

    # Based on https://gitlab.com/liberaforms/liberaforms/-/blob/main/docs/nginx.example

    networking.extraHosts =
      ''
        127.0.0.1 liberaforms
      '';

    services.nginx = mkIf cfg.enableNginx {
      enable = true;
      # Send all nginx error and access logs to journald.
      appendHttpConfig = ''
        error_log stderr;
        access_log syslog:server=unix:/dev/log combined;
        types_hash_bucket_size 128; # Clean warning from nginx log
      '';

      virtualHosts."${cfg.domain}" = {
        # Send liberaforms error and access logs to files.
        extraConfig = ''
          access_log /var/log/nginx/liberaforms.access.log;
          error_log /var/log/nginx/liberaforms.error.log notice;
        '';
        locations."/" = {
          # Aliases for static, favicon, logo, emailheader, and media paths could be added here later.
          proxyPass = "http://liberaforms:5000";
          extraConfig = ''
            proxy_set_header    Host    $host;
            proxy_set_header    X-Forwarded-For $remote_addr;
            proxy_set_header    X-Real-IP   $remote_addr;
            proxy_pass_header   server;
            proxy_set_header Host $host;
          '';
        };
        enableACME = mkIf cfg.enableHTTPS true;
        forceSSL = mkIf cfg.enableHTTPS true;
      };
    };
    security.acme = mkIf cfg.enableHTTPS {
      acceptTerms = true;
      email = "${cfg.rootEmail}";
    };
  };
}
