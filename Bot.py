import logging
import jdatetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

from telegram.error import BadRequest

CHANNEL_USERNAME = '@irandecoration_gallery'

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

TOKEN = "8737297309:AAFS-hg2x4DbTWf0HDrE2Iej7BN5QP2mwqs"

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


async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator","administrator","member"]
    except Exception:
        return False

async def force_join(update, context):
    keyboard=[
        [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("✅ تایید عضویت", callback_data="check_join")]
    ]
    msg="❌ برای استفاده از ربات ابتدا عضو کانال شوید."
    if update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def check_join(update, context):
    query = update.callback_query
    await query.answer()

    if not await is_member(query.from_user.id, context):
        await query.message.reply_text("❌ هنوز عضو کانال نشده‌اید.")
        return ConversationHandler.END

    text = """
🎨 به ربات مجموعه هُنری فــارس گـالری خوش آمدید

✨ میتوانید برای استعلام قیمت پرده و ثبت سفارش از این ربات استفاده کنید.
"""

    keyboard = [
        [InlineKeyboardButton("1️⃣ میخواهم فقط استعلام قیمت پرده بگیرم", callback_data="price")],
        [InlineKeyboardButton("2️⃣ میخواهم ثبت سفارش انجام بدم", callback_data="order")]
    ]

    await query.message.reply_text(text, reply_markup=reply_menu)
    await query.message.reply_text(
        "👇 یکی از گزینه ها را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return MAIN_MENU

# ---------------- استارت ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_member(update.effective_user.id, context):
        await force_join(update, context)
        return ConversationHandler.END

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

        await update.message.reply_text(
            text,
            reply_markup=reply_menu
        )

        await update.message.reply_text(
            "👇 یکی از گزینه ها را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif update.callback_query:

        query = update.callback_query

        await query.answer()

        await query.message.reply_text(
            text,
            reply_markup=reply_menu
        )

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

        await update.message.reply_text(
            "🌐 www.FarsGallery.com"
        )

    elif text == "💡 راهنمایی و پیشنهاد نوع پرده":

        keyboard = [

            [
                InlineKeyboardButton(
                    "🏢 اداری و تجاری",
                    callback_data="office"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 مسکونی",
                    callback_data="home"
                )
            ],
        ]

        await update.message.reply_text(
            "👇 برای چه فضایی میخواهید؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------------- راهنمایی ----------------

async def suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "office":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🏢 پرده کرکره فلزی",
                    callback_data="metal"
                )
            ]
        ]

        await query.message.reply_text(
            "✅ پیشنهاد ما برای فضای اداری و تجاری:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SELECT_PRODUCT

    elif query.data == "home":

        keyboard = [

            [
                InlineKeyboardButton(
                    "🪟 پرده شید ساده",
                    callback_data="shid_simple"
                )
            ],

            [
                InlineKeyboardButton(
                    "🦓 پرده زبرا",
                    callback_data="zebra"
                )
            ],
        ]

        await query.message.reply_text(
            "✅ پیشنهاد ما برای فضای مسکونی:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SELECT_PRODUCT

# ---------------- منوی اصلی ----------------

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "price":

        keyboard = [

            [
                InlineKeyboardButton(
                    "🪟 پرده شید ساده",
                    callback_data="shid_simple"
                )
            ],

            [
                InlineKeyboardButton(
                    "🌑 پرده شید بلک اوت",
                    callback_data="shid_blackout"
                )
            ],

            [
                InlineKeyboardButton(
                    "🦓 پرده زبرا",
                    callback_data="zebra"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏢 پرده کرکره فلزی",
                    callback_data="metal"
                )
            ],
        ]

        await query.message.reply_text(
            "👇 نوع پرده را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SELECT_PRODUCT

    elif query.data == "order":

        keyboard = [

            [
                InlineKeyboardButton(
                    "🪟 پرده شید ساده",
                    callback_data="order_shid_simple"
                )
            ],

            [
                InlineKeyboardButton(
                    "🌑 پرده شید بلک اوت",
                    callback_data="order_shid_blackout"
                )
            ],

            [
                InlineKeyboardButton(
                    "🦓 پرده زبرا",
                    callback_data="order_zebra"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏢 پرده کرکره فلزی",
                    callback_data="order_metal"
                )
            ],
        ]

        await query.message.reply_text(
            "👇 چه نوع پرده ای میخواهید؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return MAIN_MENU

# ---------------- لینک سفارش ----------------

async def order_links(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = {

        "order_shid_simple":
        "🪟 پرده شید ساده\n"
        "🏠 پیشنهاد ما برای مسکونی\n\n"
        "🔗 لینک خرید:\nhttps://farsgallery.com/product-category/curtains/shid/",

        "order_shid_blackout":
        "🌑 پرده شید بلک اوت\n"
        "💻 مناسب اداری و ویدیو پروژکتور\n\n"
        "🔗 لینک خرید:\nhttps://farsgallery.com/product-category/curtains/shid/",

        "order_zebra":
        "🦓 پرده زبرا\n"
        "🏠 پیشنهاد ما برای مسکونی\n\n"
        "🔗 لینک خرید:\nhttps://farsgallery.com/product-category/curtains/zebra/simple/",

        "order_metal":
        "🏢 پرده کرکره فلزی\n"
        "🏬 مناسب اداری و تجاری\n\n"
        "🔗 لینک خرید:\nhttps://farsgallery.com/product-category/curtains/cercere/25mil/",
    }

    await query.message.reply_text(data[query.data])

# ---------------- انتخاب پرده ----------------

async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    context.user_data["product"] = query.data

    await query.message.reply_text(
        "📐 عرض را به سانتیمتر وارد کنید:"
    )

    return GET_WIDTH

# ---------------- عرض ----------------

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text in ["🏠 شروع","💡 راهنمایی و پیشنهاد نوع پرده","🌐 وب سایت خرید آنلاین","🕒 ساعات کاری","📍 آدرس و شماره تماس"]:
        return await menu_handler(update, context)

    try:

        width = float(update.message.text)

        context.user_data["width"] = width

        await update.message.reply_text(
            "📏 ارتفاع را به سانتیمتر وارد کنید:"
        )

        return GET_HEIGHT

    except:

        await update.message.reply_text(
            "❌ فقط عدد وارد کنید"
        )

        return GET_WIDTH

# ---------------- ارتفاع و محاسبه ----------------

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text in ["🏠 شروع","💡 راهنمایی و پیشنهاد نوع پرده","🌐 وب سایت خرید آنلاین","🕒 ساعات کاری","📍 آدرس و شماره تماس"]:
        return await menu_handler(update, context)

    try:

        height = float(update.message.text)

        product_key = context.user_data["product"]

        product = PRODUCTS[product_key]

        width = context.user_data["width"]

        warning_text = ""

        if product["min_height"] > 0:

            if height < product["min_height"]:

                warning_text += (
                    f"\n⚠️ ارتفاع کمتر از "
                    f"{product['min_height']} سانت بود "
                    f"و طبق قوانین همان "
                    f"{product['min_height']} محاسبه شد."
                )

                height = product["min_height"]

        area = (width / 100) * (height / 100)

        if area < product["min_area"]:

            warning_text += (
                f"\n⚠️ متراژ کمتر از "
                f"{product['min_area']} متر مربع بود "
                f"و طبق قوانین همان "
                f"{product['min_area']} محاسبه شد."
            )

            area = product["min_area"]

        total_price = area * product["price"]

        today = jdatetime.date.today().strftime("%Y/%m/%d")

        result = f"""
📅 قیمت امروز
🗓 تاریخ: {today}

{product['name']}

📐 عرض:
{width:.0f} سانتیمتر

📏 ارتفاع:
{height:.0f} سانتیمتر
{warning_text}

🧮 متر مربع:
{area:.2f}

💰 قیمت واحد هر مترمربع:
{product['price']:,} تومان

💵 قیمت نهایی:
{total_price:,.0f} تومان

📦 هر شهری باشی ارسال میکنم
🛡 2 سال ضمانت
🚚 سه روز کاری تحویلت میدم
✨ کیفیت درجه یکه 😍
"""

        keyboard = [

            [
                InlineKeyboardButton(
                    "🎨 رنگ بندی",
                    callback_data=f"color_{product_key}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🛒 میخوای خرید کنی؟",
                    url=product["link"]
                )
            ],

            [
                InlineKeyboardButton(
                    "🔄 شروع دوباره",
                    callback_data="back_start"
                )
            ]
        ]

        await update.message.reply_text(
            result,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return MAIN_MENU

    except:

        await update.message.reply_text(
            "❌ فقط عدد وارد کنید"
        )

        return GET_HEIGHT

# ---------------- رنگ بندی ----------------

async def color_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    product_key = query.data.replace("color_", "")

    colors = PRODUCTS[product_key]["colors"]

    text = "🎨 رنگ بندی موجود:\n\n"

    for color in colors:
        text += f"{color}\n"

    await query.message.reply_text(text)

# ---------------- اجرای ربات ----------------

def main():

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(

        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(check_join, pattern="^check_join$")
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

                CallbackQueryHandler(
                    start,
                    pattern="^back_start$"
                ),

                CallbackQueryHandler(
                    color_handler,
                    pattern="^color_"
                ),

                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    menu_handler
                ),
            ],

            SELECT_PRODUCT: [

                CallbackQueryHandler(
                    select_product,
                    pattern="^(shid_simple|shid_blackout|zebra|metal)$"
                ),
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
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🏠 شروع$"), start)
        ],

        allow_reentry=True,
        per_message=False
    )

    app.add_handler(conv_handler)

    app.add_handler(
        MessageHandler(
            filters.Regex("^🏠 شروع$"),
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            start,
            pattern="^back_start$"
        )
    )


    print("✅ Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
