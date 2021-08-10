{ config, pkgs, lib, ... }:
{

  ## Postgres database ##

  services.postgresql.enable = true;
  services.postgresql.package = pkgs.postgresql_11;
  # https://unix.stackexchange.com/questions/378711/how-do-i-configure-postgress-authorization-settings-in-nixos
  services.postgresql.authentication = lib.mkForce ''
    # TYPE  DATABASE        USER            ADDRESS                 METHOD
    local   all             all                                     trust
    host    all             all             127.0.0.1/32            trust
    host    all             all             ::1/128                 trust
  '';


  ## Supervisor process manager ##

  environment.systemPackages = with pkgs; [ python38Packages.supervisor ];

  # From https://github.com/Supervisor/supervisor/blob/master/supervisor/skel/sample.conf
  environment.etc."supervisor/supervisord.conf".source = "/home/cleeyv/dev/liberaforms/nix/supervisord.conf";

  # Based on https://github.com/Supervisor/initscripts/blob/master/centos-systemd-etcs
  systemd.services.supervisor = {
    enable = true;
    description = "supervisord - Supervisor process control system for UNIX";
    after = [ "network.target" ];

    serviceConfig = {
      Type = "forking";
      ExecStart = "/run/current-system/sw/bin/supervisord -c /etc/supervisor/supervisord.conf";
      ExecReload = "/run/current-system/sw/bin/supervisorctl reload";
      ExecStop = "/run/current-system/sw/bin/supervisorctl shutdown";
      Restart = "on-failure";
      RestartSec = "42s";
    };
    wantedBy = [ "multi-user.target" ];
  };


  ## Nginx reverse proxy ##

  # Based on https://gitlab.com/liberaforms/liberaforms/-/blob/main/docs/nginx.example

  networking.extraHosts =
    ''
      127.0.0.1 liberaforms
      127.0.0.1 forms.cleeyv.tech
    '';

  # HTTPS will remain disabled until testing on a public host
  services.nginx.enable = true;
  # security.acme.acceptTerms = true;
  # security.acme.email = "cleeyv@riseup.net";

  services.nginx.virtualHosts."forms.cleeyv.tech" = {
    listen = [{
      addr = "127.0.0.1";
      port = 80;
    }];
    # enableACME = true;
    # forceSSL = true;
    extraConfig = ''
      access_log /var/log/nginx/liberaforms.access.log;
      error_log /var/log/nginx/liberaforms.error.log notice;
    '';
  };

  services.nginx.virtualHosts."forms.cleeyv.tech".locations."/" = {
    # Aliases for static, favicon, logo, emailheader, and media paths could be added here later
    proxyPass = "http://liberaforms:5000";
    extraConfig = ''
      proxy_set_header    Host    $host;
      proxy_set_header    X-Forwarded-For $remote_addr;
      proxy_set_header    X-Real-IP   $remote_addr;
      proxy_pass_header   server;
      proxy_set_header Host $host;
    '';
  };

  # Send nginx error and access logs to journald
  services.nginx.appendHttpConfig = ''
    error_log stderr;
    access_log syslog:server=unix:/dev/log combined;
    types_hash_bucket_size 128; # Clean warning from nginx log
  '';

}
