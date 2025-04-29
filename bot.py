
import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = os.getenv("BOT_TOKEN", "7138174010:AAHVDnTtHAs40OD_QbfuvM4cJuncRFg1DB8")
DATA_FILE = "records.json"

UNITS = [
    "Danga Bay 16A-01-02",
    "Danga Bay 7A-18-03A",
    "Danga Bay 17C-19-02",
    "RNF 6A-13A-09",
    "RNF B1-1 23-06",
    "testing"
]

# States
CHOOSE_ACTION, CHOOSE_MONTH, CHOOSE_UNIT, ENTER_AMOUNT, ENTER_DESC, VIEW_UNIT = range(6)

user_data_temp = {}

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def month_keyboard():
    months = [f"{i:02d}" for i in range(1, 13)]
    now = datetime.now()
    current_year = now.year
    return InlineKeyboardMarkup.from_column([
        InlineKeyboardButton(f"{current_year}-{m}", callback_data=f"month:{current_year}-{m}") for m in months
    ])

def unit_keyboard():
    return InlineKeyboardMarkup.from_column([
        InlineKeyboardButton(unit, callback_data=f"unit:{unit}") for unit in UNITS
    ])

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧾 记录消费", callback_data="record")],
        [InlineKeyboardButton("📊 查看账单", callback_data="view")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 Airbnb 每月消费记录 Ai Bot！", reply_markup=main_menu_keyboard())
    return CHOOSE_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_data_temp[query.from_user.id] = {"action": action}
    await query.edit_message_text("请选择月份：", reply_markup=month_keyboard())
    return CHOOSE_MONTH

async def choose_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    month = query.data.split(":")[1]
    uid = query.from_user.id
    user_data_temp[uid]["month"] = month

    if user_data_temp[uid]["action"] == "record":
        await query.edit_message_text("请选择单位：", reply_markup=unit_keyboard())
        return CHOOSE_UNIT
    else:
        await query.edit_message_text("请选择要查看的单位：", reply_markup=unit_keyboard())
        return VIEW_UNIT

async def choose_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    unit = query.data.split(":")[1]
    uid = query.from_user.id
    user_data_temp[uid]["unit"] = unit
    await query.edit_message_text("请输入消费金额（RM）：")
    return ENTER_AMOUNT

async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    user_data_temp[uid]["amount"] = update.message.text.strip()
    await update.message.reply_text("请输入消费备注：")
    return ENTER_DESC

async def enter_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    desc = update.message.text.strip()
    temp = user_data_temp[uid]
    now = datetime.now()
    entry = {
        "date": now.strftime("%Y-%m-%d"),
        "amount": temp["amount"],
        "desc": desc
    }

    data = load_data()
    data.setdefault(str(uid), {}).setdefault(temp["month"], {}).setdefault(temp["unit"], []).append(entry)
    save_data(data)

    await update.message.reply_text(f"✅ 已记录：{temp['unit']} | RM{temp['amount']} | {desc}")
    return ConversationHandler.END

async def view_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    unit = query.data.split(":")[1]
    uid = query.from_user.id
    month = user_data_temp[uid]["month"]
    data = load_data()
    records = data.get(str(uid), {}).get(month, {}).get(unit, [])

    if not records:
        await query.edit_message_text("该单位无消费记录。")
        return ConversationHandler.END

    lines = [f"{r['date']} - RM{r['amount']} - {r['desc']}" for r in records]
    total = sum(float(r["amount"]) for r in records)
    message = f"📊 {month} - {unit}:
" + "
".join(lines) + f"

总额：RM{total:.2f}"
    await query.edit_message_text(message)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("已取消操作。")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_ACTION: [CallbackQueryHandler(choose_action)],
            CHOOSE_MONTH: [CallbackQueryHandler(choose_month)],
            CHOOSE_UNIT: [CallbackQueryHandler(choose_unit)],
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            ENTER_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_desc)],
            VIEW_UNIT: [CallbackQueryHandler(view_unit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
