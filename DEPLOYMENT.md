# StudyBiz AI - Deployment Guide

This guide covers deploying StudyBiz AI to the internet so anyone can access it via a public URL.

## Prerequisites

Before you start, you need:

1. **A Telegram Bot Token** (if you want Telegram integration)
   - Open Telegram, search for @BotFather
   - Send `/newbot`
   - Follow the prompts to name your bot
   - Copy the token (looks like `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`)

2. **An OpenAI API key** (optional - improves AI responses)
   - Go to https://platform.openai.com/api-keys
   - Create a new key
   - Copy it (starts with `sk-`)

3. **Your GitHub repo** (already done)
   - https://github.com/Siew-116/synchrost

---

## Option A: Render.com (Recommended - Free Tier, Easiest)

Render is a cloud platform with a free tier that works perfectly for this app.

### Step 1: Create a Render account
- Go to https://render.com
- Sign up with your GitHub account
- Authorize Render to access your repos

### Step 2: Create a new Web Service
1. Click "New +" then "Web Service"
2. Select your repo: `Siew-116/synchrost`
3. Configure:
   - **Name**: `studybiz-ai` (or any name you want)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

4. Click "Advanced" and add Environment Variables:

   | Key | Value |
   |-----|-------|
   | DEMO_MODE | false |
   | EXAM_MODE | false |
   | PYTHONPATH | /opt/render/project/src/backend |
   | TELEGRAM_BOT_TOKEN | your_bot_token_from_botfather |
   | TELEGRAM_CONNECTED | true |
   | TELEGRAM_WEBHOOK_URL | https://your-app-name.onrender.com/api/telegram/webhook |
   | LLM_API_KEY | your_openai_key (optional) |
   | LLM_MODEL | gpt-4o-mini |

   Note: Replace `your-app-name` with the actual name Render gives your service.

5. Click "Create Web Service"

### Step 3: Wait for deployment
- Render will build and deploy automatically
- Takes about 2-3 minutes
- You will get a URL like: `https://studybiz-ai.onrender.com`

### Step 4: Set the Telegram webhook
Once deployed, run this command (replace with your actual URL and bot token):

```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://studybiz-ai.onrender.com/api/telegram/webhook"}'
```

You should get: `{"ok":true,"result":true,"description":"Webhook was set"}`

### Step 5: Test it
- Open your Render URL in a browser to see the app
- Send a message to your Telegram bot
- The AI should respond and create orders

---

## Option B: Railway.app

Railway is another easy platform with a free trial.

### Step 1: Sign up
- Go to https://railway.app
- Sign up with GitHub

### Step 2: Deploy
1. Click "New Project" then "Deploy from GitHub repo"
2. Select `Siew-116/synchrost`
3. Railway auto-detects Python. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. Add Environment Variables (same list as Render above)

5. Railway gives you a URL like `studybiz-ai-production.up.railway.app`

6. Set the Telegram webhook with that URL.

---

## Option C: Fly.io

Fly.io has a free tier and is good for Docker-based deployments.

### Step 1: Install Fly CLI
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Mac/Linux
curl -L https://fly.io/install.sh | sh
```

### Step 2: Deploy
```bash
fly auth signup          # or fly auth login if you have an account
cd studybiz-ai
fly launch               # Answer the prompts - it will use the Dockerfile
fly secrets set DEMO_MODE=false
fly secrets set TELEGRAM_BOT_TOKEN=your_bot_token
fly secrets set TELEGRAM_CONNECTED=true
fly secrets set TELEGRAM_WEBHOOK_URL=https://your-app.fly.dev/api/telegram/webhook
fly secrets set LLM_API_KEY=your_openai_key
fly deploy
```

You will get a URL like `https://studybiz-ai.fly.dev`

Set the webhook:
```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://studybiz-ai.fly.dev/api/telegram/webhook"}'
```

---

## Option D: VPS (DigitalOcean, AWS EC2, etc.)

For full control, deploy on a virtual server.

### Step 1: Create a server
- DigitalOcean: Create a Droplet (Ubuntu 22.04, $4/month smallest)
- AWS: Launch an EC2 instance (t2.micro, free tier)

### Step 2: SSH into the server
```bash
ssh root@your_server_ip
```

