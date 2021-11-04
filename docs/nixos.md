# LiberaForms on NixOS

These instructions are for running a local development instance of LiberaForms in a NixOS container.

For an easy way to deploy a production LiberaForms instance to NixOS on a public cloud VM, see this guide: https://github.com/ngi-nix/deploy-liberaforms

## Clone LiberaForms flake repo from ngi-nix

```
git clone https://github.com/ngi-nix/liberaforms.git
```

## Install Nix with flakes

Add the following to your NixOS configuration to install the nixFlakes version of the nix package manager, with the experimental feature for flakes enabled:
```
nix = {
  package = pkgs.nixFlakes;
  extraOptions = ''
    experimental-features = nix-command flakes
  '';
};
```
And then run `nixos-rebuild switch` to enable the new configuration.
Taken from https://nixos.wiki/wiki/Flakes#System-wide_installation

## Nix flake

The `flake.nix` (along with the nix/module.nix) contains the configuration to run a LiberaForms instance and all of its dependencies and recommended configurations (postgres, nginx, and db backups). For running in a local nixos-container HTTPS is disabled by default, and flask (the python web framework used to create LiberaForms) is running in development mode. All of the required secrets and variables are generated automatically.

## NixOS container

### Create and start

Within the cloned `liberaforms` directory, run the following commands to create and then start the nixos-container
```
sudo nixos-container create liberaforms --flake ./#liberaforms
sudo nixos-container start liberaforms
```
The `create` command will output a local container IP address (such as 10.233.1.2). Once the container is started, visiting this address in a browser on the host system will display the LiberaForms instance where you can then follow the instructions on [bootstrapping a first Admin user](https://gitlab.com/liberaforms/liberaforms/-/tree/develop#bootstrapping-the-first-admin). The default admin email address is `admin@example.org` though this can be easily modified in the `flake.nix`.

### Login

This command can be used to login to a root shell for the container:
```
sudo nixos-container root-login liberaforms
```

### Update

If you make changes to the flake.nix or the nix/module.nix and would like to see them reflected in an already running container, you can use the update command for this purpose:
```
sudo nixos-container update liberaforms --flake ./liberaforms
```

### Stop and destroy

A container that has been started can be stopped, and one that has been created can be destroyed:
```
sudo nixos-container stop liberaforms
sudo nixos-container destroy liberaforms
```

## Tests

The [unit and functional test suite](https://gitlab.com/liberaforms/liberaforms/-/tree/develop/tests) for LiberaForms can be run on NixOS using the command `nix flake check`. In order for this to be possible, email validation of new user accounts for LiberaForms on NixOS is currently disabled, pending a solution to this issue: https://gitlab.com/liberaforms/liberaforms/-/issues/126
