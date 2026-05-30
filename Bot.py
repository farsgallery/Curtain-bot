# -*- coding: utf-8 -*-

import logging
import jdatetime
import sqlite3

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = "8737297309:AAFEl8XdfWGQb_iNYjuSjido1Tgeo2XL-hA"

# 🔐 آیدی ادمین (حتماً جایگزین کن)
ADMIN_ID = 333050909

# ---------------- دیتابیس ----------------

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_seen TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product TEXT,
    area REAL,
    total_price REAL,
    date TEXT
)
""")

conn.commit()

def save_user(user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, first_seen) VALUES (?, ?)",
            (user_id, str(jdatetime.date.today()))
        )
        conn.commit()

def save_order(user_id, product, area, total):
    cursor.execute(
        "INSERT INTO orders (user_id, product, area, total_price, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, product, area, total, str(jdatetime.date.today()))
    )
    conn.commit()

# ---------------- تنظیمات پرده ----------------

PRODUCTS = {

    "shid_simple": {
        "name": "🪟 پرده شید ساده",
        "price": 1980000,
        "min_height": 200,
        "min_area": 2,
        "colors": ["⚪ سفید", "🌫 طوسی", "🟤 کرم"],
        "link": "https://farsgallery.com/product-category/curtains/shid/",
    },

    "shid_blackout": {
        "name": "🌑 پرده شید بلک اوت",
        "price": 3350000,
        "min_height": 200,
        "min_area": 2,
        "colors": ["⚪ سفید", "🌫 طوسی", "🟤 کرم"],
        "link": "https://farsgallery.com/product-category/curtains/shid/",
    },

    "zebra": {
        "name": "🦓 پرده زبرا",
        "price": 2325000,
        "min_height": 150,
        "min_area": 1.5,
        "colors": ["⚪ سفید", "🌫 طوسی", "🤎 قهوه ای"],
        "link": "https://farsgallery.com/product-category/curtains/zebra/simple/",
    },

    "metal": {
        "name": "🏢 پرده کرکره فلزی",
        "price": 2970000,
        "min_height": 0,
        "min_area": 1.5,
        "colors": ["⚪ سفید", "🌫 طوسی", "⚫ مشکی"],
        "link": "https://farsgallery.com/product-category/curtains/cercere/25mil/",
    },
}

# ---------------- مراحل ----------------

MAIN_MENU, SELECT_PRODUCT, GET_WIDTH, GET_HEIGHT = range(4)

# ---------------- منوی دائمی ----------------

reply_menu = ReplyKeyboardMarkup(
    [
        ["🏠 شروع"],
        ["💡 راهنمایی و پیشنهاد نوع پرده"],
        ["🌐 وب سایت خرید آنلاین"],
        ["🕒 ساعات کاری"],
        ["📍 آدرس و شماره تماس"],
    ],
    resize_keyboard=True
)

# ---------------- استارت ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    save_user(user_id)

    text = """
🎨 به ربات مجموعه هُنری فــارس گـالری خوش آمدید

✨ میتوانید برای استعلام قیمت پرده و ثبت سفارش از این ربات استفاده کنید.
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "1️⃣ میخواهم فقط استعلام قیمت پرده بگیرم",
                callback_data="price"
            )
        ],
        [
            InlineKeyboardButton(
                "2️⃣ میخواهم ثبت سفارش انجام بدم",
                callback_data="order"
            )
        ],
    ]

    if update.message:

        await update.message.reply_text(text, reply_markup=reply_menu)

        await update.message.reply_text(
            "👇 یکی از گزینه ها را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif update.callback_query:

        query = update.callback_query
        await query.answer()

        await query.message.reply_text(text, reply_markup=reply_menu)

        await query.message.reply_text(
            "👇 یکی از گزینه ها را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return MAIN_MENU

# ---------------- منوی ثابت ----------------

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🏠 شروع":
        return await start(update, context)

    elif text == "📍 آدرس و شماره تماس":

        await update.message.reply_text(
            "📍 شیراز خیابان قصردشت چهارراه عفیف آباد "
            "ابتدای بلوار آوینی نبش کوچه یک\n\n"
            "🏢 مجموعه گالری هنری ایران دکوراسیون (فارس گالری)\n\n"
            "📞 07136277172"
        )

    elif text == "🕒 ساعات کاری":

        await update.message.reply_text(
            "🕒 صبح 09:00 تا 13:00\n"
            "🌙 عصر 17:00 تا 21:00"
        )

    elif text == "🌐 وب سایت خرید آنلاین":

        await update.message.reply_text("🌐 www.FarsGallery.com")

    elif text == "💡 راهنمایی و پیشنهاد نوع پرده":

        keyboard = [
            [
                InlineKeyboardButton("🏢 اداری و تجاری", callback_data="office")
            ],
            [
                InlineKeyboardButton("🏠 مسکونی", callback_data="home")
            ],
        ]

        await update.message.reply_text(
            "👇 برای چه فضایی میخواهید؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------------- آمار ----------------

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    orders = cursor.fetchone()[0]

    await update.message.reply_text(
        f"📊 آمار ربات\n\n"
        f"👤 کاربران: {users}\n"
        f"🧾 سفارش‌ها: {orders}"
    )

# ---------------- محاسبه قیمت + ذخیره سفارش ----------------

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        height = float(update.message.text)

        product_key = context.user_data["product"]
        product = PRODUCTS[product_key]

        width = context.user_data["width"]

        if product["min_height"] > 0 and height < product["min_height"]:
            height = product["min_height"]

        area = (width / 100) * (height / 100)

        if area < product["min_area"]:
            area = product["min_area"]

        total_price = area * product["price"]

        # 💾 ذخیره سفارش
        save_order(update.effective_user.id, product_key, area, total_price)

        today = jdatetime.date.today().strftime("%Y/%m/%d")

        result = f"""
📅 قیمت امروز
🗓 تاریخ: {today}

{product['name']}

🧮 متر مربع: {area:.2f}

💰 قیمت واحد: {product['price']:,}

💵 قیمت نهایی: {total_price:,.0f} تومان
"""

        keyboard = [
            [
                InlineKeyboardButton("🛒 خرید", url=product["link"])
            ],
            [
                InlineKeyboardButton("🔄 شروع دوباره", callback_data="back_start")
            ]
        ]

        await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(keyboard))

        return MAIN_MENU

    except:
        await update.message.reply_text("❌ فقط عدد وارد کنید")
        return GET_HEIGHT

# ---------------- اجرای ربات ----------------

def main():

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(

        entry_points=[CommandHandler("start", start)],

        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)
            ],
            SELECT_PRODUCT: [],
            GET_WIDTH: [],
            GET_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)
            ],
        },

        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv_handler)

    # 📊 stats
    app.add_handler(CommandHandler("stats", stats))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