### Step 3: Install Python and clone the repo
```bash
apt update && apt install -y python3 python3-venv python3-pip git nginx
git clone https://github.com/Siew-116/synchrost.git
cd synchrost/studybiz-ai/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Create .env file
```bash
cat > .env << 'EOF'
DEMO_MODE=false
EXAM_MODE=false
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CONNECTED=true
TELEGRAM_WEBHOOK_URL=http://your_server_ip/api/telegram/webhook
LLM_API_KEY=your_openai_key
LLM_MODEL=gpt-4o-mini
HOST=127.0.0.1
PORT=8000
EOF
```

### Step 5: Run with systemd (keeps it running forever)
```bash
cat > /etc/systemd/system/studybiz.service << 'EOF'
[Unit]
Description=StudyBiz AI
After=network.target

[Service]
User=root
WorkingDirectory=/root/synchrost/studybiz-ai/backend
Environment=PYTHONPATH=/root/synchrost/studybiz-ai/backend
ExecStart=/root/synchrost/studybiz-ai/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable studybiz
systemctl start studybiz
```

### Step 6: Set up Nginx reverse proxy
```bash
cat > /etc/nginx/sites-available/studybiz << 'EOF'
server {
    listen 80;
    server_name your_server_ip_or_domain;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/studybiz /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 7: (Optional) Add HTTPS with free SSL
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

### Step 8: Set Telegram webhook
```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "http://your_server_ip/api/telegram/webhook"}'
```

---

## Environment Variables Reference

| Variable | Demo Mode | Production | Description |
|----------|-----------|------------|-------------|
| DEMO_MODE | true | false | If true, runs without external services |
| EXAM_MODE | false | false | Sets default for Busy Mode |
| TELEGRAM_BOT_TOKEN | (not needed) | required | Bot token from @BotFather |
| TELEGRAM_CONNECTED | false | true | Set true when Telegram is live |
| TELEGRAM_WEBHOOK_URL | (not needed) | required | Public URL + /api/telegram/webhook |
| LLM_API_KEY | (not needed) | optional | OpenAI key for smarter AI |
| LLM_MODEL | gpt-4o-mini | gpt-4o-mini | Model name |
| DATABASE_URL | sqlite:///./studybiz.db | same | Database connection |
| PORT | 8000 | set by platform | Server port |
| PYTHONPATH | (not needed) | /path/to/backend | Python import path |

---

## Telegram Bot Setup (Detailed)

1. Open Telegram on your phone or desktop
2. Search for `@BotFather`
3. Send `/newbot`
4. Enter a name (e.g., "StudyBiz AI Bot")
5. Enter a username ending in `bot` (e.g., `studybiz_ai_bot`)
6. BotFather gives you a token like: `789123456:AAHfh8v...`
7. Copy this token - you will put it in TELEGRAM_BOT_TOKEN

To make your bot respond in a group:
1. Add the bot to your Telegram group
2. Send `/start@your_bot_username` in the group
3. The bot will now receive messages from that group

---

## Post-Deployment Checklist

- [ ] App loads at your public URL (browser shows the dashboard)
- [ ] Settings page shows `DEMO_MODE = false` and `telegram_connected = true`
- [ ] Send a message to your Telegram bot - the AI responds
- [ ] Send "Hi, can I order two black hoodies size M?" - an order is created
- [ ] The order appears in the Orders page
- [ ] Go to Settings > Test AI Agent - works from the public URL
- [ ] Toggle Busy Mode on/off in Settings
- [ ] Approve/reject an exception in the Approvals page

---

## Quick Comparison

| Platform | Free Tier | Setup Time | Best For |
|----------|-----------|------------|----------|
| Render.com | Yes (sleeps after inactivity) | 5 min | Easiest, recommended |
| Railway | $5 free credit | 5 min | Fast, simple |
| Fly.io | Yes (3 small VMs) | 10 min | Docker lovers |
| VPS (DO/AWS) | AWS free tier | 20 min | Full control, production |

**Recommendation: Use Render.com** - it is the fastest to set up, has a free tier, and the `render.yaml` file is already in your repo so you can deploy with one click.

---

## Troubleshooting

**App shows "Demo Mode" after deployment**
- Check that DEMO_MODE=false is set in your platform's environment variables
- Redeploy after adding the variable

**Telegram bot does not respond**
- Verify TELEGRAM_BOT_TOKEN is correct
- Verify TELEGRAM_CONNECTED=true
- Run the setWebhook curl command and check the response
- Check that your webhook URL is accessible (open it in a browser)

**Database is empty after deployment**
- The app seeds data on first startup. If DATABASE_URL points to a persistent volume, data survives restarts
- On Render free tier, the filesystem is ephemeral - data resets on redeploy. For persistent data, use a PostgreSQL database

**"Module not found" error**
- Ensure PYTHONPATH is set to the backend directory path on your platform
