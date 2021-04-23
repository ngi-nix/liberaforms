# Tests


```
source ./venv/bin/activate
pip install pytest
pip install pytest-dotenv
#pip install pytest-order
#pip install pytest-dependency
#pip install pytest-pythonpath
```

Create `test.env` and edit
```
cd ./tests
cp test.env.example test.env
```

Run all tests, unit tests, integration test, functional tests

```
cd ./test
pytest
pytest unit
pytest integration
pytest functional
```
