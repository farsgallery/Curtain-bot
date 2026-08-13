import os
import math
import logging
from datetime import datetime
import pytz
import http.server
import socketserver
import threading
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

# --- ایجاد وب‌سرور مصنوعی برای حل ارور Port در Render ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"Dummy Web Server running on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Web server error: {e}")

threading.Thread(target=run_dummy_server, daemon=True).start()
# --------------------------------------------------------

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

CHOOSING_CURTAIN, GET_WIDTH, GET_HEIGHT, ASK_COLOR_CONFIRM, SHOW_COLORS = range(5)

PERSISTENT_KEYBOARD = ReplyKeyboardMarkup([
    ['🧮 میخواهم فقط استعلام قیمت پرده بگیرم', '🛍 میخواهم ثبت سفارش انجام بدم'],
    ['💡 راهنمایی و پیشنهاد نوع پرده', '🌐 وب سایت خرید آنلاین'],
    ['📞 تماس با ما / آدرس', '⏰ ساعات کاری'],
    ['🔄 محاسبه مجدد']
], resize_keyboard=True)

def get_today_date():
    tehran_tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(tehran_tz)
    return f"📅 تاریخ امروز: {now.strftime('%Y/%m/%d')}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        f"{get_today_date()}\n\n"
        "به ربات مجموعه هُنری فــارس گـالری خوش آمدید ✨\n\n"
        "می‌توانید برای استعلام قیمت بر اساس ابعاد و اندازه پرده مورد نظر خود "
        "و همچنین ثبت سفارش از این ربات به راحتی استفاده کنید:"
    )
    await update.message.reply_text(welcome_msg, reply_markup=PERSISTENT_KEYBOARD)
    return ConversationHandler.END

async def suggest_curtain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([
        ['🏢 اداری و تجاری', '🏠 مسکونی'],
        ['🔙 بازگشت به منوی اصلی']
    ], resize_keyboard=True)
    await update.message.reply_text("برای چه کاربردی پرده نیاز دارید؟ 🧐", reply_markup=keyboard)

async def handle_suggestion_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🏢 اداری و تجاری':
        keyboard = ReplyKeyboardMarkup([['📌 پرده کرکره فلزی'], ['🔙 بازگشت به منوی اصلی']], resize_keyboard=True)
        await update.message.reply_text("پیشنهاد ما برای محیط‌های اداری و تجاری: **پرده کرکره فلزی** است.", reply_markup=keyboard, parse_mode='Markdown')
    elif text == '🏠 مسکونی':
        keyboard = ReplyKeyboardMarkup([['📌 پرده شید ساده', '📌 پرده زبرا'], ['🔙 بازگشت به منوی اصلی']], resize_keyboard=True)
        await update.message.reply_text("پیشنهاد ما برای محیط‌های مسکونی: **پرده شید ساده** یا **پرده زبرا** است.", reply_markup=keyboard, parse_mode='Markdown')

async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📍 **آدرس:**\n"
        "شیراز، خیابان قصردشت، چهارراه عفیف‌آباد، ابتدای بلوار آوینی، نبش کوچه یک، مجموعه گالری هنری ایران دکوراسیون (فارس گالری)\n\n"
        "📞 **شماره تماس:** 07136277172"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def show_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "⏰ **ساعات کاری مجموعه:**\n\n☀️ صبح: از 09:00 تا 13:00\n🌙 عصر: از 17:00 تا 21:00"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def show_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🌐 **وب سایت خرید آنلاین:**\nwww.FarsGallery.com"
    await update.message.reply_text(msg)

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "لطفاً نوع پرده مورد نظر خود را جهت ورود به لینک خرید انتخاب کنید:\n\n"
        "1️⃣ **پرده شید ساده** (پیشنهاد ما برای مسکونی)\n"
        "🔗 [فروشگاه اینترنتی فارس گالری - شید رول](https://farsgallery.com)\n\n"
        "2️⃣ **پرده شید بلک اوت** (پیشنهاد ما برای اداری مخصوصاً اتاق کامپیوتر یا ویدیو پروژکتور)\n"
        "🔗 [فروشگاه اینترنتی فارس گالری - شید بلک اوت](https://farsgallery.com)\n\n"
        "3️⃣ **پرده زبرا** (پیشنهاد ما برای مسکونی)\n"
        "🔗 [فروشگاه اینترنتی فارس گالری - زبرا ساده](https://farsgallery.com)\n\n"
        "4️⃣ **پرده کرکره فلزی** (پیشنهاد ما برای اداری یا تجاری)\n"
        "🔗 [فروشگاه اینترنتی فارس گالری - کرکره فلزی ۲۵ میل](https://farsgallery.com)"
    )
    await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)

