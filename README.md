**G**NGforms is **N**ot **G**oogle forms

We have built this software with the hope it will be used by our neighbours, friends, and anyone else who feels GAFAM already has way to much data on **all** of use.

Don't feed the Dictator!

Please read INSTALL.txt for installation instructions.

## Something about GNGforms.

One installation (one instance running on your server), can be used for many domains. An nginx proxy in front of GNGforms can route as many domains as you wish to the gunicorn running process.

One installation, one database, one monitoring and one backup system, means less work for sysadmins.

## Config

SMTP_SERVER expects a running server that accepts connection without credentials. This need to be improved.

ROOT_USERS a list of emails. Users with these emails are automatically made Root Users.

## Users

Each domain used with GNGforms has an independent user database.

### User profiles

* Anonymous users: Can fill our forms
* Normal registered user: Can create and publish forms. Can download form data
* Admins: Can enable and disable users. Can see all forms, but not form data. Admis can also decide if new users can be created by any anonymous user, or if new users must be 'invited' by the administrators. (invite only).
* Root users: Special users created by the sysadmin. Root users can see all users and forms in the database, regardless of the domain.

## Bootstrapping users
1. From the index page, choose 'Forgot your password?' link.
2. Enter an email defined as a root_user in the config
3. Fill out the new user form.

 

