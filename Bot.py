import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)

TOKEN = "توکن_ربات"

# ---------------- محصولات ----------------

PRODUCTS = {
    "shid_simple": {
        "name": "🪟 پرده شید ساده",
        "price": 1980000,
        "min_h": 200,
        "min_a": 2,
        "colors": ["⚪ سفید", "🌫 طوسی", "🟤 کرم"],
    },
    "shid_blackout": {
        "name": "🌑 پرده شید بلک اوت",
        "price": 3350000,
        "min_h": 200,
        "min_a": 2,
        "colors": ["⚪ سفید", "🌫 طوسی", "🟤 کرم"],
    },
    "zebra": {
        "name": "🦓 پرده زبرا",
        "price": 2325000,
        "min_h": 150,
        "min_a": 1.5,
        "colors": ["⚪ سفید", "🌫 طوسی", "🤎 قهوه‌ای"],
    },
    "metal": {
        "name": "🏢 پرده کرکره فلزی",
        "price": 2970000,
        "min_h": 0,
        "min_a": 1.5,
        "colors": ["⚪ سفید", "🌫 طوسی", "⚫ مشکی"],
    },
}

# ---------------- مراحل ----------------

GET_WIDTH, GET_HEIGHT = range(2)

# ---------------- منوی ثابت ----------------

MENU = ReplyKeyboardMarkup(
    [
        ["📍 آدرس", "📞 تماس"],
        ["🕒 ساعات کاری", "🌐 سایت"],
        ["💡 راهنمایی نوع پرده"],
    ],
    resize_keyboard=True
)

# ---------------- استارت ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💰 استعلام قیمت", callback_data="price")],
        [InlineKeyboardButton("🛒 ثبت سفارش", callback_data="order")],
    ]

    await update.message.reply_text(
        "🎨 به فارس گالری خوش آمدید",
        reply_markup=MENU
    )

    await update.message.reply_text(
        "👇 انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- همه دکمه‌ها (بدون قفل شدن) ----------------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # شروع استعلام
    if data == "price":

        keyboard = [
            [InlineKeyboardButton("شید ساده", callback_data="p_shid_simple")],
            [InlineKeyboardButton("شید بلک اوت", callback_data="p_shid_blackout")],
            [InlineKeyboardButton("زبرا", callback_data="p_zebra")],
            [InlineKeyboardButton("کرکره فلزی", callback_data="p_metal")],
        ]

        await query.message.reply_text(
            "نوع پرده را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # سفارش
    elif data == "order":

        await query.message.reply_text(
            "🛒 برای ثبت سفارش وارد سایت شوید:\nhttps://FarsGallery.com"
        )

    # انتخاب پرده برای قیمت
    elif data.startswith("p_"):

        product = data.replace("p_", "")
        context.user_data["product"] = product

        await query.message.reply_text("📐 عرض (سانتیمتر):")

    # رنگ‌ها
    elif data.startswith("color"):

        p = context.user_data.get("product")
        colors = PRODUCTS[p]["colors"]

        await query.message.reply_text("🎨 رنگ‌ها:\n" + "\n".join(colors))

    # برگشت
    elif data == "back":

        await start(update, context)

# ---------------- دریافت عرض ----------------

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        width = float(update.message.text)
        context.user_data["width"] = width

        await update.message.reply_text("📏 ارتفاع (سانتیمتر):")
        return GET_HEIGHT

    except:
        await update.message.reply_text("فقط عدد وارد کن")
        return GET_WIDTH

# ---------------- دریافت ارتفاع + محاسبه ----------------

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        height = float(update.message.text)

        key = context.user_data["product"]
        p = PRODUCTS[key]

        width = context.user_data["width"]

        # اصلاح قوانین (بدون نمایش پیچیدگی)
        if height < p["min_h"]:
            height = p["min_h"]

        area = (width / 100) * (height / 100)

        if area < p["min_a"]:
            area = p["min_a"]

        total = area * p["price"]

        await update.message.reply_text(
            f"""
{p['name']}

📐 عرض: {width} cm
📏 ارتفاع: {height} cm
📊 متر مربع: {area:.2f}

💰 قیمت واحد: {p['price']:,}
💵 قیمت نهایی: {total:,.0f}

🚚 تحویل 3 روزه
🛡 2 سال ضمانت
"""
        )

        keyboard = [
            [InlineKeyboardButton("🎨 رنگ‌ها", callback_data="color")],
            [InlineKeyboardButton("🔄 محاسبه دوباره", callback_data="price")],
            [InlineKeyboardButton("🏠 شروع", callback_data="back")],
        ]

        await update.message.reply_text(
            "👇 ادامه:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ConversationHandler.END

    except:
        await update.message.reply_text("فقط عدد وارد کن")
        return GET_HEIGHT

# ---------------- اجرا ----------------

def main():

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(

        entry_points=[CommandHandler("start", start)],

        states={
            GET_WIDTH: [MessageHandler(filters.TEXT, get_width)],
            GET_HEIGHT: [MessageHandler(filters.TEXT, get_height)],
        },

        fallbacks=[],
    )

    app.add_handler(conv)

    # خیلی مهم: همه دکمه‌ها اینجا
    app.add_handler(CallbackQueryHandler(buttons))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
