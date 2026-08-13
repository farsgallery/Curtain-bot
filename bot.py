import os, logging, math
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fars-gallery")

PRODUCTS = {
    "shade": {
        "name": "پرده شید ساده",
        "price": 1_980_000,
        "min_h": 2.0, "min_area": 2.0,
        "colors": ["سفید", "طوسی", "کرم"],
    },
    "blackout": {
        "name": "پرده شید بلک اوت",
        "price": 3_350_000,
        "min_h": 2.0, "min_area": 2.0,
        "colors": ["سفید", "طوسی", "کرم"],
    },
    "zebra": {
        "name": "پرده زبرا",
        "price": 2_325_000,
        "min_h": 1.5, "min_area": 1.5,
        "colors": ["سفید", "طوسی", "قهوه‌ای"],
    },
    "metal": {
        "name": "پرده کرکره فلزی",
        "price": 2_970_000,
        "min_h": None, "min_area": 1.5,
        "colors": ["سفید", "طوسی", "مشکی"],
    },
}

def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("💰 استعلام قیمت پرده")],
            [KeyboardButton("🛒 ثبت سفارش")],
            [KeyboardButton("💡 راهنمایی و پیشنهاد نوع پرده")],
            [KeyboardButton("📍 آدرس و تماس با ما"), KeyboardButton("🕘 ساعات کاری")],
            [KeyboardButton("🌐 وب‌سایت خرید آنلاین")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

def product_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪟 پرده شید ساده", callback_data="p:shade")],
        [InlineKeyboardButton("🌑 پرده شید بلک اوت", callback_data="p:blackout")],
        [InlineKeyboardButton("🟫 پرده زبرا", callback_data="p:zebra")],
        [InlineKeyboardButton("🪟 پرده کرکره فلزی", callback_data="p:metal")],
    ])

def yes_color_keyboard(key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 آره، رنگ‌بندی رو بگو", callback_data=f"colors:{key}")]
    ])

def colors_keyboard(key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(c, callback_data=f"color:{key}:{i}")]
        for i, c in enumerate(PRODUCTS[key]["colors"])
    ])

def calc_repeat_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 دوباره محاسبه کن", callback_data="again")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")],
    ])

def order_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪟 شید ساده — پیشنهاد ما برای مسکونی", callback_data="order:shade")],
        [InlineKeyboardButton("🌑 شید بلک اوت — مناسب اداری/پروژکتور", callback_data="order:blackout")],
        [InlineKeyboardButton("🟫 زبرا — پیشنهاد ما برای مسکونی", callback_data="order:zebra")],
        [InlineKeyboardButton("🪟 کرکره فلزی — اداری/تجاری", callback_data="order:metal")],
    ])

ORDER_LINKS = {
    "shade": os.getenv("ORDER_SHADE_URL", ""),
    "blackout": os.getenv("ORDER_BLACKOUT_URL", ""),
    "zebra": os.getenv("ORDER_ZEBRA_URL", ""),
    "metal": os.getenv("ORDER_METAL_URL", ""),
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "به ربات مجموعه هنری فارس گالری خوش آمدید 🌹\n\n"
        "می‌توانید برای استعلام قیمت بر اساس ابعاد پرده و همچنین ثبت سفارش از این ربات استفاده کنید:",
        reply_markup=main_menu()
    )

async def price_menu(update, context):
    await update.message.reply_text("🧾 نوع پرده را انتخاب کنید:", reply_markup=product_keyboard())

async def ask_dimensions(query, context, key):
    context.user_data["product"] = key
    context.user_data["step"] = "width"
    p = PRODUCTS[key]
    await query.message.reply_text(
        f"📐 {p['name']}\n\nعرض پرده را به سانتی‌متر وارد کنید:"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    step = context.user_data.get("step")

    if text in ("🏠 منوی اصلی", "/start"):
        return await start(update, context)
    if text == "💰 استعلام قیمت پرده":
        return await price_menu(update, context)
    if text == "🛒 ثبت سفارش":
        return await update.message.reply_text("🛒 نوع پرده مورد نظر را انتخاب کنید:", reply_markup=order_keyboard())
    if text == "💡 راهنمایی و پیشنهاد نوع پرده":
        context.user_data["step"] = "usage"
        return await update.message.reply_text(
            "💡 پرده را برای چه کاربری می‌خواهید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏢 اداری و تجاری", callback_data="usage:office")],
                [InlineKeyboardButton("🏠 مسکونی", callback_data="usage:home")],
            ])
        )
    if text == "📍 آدرس و تماس با ما":
        return await update.message.reply_text(
            "📍 آدرس تماس با ما:\nشیراز، خیابان قصردشت، چهارراه عفیف‌آباد، ابتدای بلوار آوینی، نبش کوچه یک، مجموعه گالری هنری ایران دکوراسیون (فارس گالری)\n\n"
            "📞 شماره تماس: 07136277172"
        )
    if text == "🕘 ساعات کاری":
        return await update.message.reply_text("🕘 ساعات کاری:\nصبح 09:00 تا 13:00\nعصر 17:00 تا 21:00")
    if text == "🌐 وب‌سایت خرید آنلاین":
        url = os.getenv("WEBSITE_URL", "")
        return await update.message.reply_text(f"🌐 وب‌سایت خرید آنلاین:\n{url}" if url else "🌐 لینک وب‌سایت در تنظیمات ربات ثبت نشده است.")

    if step in ("width", "height"):
        try:
            value = float(text.replace(",", ".").replace("،", "."))
            if value <= 0:
                raise ValueError
        except ValueError:
            return await update.message.reply_text("⚠️ لطفاً فقط عدد معتبر وارد کنید.")
        if step == "width":
            context.user_data["width_cm"] = value
            context.user_data["step"] = "height"
            return await update.message.reply_text("📏 حالا ارتفاع پرده را به سانتی‌متر وارد کنید:")
        context.user_data["height_cm"] = value
        return await calculate(update, context)

