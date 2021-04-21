# Tests


```
source ./venv/bin/activate
pip install pytest
pip install pytest-dotenv
```

Create `test.env` and edit
```
cd ./tests
cp test.env.example test.env
```

Run all tests, unit tests, functional tests

```
cd ./test
pytest
pytest unit
pytest functional
```
