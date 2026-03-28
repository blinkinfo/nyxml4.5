# AutoPoly - BTC Up/Down 5-Min Trading Bot

Automated Polymarket trading bot that monitors BTC 5-minute Up/Down markets, generates signals based on price momentum, and optionally executes FOK (Fill-Or-Kill) market orders via Telegram.

## How It Works

### Strategy

Every 5 minutes, Polymarket runs a BTC Up/Down market (will BTC price go up or down in the next 5 minutes). The bot:

1. **Monitors** the current slot's Up/Down prices 85 seconds before it ends (T-85s)
2. **Signals** if either side reaches >= $0.53 (indicating market consensus)
3. **Trades** the signalled side in the NEXT 5-minute slot (N+1)
4. **Resolves** the outcome after the slot ends and tracks P&L

### Timing

- Slots align to clock: `:00`, `:05`, `:10`, `:15` ... `:55` of each hour
- Signal check: 3 minutes 35 seconds into each slot (T-85s before end)
- Example: Slot 10:00-10:05 -> check at 10:03:35 UTC -> trade in 10:05-10:10

## Features

- Real-time signal detection every 5 minutes
- Optional auto-trading with configurable USDC amount
- Full Telegram bot interface with inline keyboards
- Signal and trade performance dashboards
- Win/loss tracking with streak analytics
- SQLite database for persistence across restarts
- Recovery of unresolved signals on restart
- Single-chat authentication
- One-click Railway deployment

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POLYMARKET_PRIVATE_KEY` | Yes | - | Ethereum private key for Polymarket |
| `POLYMARKET_FUNDER_ADDRESS` | Yes | - | Funder/proxy wallet address |
| `POLYMARKET_SIGNATURE_TYPE` | No | `2` | Signature type (0, 1, or 2) |
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Yes | - | Authorised Telegram chat ID |
| `TRADE_AMOUNT_USDC` | No | `1.0` | Default trade amount in USDC |
| `DB_PATH` | No | `autopoly.db` | SQLite database path |

## Telegram Bot Setup

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token -> set as `TELEGRAM_BOT_TOKEN`
4. Message your new bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Find your `chat.id` -> set as `TELEGRAM_CHAT_ID`

## Railway Deployment

1. Fork this repository
2. Go to [Railway](https://railway.app) and create a new project
3. Connect your GitHub repo
4. Add environment variables in the Railway dashboard
5. Deploy - Railway will use the `Procfile` automatically

The bot runs as a worker process (no web server needed).

## Local Development

```bash
# Clone the repo
git clone https://github.com/blinkinfo/autopoly.git
cd autopoly

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your values

# Run
python main.py
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu with inline keyboard |
| `/status` | Bot status, balance, connection info |
| `/signals` | Signal performance dashboard |
| `/trades` | Trade P&L dashboard |
| `/settings` | Toggle autotrade, set trade amount |
| `/help` | Command reference |

## Project Structure

```
autopoly/
|-- bot/              # Telegram bot layer
|   |-- handlers.py   # Command & callback handlers
|   |-- keyboards.py  # Inline keyboard layouts
|   |-- formatters.py # Message formatting (UTC timeslots)
|   |-- middleware.py  # Chat ID auth guard
|-- core/             # Trading engine
|   |-- strategy.py   # Signal detection (T-85s, $0.53 threshold)
|   |-- trader.py     # FOK order execution
|   |-- resolver.py   # Outcome polling
|   |-- scheduler.py  # APScheduler 5-min loop
|-- polymarket/       # Polymarket API layer
|   |-- client.py     # ClobClient with L2 creds
|   |-- markets.py    # Slot boundaries & Gamma API
|   |-- account.py    # Balance & positions
|-- db/               # Database layer
|   |-- models.py     # SQLite schema
|   |-- queries.py    # CRUD & analytics
|-- config.py         # Environment config
|-- main.py           # Entry point
```

## Technical Notes

- Uses `aiosqlite` for non-blocking database access
- Uses `httpx.AsyncClient` for Gamma API calls
- `py-clob-client` calls wrapped in `asyncio.to_thread()` (synchronous library)
- APScheduler and Telegram bot share the same async event loop
- FOK order amounts rounded to 2 decimal places (py-clob-client issue #121)
- All timestamps stored and displayed in UTC

## License

MIT
