import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN", "").strip()
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fars-gallery")

PRODUCTS = {
    "shade": {"name":"پرده شید ساده","price":1980000,"min_h":200,"min_area":2.0,"colors":["سفید","طوسی","کرم"]},
    "blackout": {"name":"پرده شید بلک اوت","price":3350000,"min_h":200,"min_area":2.0,"colors":["سفید","طوسی","کرم"]},
    "zebra": {"name":"پرده زبرا","price":2325000,"min_h":150,"min_area":1.5,"colors":["سفید","طوسی","قهوه‌ای"]},
    "metal": {"name":"پرده کرکره فلزی","price":2970000,"min_h":None,"min_area":1.5,"colors":["سفید","طوسی","مشکی"]},
}

def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 استعلام قیمت پرده")],
        [KeyboardButton("🛒 ثبت سفارش")],
        [KeyboardButton("💡 راهنمایی و پیشنهاد نوع پرده")],
        [KeyboardButton("📍 آدرس و تماس با ما"), KeyboardButton("🕘 ساعات کاری")],
        [KeyboardButton("🌐 وب‌سایت خرید آنلاین")],
    ], resize_keyboard=True, is_persistent=True)

def products():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪟 پرده شید ساده", callback_data="p:shade")],
        [InlineKeyboardButton("🌑 پرده شید بلک اوت", callback_data="p:blackout")],
        [InlineKeyboardButton("🟫 پرده زبرا", callback_data="p:zebra")],
        [InlineKeyboardButton("🪟 پرده کرکره فلزی", callback_data="p:metal")],
    ])

def colors_yes(key):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎨 آره، رنگ‌بندی رو بگو", callback_data=f"colors:{key}")]])

def color_buttons(key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(c, callback_data=f"color:{key}:{i}")]
        for i, c in enumerate(PRODUCTS[key]["colors"])
    ])

def repeat_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 دوباره حساب کن", callback_data="again")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")]
    ])

def order_buttons():
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

async def start_dimensions(message, context, key):
    context.user_data["product"] = key
    context.user_data["step"] = "width"
    await message.reply_text(f"📐 {PRODUCTS[key]['name']}\n\nعرض پرده را به سانتی‌متر وارد کنید:")