async def calculate(update, context):
    key = context.user_data["product"]
    p = PRODUCTS[key]
    width_cm = context.user_data["width_cm"]
    raw_h_cm = context.user_data["height_cm"]

    width_m = width_cm / 100
    raw_h_m = raw_h_cm / 100
    h_m = max(raw_h_m, p["min_h"]) if p["min_h"] else raw_h_m
    raw_area = width_m * h_m
    area = max(raw_area, p["min_area"])

    price = round(area * p["price"])
    notes = []
    if p["min_h"] and raw_h_m < p["min_h"]:
        notes.append(f"📌 به خاطر قانون {p['name']}، ارتفاع کمتر از {p['min_h']*100:.0f} سانتی‌متر، {p['min_h']*100:.0f} در نظر گرفته شد.")
    if raw_area < p["min_area"]:
        notes.append(f"📌 به خاطر قانون {p['name']}، متراژ کمتر از {p['min_area']} مترمربع، {p['min_area']} مترمربع در نظر گرفته شد.")

    msg = (
        f"✅ محاسبه قیمت {p['name']}\n\n"
        f"📐 عرض: {width_cm:g} سانتی‌متر\n"
        f"📏 ارتفاع: {h_m*100:g} سانتی‌متر\n"
        f"📊 متر مربع: {area:.2f}\n"
        f"💵 قیمت واحد: {p['price']:,.0f} تومان\n"
        f"💰 قیمت نهایی: {price:,.0f} تومان\n\n"
    )
    if notes:
        msg += "\n".join(notes) + "\n\n"
    msg += "🚚 سه روز کاری تحویلت میدم و هر شهری هم که باشی ارسال می‌کنم.\n"
    msg += "🛡️ ۲ سال هم ضمانتش می‌کنم و کیفیتشم که درجه یکه دیگه چی می‌خوای 😍❤️"
    context.user_data["step"] = "done"
    await update.message.reply_text(msg, reply_markup=yes_color_keyboard(key))

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("p:"):
        return await ask_dimensions(q, context, data.split(":", 1)[1])
    if data == "again":
        context.user_data["step"] = None
        return await q.message.reply_text("🧾 نوع پرده را انتخاب کنید:", reply_markup=product_keyboard())
    if data == "home":
        context.user_data.clear()
        return await q.message.reply_text("🏠 منوی اصلی:", reply_markup=main_menu())
    if data.startswith("colors:"):
        key = data.split(":")[1]
        return await q.message.reply_text("🎨 رنگ‌بندی:", reply_markup=colors_keyboard(key))
    if data.startswith("color:"):
        _, key, idx = data.split(":")
        color = PRODUCTS[key]["colors"][int(idx)]
        return await q.message.reply_text(
            f"🎨 رنگ انتخابی شما: {color}\n\nبرای محاسبه مجدد یا برگشت به منوی اصلی از دکمه‌های زیر استفاده کنید:",
            reply_markup=calc_repeat_keyboard()
        )
    if data.startswith("usage:"):
        usage = data.split(":")[1]
        if usage == "office":
            return await ask_dimensions(q, context, "metal")
        return await q.message.reply_text(
            "🏠 برای کاربری مسکونی، این گزینه‌ها پیشنهاد می‌شوند:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🪟 پرده شید ساده", callback_data="p:shade")],
                [InlineKeyboardButton("🟫 پرده زبرا", callback_data="p:zebra")],
            ])
        )
    if data.startswith("order:"):
        key = data.split(":")[1]
        url = ORDER_LINKS.get(key, "")
        if url:
            return await q.message.reply_text(
                f"🛒 {PRODUCTS[key]['name']}\nبرای ثبت سفارش روی لینک زیر بزنید:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ ثبت سفارش آنلاین", url=url)]])
            )
        return await q.message.reply_text("⚠️ لینک ثبت سفارش این محصول هنوز در تنظیمات ربات وارد نشده است.")

async def error_handler(update, context):
    log.exception("Telegram error", exc_info=context.error)

def build_app():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(callback))
    app.add_error_handler(error_handler)
    return app

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    app = build_app()
    if not BASE_URL:
        raise RuntimeError("BASE_URL is not set")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{BASE_URL}/webhook/{TOKEN}",
        allowed_updates=Update.ALL_TYPES,
    )
