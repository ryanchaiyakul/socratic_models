# Socratic Models

A flexible framework for multi agent conversations.

## Setup

1. Create a "secret.py" file with a "SECRET_KEY" variable for your Gemini API key.
2. Create a python virtual environment and install the necessary packages.

```bash
python -m venv .venv
source .venv/bin/activate               # Or .venv/Scripts/activate for windows
pip install -r requirements.txt
```

## Usage

Call the function with the numbers of requested turns (each model uses a turn so 2 turns for both models to speak once).

```bash
py main.py 4
```

## Improvements

- Add a way to easily pass the initial prompt
- Test whether a prompted control signal could be used to differentiate user and model responses as the model only diffentiates between itself and foreign text
- Add OpenAI actor class