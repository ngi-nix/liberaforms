# Contributing
Under construction ..

# Translating
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
### Translating files
#### PoEdit and Lokalize
[**PoEdit**](https://poedit.net/) and [**Lokalize**](https://apps.kde.org/lokalize/) are easy to use programs to translate translation files over gettext system. With them, one can create PO files from templates (POT), translate them and add the relevant metadata (last translator, language, last modification date...)

***Other graphical editors:***
+ [Better Po Editor](https://github.com/mlocati/betterpoeditor/releases)
+ [EazyPo](http://www.eazypo.ca/)
+ [GNOME Translation Editor](https://wiki.gnome.org/Apps/Gtranslator)

#### By hand
PO files have this kind of structure:
```
#: models/form.py:690
msgid "Context"
msgstr "Testuingurua"
```
> You can copy and rename an existing, updated PO file (use another language's file). Use the corresponding [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) to rename your file.

Once having your language's file, just edit the content of `msgstr` lines for each block, edit the metadata and save your file.

### Sending changes
You can send the created or changed files via **email** to porru@liberaforms.org address or via **git** with [Merge Requests](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)


## Commit messages

Messages should be useful.

An example message.
```
database schema: change port property type from string to integer

A port number is a 16-bit unsigned integer.
Using Integer makes the database schema more explicit.

Port numbers are described at
https://en.wikipedia.org/wiki/Port_(computer_networking)

Fixes #21
```
