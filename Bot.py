import logging

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

# ------------------- تنظیمات -------------------

TOKEN = "8737297309:AAEeKqTkaOidugY_D7fpgN0SPY_e6gflmhs"

PRODUCTS = {
    "shid_simple": {
        "name": "پرده شید ساده",
        "price": 1980000,
        "min_height_cm": 200,
        "min_area": 2,
    },

    "shid_blackout": {
        "name": "پرده شید بلک اوت",
        "price": 3350000,
        "min_height_cm": 200,
        "min_area": 2,
    },

    "zebra": {
        "name": "پرده زبرا",
        "price": 2325000,
        "min_height_cm": 150,
        "min_area": 1.5,
    },

    "metal": {
        "name": "پرده کرکره فلزی",
        "price": 2970000,
        "min_height_cm": 0,
        "min_area": 1.5,
    },
}

MAIN_MENU, SELECT_PRODUCT, GET_WIDTH, GET_HEIGHT = range(4)

# ------------------- منوی دائمی -------------------

reply_menu = ReplyKeyboardMarkup(
    [
        ["📍 آدرس تماس با ما"],
        ["🕒 ساعات کاری"],
        ["📞 شماره تماس"],
        ["🌐 وب سایت خرید آنلاین"],
        ["💡 راهنمایی و پیشنهاد نوع پرده"],
    ],
    resize_keyboard=True
)

# ------------------- استارت -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🎨 به ربات مجموعه هُنری فارس گالری خوش آمدید

