# Git
## Issues

If you want to work on something create an issue

* Use a descriptive Title
* Add contextual information in the description
* Do not assign it to another person
* Assign it to yourself
* Add the label 'Doing' to the issue
* Create a new branch
* When you have finished, tag it with version and merge it into `develop` branch

## Branches
`feat/<name>` _feat: (new feature/objective)_  
`fix/<name>` _fix: (a fix)_  
⇣⇣⇣  
⇣⇣⇣ _We merge our work into develop_  
`develop`  
⇣⇣⇣   
⇣⇣⇣ _We merge develop into WIP, keeping it until  new version  
`WIP`  
⇣⇣⇣  
⇣⇣⇣ **Protected**. We merge WIP into main_  
`main`

## Commit messages

Messages should be useful, written in English and on present tense.

An example message:
```
database schema: change port property type from string to integer

A port number is a 16-bit unsigned integer.
Using Integer makes the database schema more explicit.

Port numbers are described at
https://en.wikipedia.org/wiki/Port_(computer_networking)

Fixes #21
```

## Tagging

Merge requests must be tagged

After commiting your changes, create a tag. Change the message when relevant.
```
git tag -a v$(cat VERSION.txt) -m "Bumped version $(cat VERSION.txt)"
git push origin v$(cat VERSION.txt)
```

You can list the tags

```
git tag -l --sort=-version:refname "v*"
```

# Internationalizating (i18n)
## Entering parameters into translatable strings
**Python**
`_("Text using a %s" % parameter)`

**Jinja2 HTML**  
`{%trans user=g.current_user.username%}Hello {{user}}!{%endtrans%}`  
parameters must be aliased **in** the translation opening structure and then, use that alias **in** the string surrounded with two key-brackets

## Translator comments
+ Python files: `# i18n: a comment` before internationalized strings
+ Jinja2 HTML files: `{# i18n: a comment #}` before internationalized strings


# Translating (L10n)
## Weblate
> We are working on this feature. This part will be updated.

## Manual method
> LiberaForms uses the **gettext** internationalization and localization system, so three file types exist:
> + **POT** (Portable Object Template)
>   + This is the template for all other translations. Here is were strings in code are referenced to be translated.
> + **PO** (Portable Object)
>   + These are translation files for each language. They are created from .POT and on these only the translations are made.
> + **MO** (Machine Object)
>   + Binary files generated from each .PO, computer-readable.
>   
> **JS** and **LANG** format translation files are also used. _These are translations coming from [FormBuilder](https://github.com/kevinchappell/formBuilder)_
>
> **Current directories with translation files:**  
> + Gettext
>   + ~/liberaforms/translations
>   + ~/liberaforms/form_templates/translations
> + JS
>   + ~/liberaforms/static/dataTables-languages  
> + LANG
>   + ~/liberaforms/static/formBuilder-languages   

### Translating files
#### With PoEdit and Lokalize
[**PoEdit**](https://poedit.net/) and [**Lokalize**](https://apps.kde.org/lokalize/) are easy to use programs to translate translation files over gettext system. With them, one can create PO files from templates (POT), translate them and add the relevant metadata (last translator, language, last modification date...)

***Other graphical editors:***  
* [Better Po Editor](https://github.com/mlocati/betterpoeditor/releases)
* [EazyPo](http://www.eazypo.ca/)
* [GNOME Translation Editor](https://wiki.gnome.org/Apps/Gtranslator)

#### By hand
##### PO files
They have this kind of structure:
```
#: models/form.py:690  
msgid "Context"
msgstr "Testuingurua"
```
> You can copy and rename an existing, updated PO file (use another language's file). <!-- Use the corresponding [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) code to rename your file. -->

Once having your language's file, just edit the content of `msgstr` lines for each block, edit the metadata and save your file.

##### JS files
They have this kind of structure:
```
{
"sProcessing":     "Prozesatzen...",
[...] }
```
> You can copy and rename an existing, updated JS file (use another language's file). Use the corresponding [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) code to rename your file.

Once having your language's file, just edit the content of the second part of each line.

##### LANG files
They have this kind of structure:
```
NATIVE_NAME = Dansk
ENGLISH_NAME = Danish

addOption = Tilføj valgmulighed +
allFieldsRemoved = Alle felter blev fjernet.
[...]
```
> You can copy and rename an existing, updated LANG file (use another language's file). Use the corresponding [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) code to rename your file and specify it's country variant.

Once having your language's file, just edit the content of the second part of each line.



### Sending changes
You can send the created or changed files via **email** to porru@liberaforms.org address or via **git** with [Merge Requests](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)

# Handy commands
## Update translation files
We use `pybabel` python module to manage this

### Compiling
> Compiles all existing .po files into .mo files

`pybabel compile -d ./translations`  
[Read more](http://babel.pocoo.org/en/latest/cmdline.html#compile)

> For Form Templates:

`pybabel compile -d form_templates/translations`

### Extracting
> Updates .pot file from code, extracting comments starting with 'i18n:' and adding relevant metadata

`pybabel extract -F babel/messages.cfg -o translations/messages.pot ./ --add-comment='i18n:' --copyright-holder='LiberaForms, CC-BY-SA' --msgid-bugs-address='info@liberaforms.org'`  
[Read more](http://babel.pocoo.org/en/latest/cmdline.html#extract)

> For Form Templates:

`pybabel extract -F babel/form_templates.cfg -o form_templates/translations/form_templates.pot ./ --add-comment='i18n:' --copyright-holder='LiberaForms, CC-BY-SA' --msgid-bugs-address='i
nfo@liberaforms.org'`

### Creating
> Creates new .po file from .pot.  
_You must specify the target language adding its [ISO-639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) code at the end of command_

`pybabel init -i ./translations/messages.pot -d ./translations -l eo`  
[Read more](http://babel.pocoo.org/en/latest/cmdline.html#init)

> For Form Templates:

`pybabel init -i form_templates/translations/form_templates.pot -d form_templates/translations -l eo`

### Updating
> Updates .po files according to .pot.  

`pybabel update -i ./translations/messages.pot -d ./translations`  
[Read more](http://babel.pocoo.org/en/latest/cmdline.html#update)

> For Form Templates:

`pybabel update -i form_templates/translations/form_templates.pot -d form_templates/translations`
