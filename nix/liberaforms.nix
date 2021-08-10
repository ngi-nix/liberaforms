{ pkgs, lib, ... }:
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

  systemd.services.supervisor = {
    enable = true;
    description = "supervisord - Supervisor process control system for UNIX";
    after = [ "network.target" ];

    serviceConfig = {
      Type = "forking";
      # Unclear where supervisord.conf should be located.
      ExecStart = "/run/current-system/sw/bin/supervisord -c /etc/supervisor/supervisord.conf";
      ExecReload = "/run/current-system/sw/bin/supervisord reload";
      ExecStop = "/run/current-system/sw/bin/supervisord shutdown";
    };
    # Added so that the service will start automatically.
    # Possibly also add a "Restart" to the serviceConfig if it doesn't recover from failures.
    wantedBy = [ "multi-user.target" ];
  };


  ## Nginx reverse proxy ##


}