میتوانید برای استعلام قیمت پرده و همچنین ثبت سفارش از این ربات استفاده کنید.
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

    await update.message.reply_text(
        text,
        reply_markup=reply_menu
    )

    await update.message.reply_text(
        "یکی از گزینه ها را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return MAIN_MENU

# ------------------- منوی ثابت -------------------

async def menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "📍 آدرس تماس با ما":

        await update.message.reply_text(
            "شیراز خیابان قصردشت چهارراه عفیف آباد ابتدای آوینی نبش کوچه یک\n"
            "مجموعه گالری هنری ایران دکوراسیون (فارس گالری)"
        )

    elif text == "📞 شماره تماس":

        await update.message.reply_text(
            "07136277172"
        )

    elif text == "🕒 ساعات کاری":

        await update.message.reply_text(
            "صبح 09:00 تا 13:00\n"
            "عصر 17:00 تا 21:00"
        )

    elif text == "🌐 وب سایت خرید آنلاین":

        await update.message.reply_text(
            "www.FarsGallery.com"
        )

    elif text == "💡 راهنمایی و پیشنهاد نوع پرده":

        keyboard = [
            [
                InlineKeyboardButton(
                    "اداری و تجاری",
                    callback_data="office"
                )
            ],

            [
                InlineKeyboardButton(
                    "مسکونی",
                    callback_data="home"
                )
            ],
        ]

        await update.message.reply_text(
            "کاربری مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ------------------- منوی اصلی -------------------

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "price":

        keyboard = [
            [
                InlineKeyboardButton(
                    "پرده شید ساده",
                    callback_data="shid_simple"
                )
            ],

            [
                InlineKeyboardButton(
                    "پرده شید بلک اوت",
                    callback_data="shid_blackout"
                )
            ],

            [
                InlineKeyboardButton(
                    "پرده زبرا",
                    callback_data="zebra"
                )
            ],

            [
                InlineKeyboardButton(
                    "پرده کرکره فلزی",
                    callback_data="metal"
                )
            ],
        ]

        await query.message.reply_text(
            "نوع پرده را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SELECT_PRODUCT

    elif query.data == "order":

        keyboard = [
            [
                InlineKeyboardButton(
                    "پرده شید ساده",
                    callback_data="order_shid_simple"
                )
            ],

            [
                InlineKeyboardButton(
                    "پرده شید بلک اوت",
                    callback_data="order_shid_blackout"
                )
            ],

            [
                InlineKeyboardButton(
                    "پرده زبرا",
                    callback_data="order_zebra"
                )
            ],

            [
                InlineKeyboardButton(
                    "پرده کرکره فلزی",
                    callback_data="order_metal"
                )
            ],
        ]

        await query.message.reply_text(
            "چه نوع پرده ای میخواهید؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ------------------- ثبت سفارش -------------------

async def order_links(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    links = {

        "order_shid_simple":
        "پرده شید ساده (پیشنهاد ما برای مسکونی)\n\n"
        "https://FarsGallery.com",

        "order_shid_blackout":
        "پرده شید بلک اوت (پیشنهاد ما برای اداری مخصوصا اتاق کامپیوتر یا ویدیو پروژکتور)\n\n"
        "https://FarsGallery.com",

        "order_zebra":
        "پرده زبرا (پیشنهاد ما برای مسکونی)\n\n"
        "https://FarsGallery.com",

        "order_metal":
        "پرده کرکره فلزی (پیشنهاد ما برای اداری یا تجاری)\n\n"
        "https://FarsGallery.com",
    }

    await query.message.reply_text(
        links[query.data]
    )

# ------------------- پیشنهاد پرده -------------------

async def suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "office":

        keyboard = [
            [
                InlineKeyboardButton(
                    "پرده کرکره فلزی",
                    callback_data="metal"
                )
            ]
        ]

        await query.message.reply_text(
            "پیشنهاد ما برای محیط اداری و تجاری:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SELECT_PRODUCT

    elif query.data == "home":

        keyboard = [
            [
                InlineKeyboardButton(
                    "پرده شید ساده",
                    callback_data="shid_simple"
                )
            ],

            [
                InlineKeyboardButton(
                    "پرده زبرا",
                    callback_data="zebra"
                )
            ],
        ]

        await query.message.reply_text(
            "پیشنهاد ما برای محیط مسکونی:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SELECT_PRODUCT

# ------------------- انتخاب پرده -------------------

async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    context.user_data["product"] = query.data

    await query.message.reply_text(
        "عرض را به سانتیمتر وارد کنید:"
    )

    return GET_WIDTH

# ------------------- دریافت عرض -------------------

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        width_cm = float(update.message.text)

        context.user_data["width_cm"] = width_cm

        await update.message.reply_text(
            "ارتفاع را به سانتیمتر وارد کنید:"
        )

        return GET_HEIGHT

    except:

        await update.message.reply_text(
            "فقط عدد وارد کنید"
        )

        return GET_WIDTH

# ------------------- دریافت ارتفاع و محاسبه -------------------

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        height_cm = float(update.message.text)

        product_key = context.user_data["product"]

        product = PRODUCTS[product_key]

        width_cm = context.user_data["width_cm"]

        # حداقل ارتفاع
        if product["min_height_cm"] > 0:
            if height_cm < product["min_height_cm"]:
                height_cm = product["min_height_cm"]

        width_m = width_cm / 100
        height_m = height_cm / 100

        area = width_m * height_m

        # حداقل متر مربع
        if area < product["min_area"]:
            area = product["min_area"]

        total_price = area * product["price"]

        result = f"""
✅ {product['name']}

📐 عرض:
{width_cm:.0f} سانتیمتر

📏 ارتفاع:
{height_cm:.0f} سانتیمتر

💰 قیمت واحد:
{product['price']:,} تومان

💵 قیمت نهایی:
{total_price:,.0f} تومان
"""

        await update.message.reply_text(result)

        return ConversationHandler.END

    except:

        await update.message.reply_text(
            "فقط عدد وارد کنید"
        )

        return GET_HEIGHT

# ------------------- اجرای ربات -------------------

def main():

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(

        entry_points=[
            CommandHandler("start", start)
        ],

        states={

            MAIN_MENU: [

                CallbackQueryHandler(
                    main_menu,
                    pattern="^(price|order)$"
                ),

                CallbackQueryHandler(
                    suggestion,
                    pattern="^(office|home)$"
                ),

                CallbackQueryHandler(
                    order_links,
                    pattern="^order_"
                ),

                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    menu_buttons
                ),
            ],

            SELECT_PRODUCT: [

                CallbackQueryHandler(
                    select_product,
                    pattern="^(shid_simple|shid_blackout|zebra|metal)$"
                )
            ],

            GET_WIDTH: [

                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_width
                )
            ],

            GET_HEIGHT: [

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

    print("Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
