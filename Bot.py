import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PRICES = {
    "shid": 1980000,
    "zara": 2325000,
    "karkareh": 2970000
}

MIN_HEIGHT = {
    "shid": 2.0,
    "zara": 1.5,
    "karkareh": 0
}

MIN_AREA = {
    "shid": 2.0,
    "zara": 1.5,
    "karkareh": 1.5
}

SELECTING_TYPE, ENTERING_WIDTH, ENTERING_HEIGHT = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("پرده شید", callback_data="shid")],
        [InlineKeyboardButton("پرده زبرا", callback_data="zara")],
        [InlineKeyboardButton("پرده کرکره", callback_data="karkareh")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "سلام 👋\nنوع پرده رو انتخاب کن:"

    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.message.reply_text(
            text,
            reply_markup=reply_markup
        )

    return SELECTING_TYPE


async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["curtain_type"] = query.data

    type_name = {
        "shid": "شید",
        "zara": "زبرا",
        "karkareh": "کرکره"
    }[query.data]

    await query.edit_message_text(
        f"✅ پرده {type_name} انتخاب شد.\n\nعرض پرده را به متر وارد کن:"
    )

    return ENTERING_WIDTH


async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        width = float(update.message.text)

        if width <= 0:
            await update.message.reply_text("❌ عدد مثبت وارد کن")
            return ENTERING_WIDTH

        context.user_data["width"] = width

        curtain_type = context.user_data["curtain_type"]

        min_height = MIN_HEIGHT[curtain_type]

        if min_height > 0:
            await update.message.reply_text(
                f"ارتفاع را وارد کن (حداقل {min_height} متر):"
            )
            return ENTERING_HEIGHT

        return await calculate_price(update, context)

    except ValueError:
        await update.message.reply_text("❌ فقط عدد وارد کن")
        return ENTERING_WIDTH


async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        height = float(update.message.text)

        if height <= 0:
            await update.message.reply_text("❌ عدد مثبت وارد کن")
            return ENTERING_HEIGHT

        context.user_data["height"] = height

        return await calculate_price(update, context)

    except ValueError:
        await update.message.reply_text("❌ فقط عدد وارد کن")
        return ENTERING_HEIGHT


async def calculate_price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    ctype = context.user_data["curtain_type"]

    width = context.user_data["width"]

    height = context.user_data.get("height", 1)

    area = width * height

    min_h = MIN_HEIGHT[ctype]
    min_a = MIN_AREA[ctype]

    if min_h > 0 and height < min_h:

        await update.message.reply_text(
            f"❌ حداقل ارتفاع {min_h} متر است"
        )

        return ConversationHandler.END

    if area < min_a:

        await update.message.reply_text(
            f"❌ حداقل متراژ {min_a} متر مربع است"
        )

        return ConversationHandler.END

    price_per_sqm = PRICES[ctype]

    total_price = area * price_per_sqm

    type_name = {
        "shid": "شید",
        "zara": "زبرا",
        "karkareh": "کرکره"
    }[ctype]

    result = f"""
✅ محاسبه قیمت پرده {type_name}

📐 عرض: {width} متر
📏 ارتفاع: {height} متر
🧮 مساحت: {area:.2f} متر مربع

💰 قیمت هر متر مربع:
{price_per_sqm:,} تومان

💵 قیمت نهایی:
{total_price:,.0f} تومان
"""

    await update.message.reply_text(result)

    keyboard = [
        [InlineKeyboardButton("🔄 محاسبه مجدد", callback_data="restart")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "دوباره حساب کنیم؟",
        reply_markup=reply_markup
    )

    return ConversationHandler.END


async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    return await start(update, context)


def main():

    TOKEN = "توکن جدید ربات"

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(

        entry_points=[
            CommandHandler("start", start)
        ],

        states={

            SELECTING_TYPE: [
                CallbackQueryHandler(
                    select_type,
                    pattern="^(shid|zara|karkareh)$"
                )
            ],

            ENTERING_WIDTH: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_width
                )
            ],

            ENTERING_HEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_height
                )
            ],
        },

        fallbacks=[
            CommandHandler("start", start)
        ],
    )

    app.add_handler(conv_handler)

    app.add_handler(
        CallbackQueryHandler(
            restart_callback,
            pattern="^restart$"
        )
    )

    print("✅ Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
