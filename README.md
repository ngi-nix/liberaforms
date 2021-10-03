# Libera forms

Project page [https://liberaforms.org](https://liberaforms.org)

At the center of LiberaForms is the WYSIWYG web form builder [formbuilder](https://formbuilder.online/). Users build a form, choose a URL slug, and publish it.

## Install

Please read `./docs/INSTALL.md`


## User profiles
**Anonymous users**:
 * Can fill out published forms

**Normal registered users:**
 * Can create and publish forms.
 * Can edit collected data on the web interface
 * Download collected form data in CSV
 * Share edit permission with other users on the site
 * Set some basic expiry conditions.
 * And other stuff

**Admins:**
 * Edit frontpage text
 * Invite new users to the site
 * Enable and disable users.
 * Give/remove admin permissions to users
 * Read all forms
 * Delete users and their forms
 * Site configuration. Invite only, Data protection text, smtp config, etc.
 * Admins **cannot** read collected data of other users' forms

## Bootstrapping the first Admin
1. From the index page, choose 'Forgot your password?' link.
2. Enter an email defined as a root_user in the `.env`
3. Fill out the new user form.
4. Go to the configuration page and get the **SMTP config working first**.


## License information

This project is available as open source under the terms of the AGPL 3.0 or later license. However, some elements are being licensed under different licenses, for accurate information please check individual files and also check the NOTICE file in the root of the project.
