from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

MAIN_MENU, RECORD_UNIT, RECORD_AMOUNT, RECORD_NOTE, SELECT_MONTH, SELECT_UNIT_VIEW = range(6)
records_by_month = {}

units = [
    ("u1", "Danga Bay 16A-01-02"),
    ("u2", "Danga Bay 7A-18-03A"),
    ("u3", "Danga Bay 17C-19-02"),
    ("u4", "RNF 6A-13A-09"),
    ("u5", "RNF B1-1 23-06")
]
unit_map = dict(units)
unit_map_reverse = {v: k for k, v in units}

def get_current_month():
    return datetime.now().strftime("%Y-%m")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 记录消费", callback_data="record")],
        [InlineKeyboardButton("📊 查看账单", callback_data="view")]
    ]
    await update.message.reply_text(
        "你好！请选择操作：",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

async def auto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "record":
        keyboard = [[InlineKeyboardButton(name, callback_data=f"unit_{code}")] for code, name in units]
        await query.edit_message_text("请选择消费单位：", reply_markup=InlineKeyboardMarkup(keyboard))
        return RECORD_UNIT

    elif query.data == "view":
        now = datetime.now()
        month_buttons = []
        for i in range(3):
            month = (now.month - i - 1) % 12 + 1
            year = now.year if now.month - i > 0 else now.year - 1
            month_str = f"{year}-{month:02d}"
            month_buttons.append([InlineKeyboardButton(month_str, callback_data=f"month_{month_str}")])
        await query.edit_message_text("请选择要查看的月份：", reply_markup=InlineKeyboardMarkup(month_buttons))
        return SELECT_MONTH

async def unit_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    unit_code = query.data.replace("unit_", "")
    unit_name = unit_map.get(unit_code, unit_code)
    context.user_data["unit"] = unit_name
    await query.edit_message_text(f"已选择单位：{unit_name}\n请输入消费金额 (如：25)：")
    return RECORD_AMOUNT

async def input_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text
    await update.message.reply_text("请输入消费明细 (如：洗碗液)：")
    return RECORD_NOTE

async def input_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = update.message.text
    unit = context.user_data["unit"]
    amount = context.user_data["amount"]
    month = get_current_month()

    record = {
        "date": datetime.now().strftime("%-d %b"),
        "unit": unit,
        "amount": amount,
        "note": note
    }
    if month not in records_by_month:
        records_by_month[month] = []
    records_by_month[month].append(record)

    await update.message.reply_text(
        f"✅ 成功记录！\n\n"
        f"日期：{record['date']}\n"
        f"单位：{unit}\n"
        f"金额：RM{amount}\n"
        f"明细：{note}"
    )
    return ConversationHandler.END

async def month_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_month = query.data.replace("month_", "")
    context.user_data["view_month"] = selected_month

    keyboard = [[InlineKeyboardButton(name, callback_data=f"viewunit_{code}")] for code, name in units]
    keyboard.append([InlineKeyboardButton("📋 全部单位汇总", callback_data="viewall")])

    await query.edit_message_text(f"请选择要查看的单位：", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_UNIT_VIEW

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    month = context.user_data.get("view_month", get_current_month())
    all_records = records_by_month.get(month, [])

    if query.data == "viewall":
        summary = {}
        for r in all_records:
            summary.setdefault(r["unit"], 0.0)
            summary[r["unit"]] += float(r["amount"])
        text = f"📊 {month} 总结账单：\n\n" if summary else f"📭 {month} 暂无记录。"
        for unit, total in summary.items():
            text += f"{unit}：RM{total:.2f}\n"
    else:
        unit_code = query.data.replace("viewunit_", "")
        unit = unit_map.get(unit_code, unit_code)
        unit_records = [r for r in all_records if r["unit"] == unit]
        if not unit_records:
            text = f"📭 {unit} 在 {month} 没有记录。"
        else:
            text = f"📋 {unit} - {month} 消费记录：\n\n"
            for r in unit_records:
                text += f"{r['date']} RM{r['amount']} {r['note']}\n"

    await query.edit_message_text(text)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ 操作已取消。")
    return ConversationHandler.END

app = ApplicationBuilder().token("7722054827:AAEFz3rPshUF53zhwzNUyp6jVo5bzN89Nms").build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, auto_start)],
    states={
        MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
        RECORD_UNIT: [CallbackQueryHandler(unit_selected)],
        RECORD_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_amount)],
        RECORD_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_note)],
        SELECT_MONTH: [CallbackQueryHandler(month_selected)],
        SELECT_UNIT_VIEW: [CallbackQueryHandler(show_summary)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
app.run_polling()
print("🤖 Bot 正在运行中...")
