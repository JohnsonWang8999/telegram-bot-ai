
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

BOT_TOKEN = "7722054827:AAEFz3rPshUF53zhwzNUyp6jVo5bzN89Nms"
WEBHOOK_SECRET = "/webhook"

app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Hello! Bot is running with webhook!")

application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 10000)),
    webhook_url=f"https://airbnb-xiao-fei-ji-lu-qi-ren.onrender.com{WEBHOOK_SECRET}",
    secret_token=WEBHOOK_SECRET.strip("/")
)

@app.post(WEBHOOK_SECRET)
async def webhook():
    await application.update_queue.put(Update.de_json(request.json, application.bot))
    return "ok"
