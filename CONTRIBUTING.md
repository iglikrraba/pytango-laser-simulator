# Contributing

Thanks for your interest in improving this project.

## Development setup

```
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

## Run checks

```
PYTANGO_SKIP_HMI_TEST=1 ./venv/bin/python verify_system.py
```

## Guidelines
- Follow PEP 8 for Python code style.
- Keep changes focused and include clear commit messages.
- If you add new behavior, update the README where needed.

## Pull requests
- Create a feature branch and open a PR against `main`.
- Describe the change and how it was tested.
