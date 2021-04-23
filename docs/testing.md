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
