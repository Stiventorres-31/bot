# AviatorProBot

A Python Telegram bot that monitors the Aviator game, detects trading signals via an external API, and sends real-time alerts to a Telegram channel. It implements a **martingale (gale) strategy** — automatically escalating bet suggestions on a loss, up to a configurable number of gales, before resetting the cycle.

## Features

- Fetches live round data from the Aviator API
- Applies a balanced signal filter to identify high-confidence entries
- Sends formatted Telegram messages for entries, gales, wins, and losses
- Configurable martingale depth, stake percentages, and cooldown periods
- Runs continuously as a background worker (no HTTP server required)

## Environment Variables

Set these in your Railway service before deploying:

| Variable           | Description                              |
|--------------------|------------------------------------------|
| `TELEGRAM_TOKEN`   | Bot token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Target channel or group chat ID          |

## Deploy on Railway

1. Connect this repository to a new Railway service.
2. Set the `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` environment variables in the Railway dashboard.
3. Railway will automatically detect the `Procfile` and run the bot as a **worker** process.

## Local Development

```bash
pip install -r requirements.txt
export TELEGRAM_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
python main.py
```

## Dependencies

- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) 4.14.0
- [requests](https://docs.python-requests.org/) 2.31.0

## Disclaimer

This bot is for educational purposes only. Always gamble responsibly.
