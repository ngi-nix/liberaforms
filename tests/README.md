# Tests

```
source ./venv/bin/activate
pip install pytest
pip install pytest-dotenv
pip install pytest-order
#pip install pytest-dependency
#pip install pytest-pythonpath
```

Create `test.env` and edit
```
cd ./tests
cp test.env.example test.env
```

Run all tests, unit tests, functional tests

```
cd ./tests
pytest -v
pytest -v unit
pytest -v functional
```


# List of tests

## Database
  * create tables with alembic migrations. fixture[✔]

## Users
  * create first admin user with ROOT_USERS email. functional[✔]
  * create user. unit[✔]
  * create new user with new user form
    * with RESERVED_USERNAMES
  * invite new user
    * with admin permission
    * respond to invitation

## Site
  * create a new site. unit[✔]

## Site configuration
  * save and restore favicon. functional[✔]
  * change colour. functional[✔]
  * change site name. functional[✔]
  * change default language. functional[✔]
  * change 'only invitations'. functional[✔]
  * change port. functional[✔]
  * change scheme. functional[✔]
  * edit landing page. functional[✔]
  * add/edit/delete consentment texts
  * config SMTP functional[✔] (partially)
  * test SMTP



## Forms
### Create form
  * with RESERVED_SLUGS
  * with RESERVED_FORM_ELEMENT_NAMES

### Answers
  * make a answer
  * delete/undo answer
  * edit a answer
  * delete all answer

### Exipry conditions
  * Set date expiry in past
  * set number field max total
  * set max answers

### Share a form
  * add an editor

### Shared results.
  * share the results and check the links

### Post submit text
  * Modify  the text
  * Check if user receives confirmation email.

7. CSV
  * export
  * export with deleted columns

8. Activate GDPR and try to submit a form with out checkbox.
9. Test embedded form
10. Duplicate form
11. Change author

12. Delete form and entries

13. Drop database and restore copy
