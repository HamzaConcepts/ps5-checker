# 🎮 PlayStation 5 Direct Stock Alert Bot

A lightweight, high-speed, zero-cost stock monitoring bot for **PlayStation®5 Pro (2 TB)** on PlayStation Direct. When stock becomes available, it immediately dispatches alerts to your **Discord Server** (with rich embeds, sound, and direct buy links).

---

## ⚡ Quick Start & Deployment Options

You have two easy ways to run this bot for **100% FREE**:

| Option | Setup Time | Needs PC On? | Cost | Recommended For |
| :--- | :--- | :--- | :--- | :--- |
| **1. GitHub Actions** | **2 minutes** | ❌ No (Runs in Cloud) | **$0 / Free Forever** | **Zero effort, hands-free 24/7 cloud monitoring** |
| **2. Local Background** | **10 seconds** | ✔ Yes | **$0 / Free** | **Instant check & local sound alarm** |

---

## Step 1: Create Your Discord Webhook (Takes 60 Seconds)

1. Open **Discord** and go to your server (or create a private server).
2. Right-click on the channel where you want notifications (e.g. `#ps5-alerts`) and click **Edit Channel** (⚙ gear icon).
3. Click **Integrations** on the left menu.
4. Click **Webhooks** ➔ **New Webhook**.
5. Give it a name (e.g., `PS5 Stock Alert`) and click **Copy Webhook URL**.

---

## Option A: Free Cloud Hosting via GitHub Actions (Minimal Effort, 0 Cost)

GitHub Actions will automatically run the stock checker every 5 minutes in the cloud. You do **not** need to keep your PC on, and it costs **$0**.

### Steps:
1. **Push this repository to GitHub**:
   - Create a new repository on [GitHub](https://github.com/new) (can be Public or Private).
   - Push this folder to your repository:
     ```bash
     git init
     git add .
     git commit -m "feat: initial ps5 stock bot"
     git branch -M main
     git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
     git push -u origin main
     ```

2. **Add your Discord Webhook URL to GitHub Secrets**:
   - In your GitHub repo, go to **Settings** ➔ **Secrets and variables** ➔ **Actions**.
   - Click **New repository secret**.
   - **Name**: `DISCORD_WEBHOOK_URL`
   - **Secret**: *Paste your Discord Webhook URL here*.
   - Click **Add secret**.

3. **Enable & Test the Workflow**:
   - Go to the **Actions** tab in your GitHub repository.
   - Click **PS5 Stock Monitor** on the left.
   - Click **Run workflow** ➔ **Run workflow** to test it immediately.
   - It will now run automatically on schedule every 5 minutes!

---

## Option B: Run Locally on Your PC / Laptop

### On Windows:
1. Open `.env` file in a text editor (e.g. Notepad, VS Code) and paste your Discord Webhook URL:
   ```ini
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz
   ```
2. Double-click `run_local.bat` (or run in PowerShell: `python main.py`).

### On Linux / macOS:
```bash
cp .env.example .env
# Edit .env and paste your DISCORD_WEBHOOK_URL
chmod +x run_local.sh
./run_local.sh
```

---

## 🧪 Testing the Bot & Notification

To test that your Discord webhook is working properly and see how in-stock vs out-of-stock items are detected:

```bash
python main.py --test
```

This runs a dual test:
1. Queries the **in-stock reference item** (PS5 Digital Edition) to verify in-stock detection.
2. Queries the **PS5 Pro** to verify out-of-stock detection.
3. Sends a sample test alert embed to your Discord channel.

---

## ⚙️ Configuration Reference (`.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DISCORD_WEBHOOK_URL` | *Empty* | Discord Channel Webhook URL |
| `DISCORD_NOTIFY_ROLE_ID` | `everyone` | Role mention on in-stock (`everyone`, `here`, or custom Role ID) |
| `DISCORD_BOT_USERNAME` | `PS5 Stock Alert Bot` | Name displayed in Discord message |
| `CHECK_INTERVAL_SECONDS` | `60` | Frequency (in seconds) when running in continuous loop |
| `PRODUCT_CODE` | `1000050928` | Target product SKU code on PlayStation Direct |
| `TARGET_URL` | `https://direct.playstation.com/...` | Full PlayStation Direct product URL |
| `IN_STOCK_ALERT_COOLDOWN_MINUTES` | `30` | Cooldown before resending reminder if product stays in stock |
| `ENABLE_DESKTOP_SOUND` | `true` | System beep alarm when stock is detected |
| `TELEGRAM_BOT_TOKEN` | *Optional* | Telegram Bot API token |
| `TELEGRAM_CHAT_ID` | *Optional* | Telegram Chat ID |
| `NTFY_TOPIC` | *Optional* | Free push notification topic via `ntfy.sh` |

---

## 🐳 Optional: Run with Docker

```bash
docker compose up -d --build
```

---

## 🛠️ CLI Command Options

- `python main.py` — Continuous monitoring loop (checks every 60s by default).
- `python main.py --once` — Runs a single check and exits (used by GitHub Actions / Cron).
- `python main.py --test` — Runs test suite and dispatches test alert to Discord.
- `python main.py --interval 30` — Runs loop with custom 30-second interval.

---

## 🔒 Reliability & Anti-Ban Architecture
- **Dual-Engine Checking**: Primary check uses PlayStation Direct's internal Commerce REST API for sub-second responses; automatically falls back to full HTML parsing if the API format ever changes.
- **Stealth Requesting**: Uses randomized modern User-Agents, realistic browser headers, and standard browser CORS signatures.
- **State Management**: Persists status in `stock_state.json` to prevent repeated notification spam.
