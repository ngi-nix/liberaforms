# Tests

```
source ./venv/bin/activate
pip install pytest
pip install pytest-dotenv
#pip install pytest-order
#pip install pytest-dependency
#pip install pytest-pythonpath
```

Create `test.ini` and edit
```
cd ./tests
cp test.ini.example test.ini
```

Run all tests, unit tests, functional tests

```
cd ./tests
pytest -v
pytest -v unit
pytest -v functional
```

See more output

```
pytest -v -s
```

## Testing emails notifications

You will need two valid email accounts. One for `admin` and one for `dummy user`

You can skip sending mails by setting `SKIP_EMAILS` to `True` in `test.ini`

# List of tests

## Database
  * create tables with alembic migrations. fixture[✔]

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
  * config SMTP functional[✔]
  * test SMTP functional[✔]
  * set public link creation. functional[✔]

## Users
  * create first admin user with ROOT_USERS email. functional[✔]
  * test admin preferneces. functional[✔]
  * test new user form. functional[✔]
    * with invalid email/password. functional[✔]
    * with RESERVED_USERNAMES. functional[✔]
    * unique username/email. functional[✔]
  * create user. unit[✔]
  * change email
  * change password. functional[✔]
  * change language. functional[✔]
  * set New answer notification default. functional[✔]
  * invite new user. functional[✔]
    * delete invite. functional[✔]
    * with admin permission. functional[✔]

## Forms
  * create a form. functional[✔]
    * with RESERVED_SLUGS. functional[✔]
    * with unavailable slugs. functional[✔]
    * with RESERVED_FORM_ELEMENT_NAMES
  * set date expiry in past and future. functional[✔]
  * set and test number field max total. functional[✔]
  * test number field max total expiry. functional[✔]
  * set and test max answers. functional[✔]
  * test max answers expiry. functional[✔]
  * add an editor. functional[✔]
  * share answers. functional[✔]
    * check the links
  * modify post submit text. functional[✔]
  * modify expity text. functional[✔]
  * check if user receives confirmation email.
  * activate GDPR consent. functional[✔]
    * and try to submit a form with out checkbox.
  * duplicate form. functional[✔]
  * test embedded form. functional[✔]
  * change author
  * delete form and answers. functional[✔]

## Answers
  * make an answer. functional[✔]
  * delete an answer. functional[✔]
  * undo delete
  * edit a answer
  * delete all answers. functional[✔]
  * export CSV. functional[✔]
  * export CSV with deleted columns

# Backups
Drop database and restore copy
