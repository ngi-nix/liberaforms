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
