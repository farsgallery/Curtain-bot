import os
import logging
import jdatetime
from aiohttp import web
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

# ---------------- لاگ ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------- تنظیمات محیطی ----------------
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@irandecoration_gallery")
WEBHOOK_URL = os.environ.get("https://farsgallery-bot.onrender.com")
PORT = int(os.environ.get("PORT", "10000"))

if not TOKEN:
    raise ValueError("8737297309:AAGOejgXoxwlGjG2PdcGxkYtzOWJMNPtZA4")

# ---------------- محصولات ----------------
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
        "colors": ["⚪ سفید", "🌫 طوسی", "🤎 قهوه‌ای"],
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

ORDER_LINKS = {
    "order_shid_simple": "🪟 پرده شید ساده\n\n🔗 لینک خرید:\nhttps://farsgallery.com/product-category/curtains/shid/",
    "order_shid_blackout": "🌑 پرده شید بلک اوت\n💻 مناسب اداری و ویدیو پروژکتور\n\n🔗 لینک خرید:\nhttps://farsgallery.com/product-category/curtains/shid/",
    "order_zebra": "🦓 پرده زبرا\n🏠 پیشنهاد ما برای مسکونی\n\n🔗 لینک خرید:\nhttps://farsgallery.com/product-category/curtains/zebra/simple/",
    "order_metal": "🏢 پرده کرکره فلزی\n🏬 مناسب اداری و تجاری\n\n🔗 لینک خرید:\nhttps://farsgallery.com/product-category/curtains/cercere/25mil/",
}

# ---------------- مراحل مکالمه ----------------
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
    resize_keyboard=True,
)

MENU_KEYS = [
    "🏠 شروع",
    "💡 راهنمایی و پیشنهاد نوع پرده",
    "🌐 وب سایت خرید آنلاین",
    "🕒 ساعات کاری",
    "📍 آدرس و شماره تماس",
]


# ---------------- بررسی عضویت ----------------
async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception as e:
        logger.warning("is_member error: %s", e)
        return False


async def force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("✅ تایید عضویت", callback_data="check_join")],
    ]
    msg = "❌ برای استفاده از ربات ابتدا عضو کانال شوید."
    if update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_member(query.from_user.id, context):
        await query.message.reply_text("❌ هنوز عضو کانال نشده‌اید.")
        return ConversationHandler.END

    await show_main_menu(query.message, context)
    return MAIN_MENU


