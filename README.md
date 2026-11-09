# Win365 Telegram Bot

Win365 is a simple independent productivity bot with three reply-keyboard buttons:

- **Text Counter** — word, character, and line counts for submitted text.
- **Quick Calculator** — safely calculates basic arithmetic.
- **Help & Information** — explains the bot's features.

The bot automatically sets its Telegram **name, About (short description), full description, and command menu** at startup. No gambling, casino, referral, or redirect functionality is included.

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and obtain its token.
2. Set the `BOT_TOKEN` environment variable (never commit the token).
3. Install dependencies: `pip install -r requirements.txt`
4. Start: `python bot.py`

For local setup, copy `.env.example` to `.env`; if using a shell, export the variable or load it before running. The bot reads the `.env` file automatically.

## Hosting on Render

Deploy as a **Background Worker**, using this repo, with:
- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Environment variable: `BOT_TOKEN` = your BotFather token

Alternatively use the supplied Dockerfile. Run only one polling instance per bot token. Do not run a webhook simultaneously.

## Commands

`/start` — show welcome and three-button keyboard  
`/count` — start text counter  
`/calc` — start calculator input  
`/help` — show Help & Information  
`/cancel` — exit calculator input

The text counter counts words, characters, and lines from submitted messages (up to 4,000 characters). The calculator supports +, -, *, /, parentheses, and ^ (power), with safety limits. For example: `(12 + 8) / 4`.

## Telegram Ads destination readiness

Before running ads, upload an appropriate bot profile photo via BotFather; verify all buttons and commands work with the deployed bot; make sure the ad copy accurately describes these features. Telegram independently reviews ads and destinations, so approval is not guaranteed.
