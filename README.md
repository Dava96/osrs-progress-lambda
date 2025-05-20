# Osrs Progress Discord Lambda

This AWS Lambda function fetches Old School Runescape player progress and posts updates to a Discord channel via webhook.

## Features

- Fetches player progress from the Wise Old Man API
- Ranks players by either experience, boss, activity, and efficiency metrics
- Formats and sends updates to Discord using webhooks
- Designed for automated deployment with GitHub Actions

## Usage

1. Set the following environment variables in Lambda:
   - `USERNAMES`: Comma-separated list of OSRS usernames
   - `WEBHOOK_URL`: Discord webhook URL

2. Deploy using your preferred method (e.g., GitHub Actions).

## Local Installation

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Testing

Run tests with:

```bash
python -m unittest discover tests
```

## Requirements

- Python 3.12+
- `requests`
- `discord-webhook`

## License

MIT

