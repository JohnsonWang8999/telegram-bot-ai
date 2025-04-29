
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

app = Flask(__name__)

BOT_TOKEN = "7138174010:AAHVDnTtHAs40OD_QbfuvM4cJuncRFg1DB8"
WEBHOOK_PATH = "/webhook"

application = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello! Your Airbnb bot is running.")

application.add_handler(CommandHandler("start", start))

@app.post(WEBHOOK_PATH)
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.update_queue.put(update)
    return "ok"

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url="https://airbnb-xiao-fei-ji-lu-qi-ren.onrender.com/webhook",
        secret_token="webhook"
    )
