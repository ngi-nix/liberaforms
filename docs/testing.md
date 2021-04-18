# Tests


```
source ./venv/bin/activate
pip install pytest
pip install pytest-dotenv
```

Create `.env` and edit
```
cd ./liberaforms/tests
cp dotenv.example .env
```

Run all tests

```
pytest
```

Run only `unit` tests

```
cd ./liberaforms/tests/unit
pytest
```
