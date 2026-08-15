import os
import math
import logging
import jdatetime
import http.server
import socketserver
import threading
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

# --- آیدی کانال جهت جوین اجباری ---
CHANNEL_USERNAME = "@irandecoration_gallery"

# --- لینک‌های اختصاصی و مستقیم هر محصول ---
PRODUCT_LINKS = {
    'پرده شید ساده': 'https://farsgallery.com/product-category/curtains/shid/',
    'پرده شید بلک اوت': 'https://farsgallery.com/product-category/curtains/shid/',
    'پرده زبرا': 'https://farsgallery.com/product-category/curtains/zebra/simple/',
    'پرده کرکره فلزی': 'https://farsgallery.com/product-category/curtains/cercere/'
}

# --- وب‌سرور مجازی جهت نگه داشتن ربات روی Render ---
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

GET_WIDTH, GET_HEIGHT = range(2)

# --- منوی اصلی ثابت پایین ---
PERSISTENT_KEYBOARD = ReplyKeyboardMarkup([
    ['شروع 🏠'],
    ['راهنمایی و پیشنهاد نوع پرده 💡'],
    ['وب سایت خرید آنلاین 🌐'],
    ['ساعات کاری 🕒'],
    ['آدرس و شماره تماس 📍']
], resize_keyboard=True)

def get_jalali_date():
    now = jdatetime.datetime.now()
    return now.strftime('%Y/%m/%d')

# بررسی عضویت در کانال
async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        return True

async def send_join_channel_message(update: Update):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال فارس گالری", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_join")]
    ])
    msg_text = (
        "⚠️ **دسترسـی محدود است!**\n\n"
        "برای استفاده از خدمات و استعلام قیمت ربات فارس گالری، لطفاً ابتدا در کانال رسمی ما عضو شوید و سپس روی دکمه **بررسی عضویت 🔄** کلیک کنید."
    )
    if update.message:
        await update.message.reply_text(msg_text, reply_markup=keyboard, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg_text, reply_markup=keyboard, parse_mode='Markdown')

# تابع پیام خوش‌آمدگویی همراه با دکمه‌های شیشه‌ای ۱ و ۲
async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ میخواهم فقط استعلام قیمت پرده بگیرم", callback_data="start_inquiry")],
        [InlineKeyboardButton("2️⃣ میخواهم ثبت سفارش انجام بدم", callback_data="start_order")]
    ])
    welcome_msg = (
        "به ربات مجموعه هُنری فارس گالری خوش آمدید 🎨\n\n"
        "✨ می‌توانید برای استعلام قیمت پرده و ثبت سفارش از این ربات استفاده کنید.\n\n"
        "👇 یکی از گزینه ها را انتخاب کنید:"
    )
    if update.message:
        await update.message.reply_text(welcome_msg, reply_markup=PERSISTENT_KEYBOARD)
        await update.message.reply_text("👇 انتخاب کنید:", reply_markup=inline_kb)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_msg, reply_markup=inline_kb)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_member(user_id, context):
        await send_join_channel_message(update)
        return ConversationHandler.END
    await send_welcome_message(update, context)
    return ConversationHandler.END

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if await is_user_member(user_id, context):
        await query.message.reply_text("✅ عضویت شما تأیید شد!", reply_markup=PERSISTENT_KEYBOARD)
        await send_welcome_message(update, context)
    else:
        await query.answer("❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)

# نمایش لیست شیشه‌ای پرده‌ها
async def show_curtains_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    curtains_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="select_پرده شید ساده")],
        [InlineKeyboardButton("پرده شید بلک اوت 🌚", callback_data="select_پرده شید بلک اوت")],
        [InlineKeyboardButton("پرده زبرا 🦓", callback_data="select_پرده زبرا")],
        [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="select_پرده کرکره فلزی")]
    ])
    await query.message.reply_text("👇 نوع پرده را انتخاب کنید:", reply_markup=curtains_kb)

