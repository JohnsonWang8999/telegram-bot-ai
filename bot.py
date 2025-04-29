import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "7138174010:AAHVDnTtHAs40OD_QbfuvM4cJuncRFg1DB8"
WEBHOOK_PATH = f"/webhook/{TOKEN}"

app = Flask(__name__)
bot = Bot(TOKEN)

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 Airbnb 每月消费记录 Ai Bot！")

application.add_handler(CommandHandler("start", start))

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running."

if __name__ == "__main__":
    application.run_polling()  # Only for local test; not used on Render