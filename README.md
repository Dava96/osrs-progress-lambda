# Osrs Progress Lambda

This AWS Lambda function fetches Old School Runescape player progress and posts updates to a Discord channel via webhook.

## Features

- Fetches player progress from the Wise Old Man API
- Wont include inactive players
- Ranks players by either experience, boss, activity, or efficiency metrics
- Formats and sends updates to Discord using webhooks
- Designed for automated deployment with GitHub Actions

Ranking Embed

![image](https://github.com/user-attachments/assets/3cac51ec-d546-4b25-82ed-a6e8ed3fb605)

Player Embed

![image](https://github.com/user-attachments/assets/91a5a96f-448b-48c5-add6-a5db4d3d5405)



## Usage

1. Set the following environment variables in Lambda:
   - `USERNAMES`: Comma-separated list of OSRS usernames - Required
   - `WEBHOOK_URL`: Discord webhook URL - Required
   - `SEND_PLAYER_EMBED`: `true`, `false` - Defaults to `true`
   - `SEND_RANKING_EMBED`: `true`,`false` - Default to `true`
   - `SORT_BY`: `experience_gains`, `boss_gains`, `activity_gains` - Defaults to `experience_gains`
   - `PERIOD`: `five_min` `day`, `week`, `month` - Defaults to `day`

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

## Thanks to
https://github.com/wise-old-man/wise-old-man