# ---------------- نمایش منوی اصلی ----------------
async def show_main_menu(message, context: ContextTypes.DEFAULT_TYPE):
    text = """
🎨 به ربات مجموعه هُنری فــارس گـالری خوش آمدید

✨ می‌توانید برای استعلام قیمت پرده و ثبت سفارش از این ربات استفاده کنید.
"""
    keyboard = [
        [InlineKeyboardButton("1️⃣ میخواهم فقط استعلام قیمت پرده بگیرم", callback_data="price")],
        [InlineKeyboardButton("2️⃣ میخواهم ثبت سفارش انجام بدم", callback_data="order")],
    ]
    await message.reply_text(text, reply_markup=reply_menu)
    await message.reply_text("👇 یکی از گزینه‌ها را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))


# ---------------- استارت ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_member(user_id, context):
        await force_join(update, context)
        return ConversationHandler.END

    target_msg = update.message or update.callback_query.message
    await show_main_menu(target_msg, context)
    return MAIN_MENU


# ---------------- منوی دکمه‌های ثابت ----------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🏠 شروع":
        return await start(update, context)

    if text == "📍 آدرس و شماره تماس":
        await update.message.reply_text(
            "📍 شیراز خیابان قصردشت چهارراه عفیف آباد "
            "ابتدای بلوار آوینی نبش کوچه یک\n\n"
            "🏢 مجموعه گالری هنری ایران دکوراسیون (فارس گالری)\n\n"
            "📞 07136277172"
        )

    elif text == "🕒 ساعات کاری":
        await update.message.reply_text("🕒 صبح 09:00 تا 13:00\n🌙 عصر 17:00 تا 21:00")

    elif text == "🌐 وب سایت خرید آنلاین":
        await update.message.reply_text("🌐 www.FarsGallery.com")

    elif text == "💡 راهنمایی و پیشنهاد نوع پرده":
        keyboard = [
            [InlineKeyboardButton("🏢 اداری و تجاری", callback_data="office")],
            [InlineKeyboardButton("🏠 مسکونی", callback_data="home")],
        ]
        await update.message.reply_text(
            "👇 برای چه فضایی می‌خواهید؟",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ---------------- راهنمای اداری/مسکونی ----------------
async def suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "office":
        keyboard = [
            [InlineKeyboardButton("🪟 پرده شید ساده", callback_data="shid_simple")],
            [InlineKeyboardButton("🌑 پرده شید بلک اوت", callback_data="shid_blackout")],
            [InlineKeyboardButton("🏢 پرده کرکره فلزی", callback_data="metal")],
        ]
        await query.message.reply_text(
            "🏢 برای فضای اداری پیشنهاد ما:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif query.data == "home":
        keyboard = [
            [InlineKeyboardButton("🦓 پرده زبرا", callback_data="zebra")],
            [InlineKeyboardButton("🪟 پرده شید ساده", callback_data="shid_simple")],
        ]
        await query.message.reply_text(
            "🏠 برای فضای مسکونی پیشنهاد ما:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ---------------- انتخاب نوع درخواست (استعلام/سفارش) ----------------
async def main_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "price":
        keyboard = [
            [InlineKeyboardButton("🪟 پرده شید ساده", callback_data="shid_simple")],
            [InlineKeyboardButton("🌑 پرده شید بلک اوت", callback_data="shid_blackout")],
            [InlineKeyboardButton("🦓 پرده زبرا", callback_data="zebra")],
            [InlineKeyboardButton("🏢 پرده کرکره فلزی", callback_data="metal")],
        ]
        await query.message.reply_text(
            "👇 نوع پرده را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SELECT_PRODUCT

    elif query.data == "order":
        keyboard = [
            [InlineKeyboardButton("🪟 پرده شید ساده", callback_data="order_shid_simple")],
            [InlineKeyboardButton("🌑 پرده شید بلک اوت", callback_data="order_shid_blackout")],
            [InlineKeyboardButton("🦓 پرده زبرا", callback_data="order_zebra")],
            [InlineKeyboardButton("🏢 پرده کرکره فلزی", callback_data="order_metal")],
        ]
        await query.message.reply_text(
            "👇 چه نوع پرده‌ای می‌خواهید؟",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return MAIN_MENU


# ---------------- لینک سفارش ----------------
async def order_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in ORDER_LINKS:
        await query.message.reply_text(ORDER_LINKS[query.data])


# ---------------- انتخاب پرده برای استعلام ----------------
async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["product"] = query.data
    await query.message.reply_text("📐 عرض را به سانتیمتر وارد کنید:")
    return GET_WIDTH


# ---------------- دریافت عرض ----------------
async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_KEYS:
        return await menu_handler(update, context)

    try:
        width = float(update.message.text)
        if width <= 0:
            raise ValueError
        context.user_data["width"] = width
        await update.message.reply_text("📏 ارتفاع را به سانتیمتر وارد کنید:")
        return GET_HEIGHT
    except Exception:
        await update.message.reply_text("❌ فقط عدد مثبت وارد کنید (مثلاً 150)")
        return GET_WIDTH


# ---------------- دریافت ارتفاع و محاسبه ----------------
async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_KEYS:
        return await menu_handler(update, context)

    try:
        height = float(update.message.text)
        if height <= 0:
            raise ValueError

        product_key = context.user_data.get("product")
        product = PRODUCTS[product_key]
        width = context.user_data["width"]

        warning_text = ""

        if product["min_height"] > 0 and height < product["min_height"]:
            warning_text += (
                f"\n⚠️ ارتفاع کمتر از {product['min_height']} سانت بود "
                f"و طبق قوانین همان {product['min_height']} محاسبه شد."
            )
            height = product["min_height"]

        area = (width / 100) * (height / 100)

        if area < product["min_area"]:
            warning_text += (
                f"\n⚠️ متراژ کمتر از {product['min_area']} متر مربع بود "
                f"و طبق قوانین همان {product['min_area']} محاسبه شد."
            )
            area = product["min_area"]

        total_price = area * product["price"]
        today = jdatetime.date.today().strftime("%Y/%m/%d")

        result = f"""
📅 قیمت امروز
🗓 تاریخ: {today}

{product['name']}

📐 عرض: {width:.0f} سانتیمتر
📏 ارتفاع: {height:.0f} سانتیمتر
{warning_text}

🧮 متر مربع: {area:.2f}

💰 قیمت واحد هر مترمربع: {product['price']:,} تومان
💵 قیمت نهایی: {total_price:,.0f} تومان

📦 هر شهری باشی ارسال می‌کنم
🛡 2 سال ضمانت
🚚 سه روز کاری تحویلت میدم
✨ کیفیت درجه یکه 😍
"""

        keyboard = [
            [InlineKeyboardButton("🎨 رنگ بندی", callback_data=f"color_{product_key}")],
            [InlineKeyboardButton("🛒 میخوای خرید کنی؟", url=product["link"])],
            [InlineKeyboardButton("🔄 شروع دوباره", callback_data="back_start")],
        ]
        await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(keyboard))
        return MAIN_MENU

    except Exception:
        await update.message.reply_text("❌ فقط عدد مثبت وارد کنید (مثلاً 200)")
        return GET_HEIGHT


# ---------------- نمایش رنگ‌بندی ----------------
async def color_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_key = query.data.replace("color_", "")
    if product_key not in PRODUCTS:
        return
    colors = PRODUCTS[product_key]["colors"]
    text = "🎨 رنگ بندی موجود:\n\n" + "\n".join(colors)
    await query.message.reply_text(text)


# ---------------- بازگشت به استارت ----------------
async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_main_menu(query.message, context)
    return MAIN_MENU


# ---------------- مدیریت خطای عمومی ----------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)


# ---------------- تنظیم Webhook روی aiohttp ----------------
async def webhook_handler(request: web.Request):
    application = request.app["application"]
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        return web.Response(text="ok")
    except Exception as e:
        logger.exception("webhook error: %s", e)
        return web.Response(status=400, text="bad request")


async def health_handler(request: web.Request):
    return web.Response(text="Bot is running ✅")


async def on_startup(app: web.Application):
    application = app["application"]
    webhook_path = f"/{TOKEN}"
    if WEBHOOK_URL:
        full_url = f"{WEBHOOK_URL.rstrip('/')}{webhook_path}"
        await application.bot.set_webhook(url=full_url, allowed_updates=Update.ALL_TYPES)
        logger.info("Webhook set to: %s", full_url)
    else:
        logger.warning("WEBHOOK_URL not set - webhook not configured")


async def on_shutdown(app: web.Application):
    application = app["application"]
    await application.bot.delete_webhook()
    await application.shutdown()


# ---------------- ساخت اپلیکیشن ----------------
def build_application() -> Application:
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(check_join, pattern="^check_join$"),
            CallbackQueryHandler(back_to_start, pattern="^back_start$"),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_choice, pattern="^(price|order)$"),
                CallbackQueryHandler(suggestion, pattern="^(office|home)$"),
                CallbackQueryHandler(order_link_handler, pattern="^order_"),
                CallbackQueryHandler(color_handler, pattern="^color_"),
                CallbackQueryHandler(back_to_start, pattern="^back_start$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler),
            ],
            SELECT_PRODUCT: [
                CallbackQueryHandler(select_product, pattern="^(shid_simple|shid_blackout|zebra|metal)$"),
            ],
            GET_WIDTH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_width),
            ],
            GET_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_height),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    return app


# ---------------- اجرای اصلی ----------------
def main():
    application = build_application()

    web_app = web.Application()
    web_app["application"] = application
    web_app.router.add_post(f"/{TOKEN}", webhook_handler)
    web_app.router.add_get("/", health_handler)
    web_app.router.add_get("/health", health_handler)

    web_app.on_startup.append(on_startup)
    web_app.on_shutdown.append(on_shutdown)

    logger.info("Starting aiohttp server on port %s", PORT)
    web.run_app(web_app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