async def calculate(message, context):
    key = context.user_data["product"]
    p = PRODUCTS[key]
    width_cm = context.user_data["width_cm"]
    input_height = context.user_data["height_cm"]

    height_cm = max(input_height, p["min_h"]) if p["min_h"] else input_height
    area = (width_cm / 100) * (height_cm / 100)
    final_area = max(area, p["min_area"])
    final_price = round(final_area * p["price"])

    notes = []
    if p["min_h"] and input_height < p["min_h"]:
        notes.append(f"📌 به خاطر قانون {p['name']}، ارتفاع کمتر از {p['min_h']} سانتی‌متر، {p['min_h']} در نظر گرفته شد.")
    if area < p["min_area"]:
        notes.append(f"📌 به خاطر قانون {p['name']}، متراژ کمتر از {p['min_area']:g} مترمربع، {p['min_area']:g} در نظر گرفته شد.")

    text = (
        f"✅ نتیجه محاسبه {p['name']}\n\n"
        f"📐 عرض: {width_cm:g} سانتی‌متر\n"
        f"📏 ارتفاع: {height_cm:g} سانتی‌متر\n"
        f"📊 متر مربع: {final_area:.2f}\n"
        f"💵 قیمت واحد: {p['price']:,.0f} تومان\n"
        f"💰 قیمت نهایی: {final_price:,.0f} تومان\n\n"
    )
    if notes:
        text += "\n".join(notes) + "\n\n"
    text += (
        "🚚 سه روز کاری تحویلت میدم و هر شهری هم که باشی ارسال می‌کنم.\n"
        "🛡️ ۲ سال هم ضمانتش می‌کنم و کیفیتشم که درجه یکه دیگه چی می‌خوای 😍❤️"
    )
    context.user_data["step"] = "done"
    await message.reply_text(text, reply_markup=colors_yes(key))

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    step = context.user_data.get("step")

    if text == "💰 استعلام قیمت پرده":
        return await update.message.reply_text("🧾 نوع پرده را انتخاب کنید:", reply_markup=products())

    if text == "🛒 ثبت سفارش":
        return await update.message.reply_text("🛒 اول نوع پرده را انتخاب کنید:", reply_markup=order_buttons())

    if text == "💡 راهنمایی و پیشنهاد نوع پرده":
        return await update.message.reply_text(
            "💡 پرده را برای چه کاربری می‌خواهید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏢 اداری و تجاری", callback_data="usage:office")],
                [InlineKeyboardButton("🏠 مسکونی", callback_data="usage:home")]
            ])
        )

    if text == "📍 آدرس و تماس با ما":
        return await update.message.reply_text(
            "📍 آدرس تماس با ما:\n"
            "شیراز، خیابان قصردشت، چهارراه عفیف‌آباد، ابتدای بلوار آوینی، نبش کوچه یک، "
            "مجموعه گالری هنری ایران دکوراسیون (فارس گالری)\n\n"
            "📞 شماره تماس: 07136277172"
        )

    if text == "🕘 ساعات کاری":
        return await update.message.reply_text("🕘 ساعات کاری:\nصبح: 09:00 تا 13:00\nعصر: 17:00 تا 21:00")

    if text == "🌐 وب‌سایت خرید آنلاین":
        url = os.getenv("WEBSITE_URL", "")
        return await update.message.reply_text(f"🌐 وب‌سایت خرید آنلاین:\n{url}" if url else "🌐 لینک وب‌سایت تنظیم نشده است.")

    if text in ("🏠 منوی اصلی", "شروع"):
        return await start(update, context)

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
        return await calculate(update.message, context)

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("p:"):
        return await start_dimensions(q.message, context, data.split(":")[1])

    if data == "again":
        context.user_data.clear()
        return await q.message.reply_text("🧾 نوع پرده را انتخاب کنید:", reply_markup=products())

    if data == "home":
        context.user_data.clear()
        return await q.message.reply_text("🏠 منوی اصلی:", reply_markup=main_menu())

    if data.startswith("colors:"):
        return await q.message.reply_text("🎨 رنگ‌بندی:", reply_markup=color_buttons(data.split(":")[1]))

    if data.startswith("color:"):
        _, key, index = data.split(":")
        color = PRODUCTS[key]["colors"][int(index)]
        return await q.message.reply_text(
            f"🎨 رنگ انتخابی: {color}\n\nمی‌توانید دوباره محاسبه کنید یا به منوی اصلی برگردید.",
            reply_markup=repeat_buttons()
        )

    if data == "usage:office":
        return await start_dimensions(q.message, context, "metal")

    if data == "usage:home":
        return await q.message.reply_text(
            "🏠 پیشنهادهای مناسب مسکونی:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🪟 پرده شید ساده", callback_data="p:shade")],
                [InlineKeyboardButton("🟫 پرده زبرا", callback_data="p:zebra")]
            ])
        )

    if data.startswith("order:"):
        key = data.split(":")[1]
        url = ORDER_LINKS.get(key, "")
        if not url:
            return await q.message.reply_text("⚠️ لینک ثبت سفارش این محصول در تنظیمات Render وارد نشده است.")
        return await q.message.reply_text(
            f"🛒 {PRODUCTS[key]['name']}\nبرای ثبت سفارش روی لینک زیر بزنید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ ثبت سفارش آنلاین", url=url)]])
        )

async def error_handler(update, context):
    log.exception("Telegram error", exc_info=context.error)

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")
    if not BASE_URL:
        raise RuntimeError("BASE_URL environment variable is missing.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(error_handler)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=f"webhook/{TOKEN}",
        webhook_url=f"{BASE_URL}/webhook/{TOKEN}",
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()