async def start_price_inquiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([
        ['📌 پرده شید ساده', '📌 پرده شید بلک اوت'],
        ['📌 پرده زبرا', '📌 پرده کرکره فلزی'],
        ['🔙 بازگشت به منوی اصلی']
    ], resize_keyboard=True)
    await update.message.reply_text("لطفاً نوع پرده مورد نظر را جهت استعلام قیمت انتخاب کنید:", reply_markup=keyboard)
    return CHOOSING_CURTAIN

async def curtain_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    curtain_type = update.message.text.replace('📌 ', '')
    if curtain_type == '🔙 بازگشت به منوی اصلی':
        await update.message.reply_text("به منوی اصلی بازگشتید.", reply_markup=PERSISTENT_KEYBOARD)
        return ConversationHandler.END
    
    context.user_data['curtain_type'] = curtain_type
    await update.message.reply_text(f"لطفاً **عرض** پرده را به **سانتی‌متر** وارد کنید (مثال: 150):", parse_mode='Markdown')
    return GET_WIDTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        width = float(update.message.text)
        context.user_data['width'] = width
        await update.message.reply_text("لطفاً **ارتفاع** پرده را به **سانتی‌متر** وارد کنید (مثال: 200):", parse_mode='Markdown')
        return GET_HEIGHT
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً عرض را به صورت عدد وارد کنید.")
        return GET_WIDTH

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        width = context.user_data['width']
        curtain_type = context.user_data['curtain_type']
        
        unit_price = 0
        min_height = 0
        min_area = 0
        rules_applied = []

        if curtain_type == 'پرده شید ساده':
            unit_price = 1980000
            min_height, min_area = 200, 2.0
            calc_height = height
            if height < min_height:
                calc_height = min_height
                rules_applied.append("به خاطر قانون پرده شید کمتر از 200، من 200 در نظر گرفتم.")
            area = (width / 100) * (calc_height / 100)
            calc_area = area
            if area < min_area:
                calc_area = min_area
                rules_applied.append("به خاطر قانون پرده شید، من کمتر از متراژ 2 همان 2 در نظر گرفتم.")

        elif curtain_type == 'پرده شید بلک اوت':
            unit_price = 3350000
            min_height, min_area = 200, 2.0
            calc_height = height
            if height < min_height:
                calc_height = min_height
                rules_applied.append("به خاطر قانون پرده شید کمتر از 200، من 200 در نظر گرفتم.")
            area = (width / 100) * (calc_height / 100)
            calc_area = area
            if area < min_area:
                calc_area = min_area
                rules_applied.append("به خاطر قانون پرده شید، من کمتر از متراژ 2 همان 2 در نظر گرفتم.")

        elif curtain_type == 'پرده زبرا':
            unit_price = 2325000
            min_height, min_area = 150, 1.5
            calc_height = height
            if height < min_height:
                calc_height = min_height
                rules_applied.append("به خاطر قانون پرده زبرا کمتر از 150، من 150 در نظر گرفتم.")
            area = (width / 100) * (calc_height / 100)
            calc_area = area
            if area < min_area:
                calc_area = min_area
                rules_applied.append("به خاطر قانون پرده زبرا، من کمتر از متراژ 1.5 همان 1.5 در نظر گرفتم.")

        elif curtain_type == 'پرده کرکره فلزی':
            unit_price = 2970000
            min_area = 1.5
            calc_height = height
            area = (width / 100) * (calc_height / 100)
            calc_area = area
            if area < min_area:
                calc_area = min_area
                rules_applied.append("به خاطر قانون پرده کرکره فلزی، کمتر از 1.5 متر مربع همان 1.5 در نظر گرفتم.")

        total_price = int(calc_area * unit_price)
        
        rules_text = "\n".join([f"⚠️ {r}" for r in rules_applied])
        if rules_text:
            rules_text = "\n" + rules_text + "\n"

        result_msg = (
            f"📊 **نتیجه محاسبات {curtain_type}:**\n\n"
            f"📏 عرض: {width} سانتی‌متر\n"
            f"📐 ارتفاع: {height} سانتی‌متر\n"
            f"📐 متراژ محاسبه شده: {calc_area:.2f} متر مربع\n"
            f"{rules_text}\n"
            f"💵 قیمت واحد: {unit_price:,} تومان\n"
            f"💰 **قیمت نهایی:** {total_price:,} تومان\n\n"
            "سه روز کاری تحویلت میدم و هر شهری هم که باشی ارسال میکنم و 2 سال هم ضمانتش میکنم و کیفیتشم که درجه یکه دیگه چی میخوای 😍😍"
        )

        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("آره 😍 (مشاهده رنگ‌بندی)", callback_data=f"colors_{curtain_type}")]
        ])

        await update.message.reply_text(result_msg, parse_mode='Markdown', reply_markup=inline_kb)
        await update.message.reply_text("برای محاسبه مجدد یا گزینه‌های دیگر از منوی زیر استفاده کنید:", reply_markup=PERSISTENT_KEYBOARD)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("⚠️ لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return GET_HEIGHT

async def show_colors_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    curtain_type = query.data.replace("colors_", "")

    if curtain_type in ['پرده شید ساده', 'پرده شید بلک اوت']:
        colors = ["⚪️ سفید", "🩶 طوسی", "🏷 کرم"]
    elif curtain_type == 'پرده زبرا':
        colors = ["⚪️ سفید", "🩶 طوسی", "🟤 قهوه‌ای"]
    elif curtain_type == 'پرده کرکره فلزی':
        colors = ["⚪️ سفید", "🩶 طوسی", "⬛️ مشکی"]
    else:
        colors = ["⚪️ سفید", "🩶 طوسی"]

    color_buttons = [[InlineKeyboardButton(c, callback_data="color_selected")] for c in colors]
    await query.message.reply_text("🎨 **رنگ‌بندی‌های موجود:**", reply_markup=InlineKeyboardMarkup(color_buttons), parse_mode='Markdown')

async def color_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("رنگ انتخاب شد!")
    await query.message.reply_text("✨ جهت ثبت نهایی سفارش می‌توانید از طریق منو روی دکمه «ثبت سفارش» کلیک کنید.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.", reply_markup=PERSISTENT_KEYBOARD)
    return ConversationHandler.END

def main():
    # دریافت توکن از متغیر محیطی یا استفاده مستقیم از مقدار دستی
    TOKEN = os.environ.get("BOT_TOKEN", "8737297309:AAGcH5LLdjnJB49V2r76cpnxE8qxYcVIz9o")

    app = ApplicationBuilder().token(TOKEN).build()

    price_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^(🧮 میخواهم فقط استعلام قیمت پرده بگیرم|🔄 محاسبه مجدد)$'), start_price_inquiry),
            MessageHandler(filters.Regex('^📌 '), curtain_chosen)
        ],
        states={
            CHOOSING_CURTAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, curtain_chosen)],
            GET_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_width)],
            GET_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(price_handler)
    app.add_handler(MessageHandler(filters.Regex('^🛍 میخواهم ثبت سفارش انجام بدم$'), start_order))
    app.add_handler(MessageHandler(filters.Regex('^💡 راهنمایی و پیشنهاد نوع پرده$'), suggest_curtain))
    app.add_handler(MessageHandler(filters.Regex('^(🏢 اداری و تجاری|🏠 مسکونی)$'), handle_suggestion_choice))
    app.add_handler(MessageHandler(filters.Regex('^📞 تماس با ما / آدرس$'), show_contact))
    app.add_handler(MessageHandler(filters.Regex('^⏰ ساعات کاری$'), show_hours))
    app.add_handler(MessageHandler(filters.Regex('^🌐 وب سایت خرید آنلاین$'), show_website))
    
    app.add_handler(CallbackQueryHandler(show_colors_callback, pattern="^colors_"))
    app.add_handler(CallbackQueryHandler(color_selected_callback, pattern="^color_selected$"))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