async def select_curtain_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    curtain_type = query.data.replace("select_", "")
    context.user_data['curtain_type'] = curtain_type
    
    icon_map = {
        'پرده شید ساده': 'پرده شید ساده 🪟',
        'پرده شید بلک اوت': 'پرده شید بلک اوت 🌚',
        'پرده زبرا': 'پرده زبرا 🦓',
        'پرده کرکره فلزی': 'پرده کرکره فلزی 🏢'
    }
    context.user_data['curtain_icon'] = icon_map.get(curtain_type, curtain_type)

    await query.message.reply_text(f"لطفاً **عرض** پرده را به **سانتی‌متر** وارد کنید (مثال: 150):", parse_mode='Markdown')
    return GET_WIDTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        width = float(text)
        context.user_data['width'] = width
        await update.message.reply_text("لطفاً **ارتفاع** پرده را به **سانتی‌متر** وارد کنید (مثال: 200):", parse_mode='Markdown')
        return GET_HEIGHT
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً عرض را به صورت عدد وارد کنید (مثال: 150).")
        return GET_WIDTH

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        height = float(text)
        width = context.user_data['width']
        curtain_type = context.user_data['curtain_type']
        curtain_icon = context.user_data['curtain_icon']
        
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

        # انتخاب لینک اختصاصی محصول
        buy_url = PRODUCT_LINKS.get(curtain_type, 'https://farsgallery.com')

        result_msg = (
            f" قیمت امروز\n"
            f"🗓 تاریخ: {get_jalali_date()}\n\n"
            f"{curtain_icon}\n\n"
            f"📐 عرض:\n{int(width)} سانتیمتر\n\n"
            f"📐 ارتفاع:\n{int(height)} سانتیمتر\n\n"
            f"🧮 متر مربع:\n{calc_area:.2f}\n\n"
            f"{rules_text}"
            f"🪙 قیمت واحد هر مترمربع:\n{unit_price:,} تومان\n\n"
            f"💵 قیمت نهایی:\n{total_price:,} تومان\n\n"
            f"📦 هر شهری باشی ارسال میکنم\n"
            f"🛡 5 سال ضمانت\n"
            f"🚚 سه روز کاری تحویلت میدم\n"
            f"✨ کیفیت درجه یک 😍😍"
        )

        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("رنگ بندی 🎨", callback_data=f"colors_{curtain_type}")],
            [InlineKeyboardButton("میخوای خرید کنی؟ 🛒", url=buy_url)],
            [InlineKeyboardButton("شروع دوباره 🔄", callback_data="start_inquiry")]
        ])

        await update.message.reply_text(result_msg, reply_markup=inline_kb)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("⚠️ لطفاً ارتفاع را به صورت عدد وارد کنید (مثال: 200).")
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
    await query.message.reply_text("✨ جهت ثبت نهایی سفارش می‌توانید از طریق منوی اصلی روی دکمه ثبت سفارش کلیک کنید.")

async def start_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    msg = (
        "لطفاً نوع پرده مورد نظر خود را جهت ورود به لینک خرید انتخاب کنید:\n\n"
        f"1️⃣ **پرده شید ساده** (پیشنهاد ما برای مسکونی)\n"
        f"🔗 [فروشگاه اینترنتی فارس گالری - شید رول]({PRODUCT_LINKS['پرده شید ساده']})\n\n"
        f"2️⃣ **پرده شید بلک اوت** (پیشنهاد ما برای اداری)\n"
        f"🔗 [فروشگاه اینترنتی فارس گالری - شید بلک اوت]({PRODUCT_LINKS['پرده شید بلک اوت']})\n\n"
        f"3️⃣ **پرده زبرا** (پیشنهاد ما برای مسکونی)\n"
        f"🔗 [فروشگاه اینترنتی فارس گالری - زبرا ساده]({PRODUCT_LINKS['پرده زبرا']})\n\n"
        f"4️⃣ **پرده کرکره فلزی** (پیشنهاد ما برای اداری یا تجاری)\n"
        f"🔗 [فروشگاه اینترنتی فارس گالری - کرکره فلزی]({PRODUCT_LINKS['پرده کرکره فلزی']})"
    )
    await query.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)

# دکمه‌های منوی ثابت اصلی
async def suggest_curtain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏢 اداری و تجاری", callback_data="sugg_office")],
        [InlineKeyboardButton("🏠 مسکونی", callback_data="sugg_home")]
    ])
    await update.message.reply_text("برای چه کاربردی پرده نیاز دارید؟ 🧐", reply_markup=keyboard)
    return ConversationHandler.END

