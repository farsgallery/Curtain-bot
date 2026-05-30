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

ADMIN_ID = 333050909  # 👈 آیدی عددی خودت

# ---------------- DATABASE ----------------

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product TEXT,
    area REAL,
    price REAL,
    date TEXT
)
""")

conn.commit()


def save_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()


def save_order(user_id, product, area, price):
    cur.execute(
        "INSERT INTO orders (user_id, product, area, price, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, product, area, price, str(jdatetime.date.today()))
    )
    conn.commit()


def get_stats():
    users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    orders = cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    return users, orders


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

MAIN_MENU, SELECT_PRODUCT, GET_WIDTH, GET_HEIGHT = range(4)

# ---------------- منو ----------------

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

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user.id)

    text = """
🎨 خوش آمدید
"""

    keyboard = [
        [InlineKeyboardButton("استعلام قیمت", callback_data="price")],
        [InlineKeyboardButton("ثبت سفارش", callback_data="order")],
    ]

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_menu)
        await update.message.reply_text("👇 انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    return MAIN_MENU


# ---------------- MENU ----------------

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🏠 شروع":
        return await start(update, context)

    elif text == "📍 آدرس و شماره تماس":
        await update.message.reply_text("📞 07136277172")

    elif text == "🕒 ساعات کاری":
        await update.message.reply_text("09-13 / 17-21")

    elif text == "🌐 وب سایت خرید آنلاین":
        await update.message.reply_text("www.FarsGallery.com")

    elif text == "💡 راهنمایی و پیشنهاد نوع پرده":
        keyboard = [
            [InlineKeyboardButton("اداری", callback_data="office")],
            [InlineKeyboardButton("مسکونی", callback_data="home")],
        ]
        await update.message.reply_text("نوع فضا؟", reply_markup=InlineKeyboardMarkup(keyboard))


# ---------------- GET HEIGHT ----------------

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        height = float(update.message.text)

        product_key = context.user_data["product"]
        product = PRODUCTS[product_key]
        width = context.user_data["width"]

        area = (width / 100) * (height / 100)

        if area < product["min_area"]:
            area = product["min_area"]

        total_price = area * product["price"]

        save_order(
            update.effective_user.id,
            product["name"],
            area,
            total_price
        )

        today = jdatetime.date.today()

        result = f"""
📅 {today}

{product['name']}

💰 قیمت کل: {total_price:,.0f}
"""

        keyboard = [
            [InlineKeyboardButton("🛒 خرید", url=product["link"])],
            [InlineKeyboardButton("🔄 شروع دوباره", callback_data="back_start")]
        ]

        await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(keyboard))

        return MAIN_MENU

    except:
        await update.message.reply_text("عدد وارد کن")
        return GET_HEIGHT


# ---------------- STATS ----------------

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    users, orders = get_stats()

    await update.message.reply_text(
        f"👥 کاربران: {users}\n📦 سفارش‌ها: {orders}"
    )


# ---------------- MAIN ----------------

def main():

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(

        entry_points=[CommandHandler("start", start)],

        states={

            MAIN_MENU: [
                CallbackQueryHandler(menu_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler),
            ],

            SELECT_PRODUCT: [],

            GET_WIDTH: [],
            GET_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_height),
            ],
        },

        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stats", stats))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