# هدایت مستقیم از راهنما به محاسبه قیمت
async def handle_suggestion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'sugg_office':
        msg = "پیشنهاد ما برای محیط‌های اداری و تجاری: **پرده کرکره فلزی 🏢** و **پرده شید بلک اوت 🌚** است.\n\n👇 جهت استعلام قیمت یکی از موارد زیر را انتخاب کنید:"
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("محاسبه قیمت پرده کرکره فلزی 🏢", callback_data="select_پرده کرکره فلزی")],
            [InlineKeyboardButton("محاسبه قیمت پرده شید بلک اوت 🌚", callback_data="select_پرده شید بلک اوت")],
            [InlineKeyboardButton("محاسبه سایر پرده‌ها 🧮", callback_data="start_inquiry")]
        ])
    else:
        msg = "پیشنهاد ما برای محیط‌های مسکونی: **پرده شید ساده 🪟** و **پرده زبرا 🦓** است.\n\n👇 جهت استعلام قیمت یکی از موارد زیر را انتخاب کنید:"
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("محاسبه قیمت پرده زبرا 🦓", callback_data="select_پرده زبرا")],
            [InlineKeyboardButton("محاسبه قیمت پرده شید ساده 🪟", callback_data="select_پرده شید ساده")],
            [InlineKeyboardButton("محاسبه سایر پرده‌ها 🧮", callback_data="start_inquiry")]
        ])
    await query.message.reply_text(msg, reply_markup=buttons, parse_mode='Markdown')

async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📍 **آدرس و شماره تماس:**\n\n"
        "شیراز، خیابان قصردشت، چهارراه عفیف‌آباد، ابتدای بلوار آوینی، نبش کوچه یک، مجموعه گالری هنری ایران دکوراسیون (فارس گالری)\n\n"
        "📞 **شماره تماس:** 07136277172"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')
    return ConversationHandler.END

async def show_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🕒 **ساعات کاری مجموعه:**\n\n☀️ صبح: از 09:00 تا 13:00\n🌙 عصر: از 17:00 تا 21:00"
    await update.message.reply_text(msg, parse_mode='Markdown')
    return ConversationHandler.END

async def show_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🌐 **وب سایت خرید آنلاین:**\nwww.FarsGallery.com"
    await update.message.reply_text(msg)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عمل لغو شد.", reply_markup=PERSISTENT_KEYBOARD)
    return ConversationHandler.END

def main():
    TOKEN = os.environ.get("BOT_TOKEN", "8737297309:AAGcH5LLdjnJB49V2r76cpnxE8qxYcVIz9o")

    app = ApplicationBuilder().token(TOKEN).build()

    price_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(select_curtain_callback, pattern="^select_")
        ],
        states={
            GET_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^(شروع 🏠|راهنمایی و پیشنهاد نوع پرده 💡|وب سایت خرید آنلاین 🌐|ساعات کاری 🕒|آدرس و شماره تماس 📍)$'), get_width)],
            GET_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^(شروع 🏠|راهنمایی و پیشنهاد نوع پرده 💡|وب سایت خرید آنلاین 🌐|ساعات کاری 🕒|آدرس و شماره تماس 📍)$'), get_height)]
        },
        fallbacks=[
            MessageHandler(filters.Regex('^(شروع 🏠|راهنمایی و پیشنهاد نوع پرده 💡|وب سایت خرید آنلاین 🌐|ساعات کاری 🕒|آدرس و شماره تماس 📍)$'), cancel),
            CommandHandler('cancel', cancel)
        ]
    )

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(price_conv_handler)
    
    # دکمه‌های ثابت منو
    app.add_handler(MessageHandler(filters.Regex('^شروع 🏠$'), start_command))
    app.add_handler(MessageHandler(filters.Regex('^راهنمایی و پیشنهاد نوع پرده 💡$'), suggest_curtain))
    app.add_handler(MessageHandler(filters.Regex('^وب سایت خرید آنلاین 🌐$'), show_website))
    app.add_handler(MessageHandler(filters.Regex('^ساعات کاری 🕒$'), show_hours))
    app.add_handler(MessageHandler(filters.Regex('^آدرس و شماره تماس 📍$'), show_contact))
    
    # کالبک‌های دکمه‌های شیشه‌ای
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(show_curtains_callback, pattern="^start_inquiry$"))
    app.add_handler(CallbackQueryHandler(start_order_callback, pattern="^start_order$"))
    app.add_handler(CallbackQueryHandler(handle_suggestion_callback, pattern="^sugg_"))
    app.add_handler(CallbackQueryHandler(show_colors_callback, pattern="^colors_"))
    app.add_handler(CallbackQueryHandler(color_selected_callback, pattern="^color_selected$"))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
