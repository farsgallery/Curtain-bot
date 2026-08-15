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

# --- تنظیمات مدیریت و کانال ---
ADMIN_ID = 333050909  
ADMIN_USERNAME = "@arhnh"
CHANNEL_USERNAME = "@irandecoration_gallery"

PRODUCT_LINKS = {
    'پرده شید ساده': 'https://farsgallery.com/product-category/curtains/shid/',
    'پرده شید بلک اوت': 'https://farsgallery.com/product-category/curtains/shid/',
    'پرده زبرا': 'https://farsgallery.com/product-category/curtains/zebra/simple/',
    'پرده کرکره فلزی': 'https://farsgallery.com/product-category/curtains/cercere/'
}

PRICES = {
    'پرده شید ساده': 1980000,
    'پرده شید بلک اوت': 3350000,
    'پرده زبرا': 2325000,
    'پرده کرکره فلزی': 2970000
}

USER_LIST = set()

# فایل آیدی‌های به‌روزرسانی شده
PORTFOLIO_IMAGES = {
    'پرده زبرا': [
        "AgACAgQAAxkBAAINgmqAN9MBBfL-fATjGc0bAvKXqcwkAAIHEGsbKiQBUD_cumH9NZmpAQADAgADeQADPQQ",
        "AgACAgQAAxkBAAINg2qAN9M86Ch402OO3kv9dngq5utnAAIIEGsbKiQBUDOPifTSJATYAQADAgADeQADPQQ",
        "AgACAgQAAxkBAAINhGqAN9MufbDbySYx6hiDtQheDuTbAAIJEGsbKiQBUNTZcyys1KRDAQADAgADeQADPQQ"
    ],
    'پرده کرکره فلزی': [
        "AgACAgQAAxkBAAINiGqAOB48r5f99pD3JAoT3IJ4YA-FAAINEGsbKiQBUKYBX3ntTJLPAQADAgADeQADPQQ",
        "AgACAgQAAxkBAAINiWqAOB78ixk8x7bWq2mT0Az0mZZXAAIOEGsbKiQBUK8hQZZmc8J4AQADAgADeQADPQQ",
        "AgACAgQAAxkBAAINimqAOB6Dw-IGQRft6PAnxfuXvXHYAAJsD2sb03MBUG8XGvaJAbRPAQADAgADeQADPQQ"
    ],
    'پرده شید ساده': [
        "AgACAgQAAxkBAAINjmqAOGeyv2OWNrt-3xAffcH-IgxPAAIQEGsbKiQBUHsdkKQY4gXPAQADAgADeQADPQQ",
        "AgACAgQAAxkBAAINj2qAOGe9JfdiH_qXeNihXAFeXHB1AAJwD2sb03MBUHsa4Jyg84PeAQADAgADeQADPQQ",
        "AgACAgQAAxkBAAINkmqAOJe30jXWZERkxzIpnIbswDZNAAIREGsbKiQBUAkolxQ5GHJNAQADAgADeQADPQQ"
    ],
    'پرده شید بلک اوت': [
        "AgACAgQAAxkBAAINgGqAN4xO0CG4N5YJ__6hjPGfSrDJAAIGEGsbKiQBUFBGGh9u51EmAQADAgADeQADPQQ"
    ]
}

# --- وب‌سرور مجازی Render ---
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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

GET_WIDTH, GET_HEIGHT = range(2)
ORD_NAME, ORD_PHONE, ORD_TYPE, ORD_ADDRESS = range(2, 6)
SET_PR_VAL = 6

# --- منوی اصلی ---
PERSISTENT_KEYBOARD = ReplyKeyboardMarkup([
    ['شروع 🏠'],
    ['راهنمایی و پیشنهاد نوع پرده 💡', 'نمونه کارها 🖼'],
    ['ثبت سفارش و مشاوره مستقیم 📝', 'آموزش اندازه‌گیری 📐'],
    ['محاسبه هزینه نصب و ارسال 🚚', 'وب سایت خرید آنلاین 🌐'],
    ['ساعات کاری 🕒', 'آدرس و شماره تماس 📍']
], resize_keyboard=True)

def get_jalali_date():
    now = jdatetime.datetime.now()
    return now.strftime('%Y/%m/%d')

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        return True

# --- دریافت و استخراج File ID مخصوص ادمین ---
async def get_photo_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        file_id = update.message.document.file_id
    else:
        return

    text = (
        "📸 **فایل آیدی دریافت شد:**\n\n"
        f"`{file_id}`\n\n"
        "📌 *کد بالا را کپی کرده و در بخش PORTFOLIO_IMAGES کد قرار دهید.*"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def send_join_channel_message(update: Update):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال ما", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_join")]
    ])
    msg_text = (
        "⚠️ **دسترسـی محدود است!**\n\n"
        "برای استفاده از استعلام قیمت ، لطفاً ابتدا در کانال رسمی ما عضو شوید و سپس روی دکمه **بررسی عضویت 🔄** کلیک کنید."
    )
    if update.message:
        await update.message.reply_text(msg_text, reply_markup=keyboard, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg_text, reply_markup=keyboard, parse_mode='Markdown')

async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ میخواهم فقط استعلام قیمت پرده بگیرم", callback_data="start_inquiry")],
        [InlineKeyboardButton("2️⃣ میخواهم ثبت سفارش انجام بدم", callback_data="start_order")]
    ])
    welcome_msg = (
        "به ربات مجموعه هُنری فارس گالری خوش آمدید 🎨\n\n"
        "✨ می‌توانید برای استعلام قیمت پرده و ثبت سفارش از این ربات استفاده کنید."
    )
    if update.message:
        await update.message.reply_text(welcome_msg, reply_markup=PERSISTENT_KEYBOARD)
        await update.message.reply_text("👇 یکی از گزینه ها را انتخاب کنید:", reply_markup=inline_kb)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_msg, reply_markup=inline_kb)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_LIST.add(user_id)
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

    await query.message.reply_text("لطفاً **عرض** پرده را به **سانتی‌متر** وارد کنید (مثال: 150):", parse_mode='Markdown')
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
        
        unit_price = PRICES.get(curtain_type, 2000000)
        rules_applied = []

        if curtain_type in ['پرده شید ساده', 'پرده شید بلک اوت']:
            min_height, min_area = 200, 2.0
            calc_height = max(height, min_height)
            if height < min_height:
                rules_applied.append("به خاطر قانون پرده شید کمتر از 200، من 200 در نظر گرفتم.")
            area = (width / 100) * (calc_height / 100)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("به خاطر قانون پرده شید، من کمتر از متراژ 2 همان 2 در نظر گرفتم.")

        elif curtain_type == 'پرده زبرا':
            min_height, min_area = 150, 1.5
            calc_height = max(height, min_height)
            if height < min_height:
                rules_applied.append("به خاطر قانون پرده زبرا کمتر از 150، من 150 در نظر گرفتم.")
            area = (width / 100) * (calc_height / 100)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("به خاطر قانون پرده زبرا، من کمتر از متراژ 1.5 همان 1.5 در نظر گرفتم.")

        elif curtain_type == 'پرده کرکره فلزی':
            min_area = 1.5
            area = (width / 100) * (height / 100)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("به خاطر قانون پرده کرکره فلزی، کمتر از 1.5 متر مربع همان 1.5 در نظر گرفتم.")

        total_price = int(calc_area * unit_price)
        
        rules_text = "\n".join([f"⚠️ {r}" for r in rules_applied])
        if rules_text:
            rules_text = "\n" + rules_text + "\n"

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
            [InlineKeyboardButton("نمونه کارها 🖼", callback_data=f"port_{curtain_type}")],
            [InlineKeyboardButton("هزینه نصب و ارسال 🚚", callback_data="show_install_info")],
            [InlineKeyboardButton("آموزش اندازه‌گیری 📐", callback_data="show_measure_info")],
            [InlineKeyboardButton("ثبت سفارش در تلگرام یا مشاوره 📝", callback_data="start_direct_order_cb")],
            [InlineKeyboardButton("میخوای خرید آنلاین کنی؟ 🛒", url=buy_url)],
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
    await query.message.reply_text("✨ جهت ثبت نهایی سفارش می‌توانید از دکمه «ثبت سفارش در تلگرام یا مشاوره» استفاده کنید.")

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

async def show_portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("پرده زبرا 🦓", callback_data="port_پرده زبرا")],
        [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="port_پرده شید ساده")],
        [InlineKeyboardButton("پرده شید بلک اوت 🌚", callback_data="port_پرده شید بلک اوت")],
        [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="port_پرده کرکره فلزی")]
    ])
    await update.message.reply_text("🖼 نمونه کار کدام محصول را می‌خواهید مشاهده کنید؟", reply_markup=kb)

async def send_portfolio_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("port_", "")
    imgs = PORTFOLIO_IMAGES.get(p_name, [])
    if not imgs:
        await query.message.reply_text(f"⚠️ هنوز تصویری برای **{p_name}** در سیستم ثبت نشده است.", parse_mode='Markdown')
        return
    await query.message.reply_text(f"📸 **نمونه کارهای {p_name}:**", parse_mode='Markdown')
    for img in imgs:
        await query.message.reply_photo(photo=img)

async def start_direct_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    await msg_target.reply_text("📝 جهت ثبت سفارش مستقیم یا مشاوره تلفنی، لطفاً **نام و نام خانوادگی** خود را وارد کنید:")
    return ORD_NAME

async def start_direct_order_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await start_direct_order(update, context)

async def get_ord_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_name'] = update.message.text
    await update.message.reply_text("📞 لطفاً **شماره تماس** خود را وارد کنید:")
    return ORD_PHONE

async def get_ord_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_phone'] = update.message.text
    await update.message.reply_text("🪟 **نوع پرده** مورد نظر را وارد کنید:")
    return ORD_TYPE

async def get_ord_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_type'] = update.message.text
    await update.message.reply_text("📍 لطفاً **شهر و آدرس** خود را وارد کنید:")
    return ORD_ADDRESS

async def get_ord_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_address'] = update.message.text
    order_data = (
        "📥 **سفارش / مشاوره جدید**\n\n"
        f"👤 **نام:** {context.user_data['order_name']}\n"
        f"📞 **تلفن:** {context.user_data['order_phone']}\n"
        f"🪟 **نوع پرده:** {context.user_data['order_type']}\n"
        f"📍 **آدرس:** {context.user_data['order_address']}\n"
        f"🆔 **کاربر:** @{update.effective_user.username or 'بدون آیدی'} (ID: {update.effective_user.id})"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=order_data)
    await update.message.reply_text("✅ درخواست شما ثبت شد. کارشناسان ما به زودی با شما تماس خواهند گرفت.", reply_markup=PERSISTENT_KEYBOARD)
    return ConversationHandler.END

async def calc_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    text = (
        "🚚 **محاسبه هزینه نصب، اندازه‌گیری و ارسال:**\n\n"
        "📏 **هزینه اندازه‌گیری (شیراز):** 500,000 تومان\n"
        "🛠 **هزینه نصب:** هر درگاه 500,000 تومان (پنجره تک‌تکه = ۱ درگاه)\n"
        "🚕 **کرایه حمل (شیراز):** 150,000 تومان\n"
        "📦 **ارسال به سایر شهرها:** بسته‌بندی مقاوم و ارسال با تیپاکس (پس‌کرایه)\n\n"
        "📞 جهت هماهنگی نصب در شهرستان‌ها تماس بگیرید."
    )
    await msg_target.reply_text(text, parse_mode='Markdown')

async def show_measurement_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    guide_text = (
        "📐 **آموزش جامع اندازه‌گیری پرده:**\n\n"
        "1️⃣ **خارج از چهارچوب (روکار):**\n"
        "• **عرض:** عرض پنجره + ۱۵ سانتی‌متر\n"
        "• **ارتفاع:** ارتفاع پنجره + ۲۰ سانتی‌متر\n\n"
        "2️⃣ **داخل چهارچوب (توکار):**\n"
        "• **عرض:** عرض کامل چهارچوب منفی ۱ سانتی‌متر\n"
        "• **ارتفاع:** ارتفاع کامل چهارچوب + ۲۰ سانتی‌متر\n\n"
        "📌 **توصیه می‌شود حتماً از متر فلزی استفاده کنید.**"
    )
    await msg_target.reply_text(guide_text, parse_mode='Markdown')

# --- پنل مدیریت اختصاصی (/admin) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats")],
        [InlineKeyboardButton("💵 تغییر قیمت محصولات", callback_data="admin_change_price")],
        [InlineKeyboardButton("👥 لیست آیدی کاربران", callback_data="admin_users")]
    ])
    await update.message.reply_text("⚙️ **پنل مدیریت فارس گالری:**", reply_markup=kb, parse_mode='Markdown')

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "admin_stats":
        await query.message.reply_text(f"📊 **تعداد کل کاربران:** {len(USER_LIST)} نفر")
    elif query.data == "admin_users":
        users_str = "\n".join([str(u) for u in USER_LIST])
        await query.message.reply_text(f"👥 **آیدی کاربران:**\n\n{users_str}")
    elif query.data == "admin_change_price":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="setp_پرده شید ساده")],
            [InlineKeyboardButton("پرده شید بلک اوت 🌚", callback_data="setp_پرده شید بلک اوت")],
            [InlineKeyboardButton("پرده زبرا 🦓", callback_data="setp_پرده زبرا")],
            [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="setp_پرده کرکره فلزی")]
        ])
        await query.message.reply_text("کدام محصول را جهت تغییر قیمت انتخاب می‌کنید؟", reply_markup=kb)

async def select_price_to_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("setp_", "")
    context.user_data['editing_product'] = p_name
    await query.message.reply_text(f"قیمت جدید **{p_name}** را به تومان وارد کنید:", parse_mode='Markdown')
    return SET_PR_VAL

async def save_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p_name = context.user_data.get('editing_product')
    try:
        new_val = int(update.message.text)
        PRICES[p_name] = new_val
        await update.message.reply_text(f"✅ قیمت **{p_name}** با موفقیت به {new_val:,} تومان تغییر یافت.", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("⚠️ عدد وارد شده نامعتبر است.")
    return ConversationHandler.END

async def suggest_curtain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏢 اداری و تجاری", callback_data="sugg_office")],
        [InlineKeyboardButton("🏠 مسکونی", callback_data="sugg_home")]
    ])
    await update.message.reply_text("برای چه کاربردی پرده نیاز دارید؟ 🧐", reply_markup=keyboard)
    return ConversationHandler.END

async def handle_suggestion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'sugg_office':
        msg = "پیشنهاد ما برای محیط‌های اداری و تجاری: **پرده کرکره فلزی 🏢** است."
    else:
        msg = "پیشنهاد ما برای محیط‌های مسکونی: **پرده شید ساده 🪟** یا **پرده زبرا 🦓** است."
    await query.message.reply_text(msg, parse_mode='Markdown')

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
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ میخواهم فقط استعلام قیمت پرده بگیرم", callback_data="start_inquiry")],
        [InlineKeyboardButton("2️⃣ میخواهم ثبت سفارش انجام بدم", callback_data="start_order")]
    ])
    await update.message.reply_text("❌ **دستور لغو شد.**", parse_mode='Markdown')
    await update.message.reply_text("👇 یکی از گزینه ها را انتخاب کنید:", reply_markup=inline_kb)
    return ConversationHandler.END

def main():
    TOKEN = os.environ.get("BOT_TOKEN", "8737297309:AAGcH5LLdjnJB49V2r76cpnxE8qxYcVIz9o")

    app = ApplicationBuilder().token(TOKEN).build()

    MENU_REGEX = '^(شروع 🏠|راهنمایی و پیشنهاد نوع پرده 💡|وب سایت خرید آنلاین 🌐|ساعات کاری 🕒|آدرس و شماره تماس 📍|نمونه کارها 🖼|ثبت سفارش و مشاوره مستقیم 📝|آموزش اندازه‌گیری 📐|محاسبه هزینه نصب و ارسال 🚚)$'

    price_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(select_curtain_callback, pattern="^select_")
        ],
        states={
            GET_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_width)],
            GET_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_height)]
        },
        fallbacks=[
            MessageHandler(filters.Regex(MENU_REGEX), cancel),
            CommandHandler('cancel', cancel)
        ]
    )

    direct_order_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^ثبت سفارش و مشاوره مستقیم 📝$'), start_direct_order),
            CallbackQueryHandler(start_direct_order_cb, pattern="^start_direct_order_cb$")
        ],
        states={
            ORD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_ord_name)],
            ORD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_ord_phone)],
            ORD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_ord_type)],
            ORD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_ord_address)],
        },
        fallbacks=[
            MessageHandler(filters.Regex(MENU_REGEX), cancel),
            CommandHandler('cancel', cancel)
        ]
    )

    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_price_to_change, pattern="^setp_")],
        states={SET_PR_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), save_new_price)]},
        fallbacks=[
            MessageHandler(filters.Regex(MENU_REGEX), cancel),
            CommandHandler('cancel', cancel)
        ]
    )

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('admin', admin_panel))
    
    # دریافت عکس ادمین جهت استخراج File ID
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, get_photo_file_id))

    app.add_handler(price_conv_handler)
    app.add_handler(direct_order_conv)
    app.add_handler(admin_conv)
    
    # دکمه‌های ثابت منو
    app.add_handler(MessageHandler(filters.Regex('^شروع 🏠$'), start_command))
    app.add_handler(MessageHandler(filters.Regex('^راهنمایی و پیشنهاد نوع پرده 💡$'), suggest_curtain))
    app.add_handler(MessageHandler(filters.Regex('^وب سایت خرید آنلاین 🌐$'), show_website))
    app.add_handler(MessageHandler(filters.Regex('^ساعات کاری 🕒$'), show_hours))
    app.add_handler(MessageHandler(filters.Regex('^آدرس و شماره تماس 📍$'), show_contact))
    app.add_handler(MessageHandler(filters.Regex('^نمونه کارها 🖼$'), show_portfolio_menu))
    app.add_handler(MessageHandler(filters.Regex('^آموزش اندازه‌گیری 📐$'), show_measurement_guide))
    app.add_handler(MessageHandler(filters.Regex('^محاسبه هزینه نصب و ارسال 🚚$'), calc_services))
    
    # کالبک‌ها
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(show_curtains_callback, pattern="^start_inquiry$"))
    app.add_handler(CallbackQueryHandler(start_order_callback, pattern="^start_order$"))
    app.add_handler(CallbackQueryHandler(handle_suggestion_callback, pattern="^sugg_"))
    app.add_handler(CallbackQueryHandler(show_colors_callback, pattern="^colors_"))
    app.add_handler(CallbackQueryHandler(color_selected_callback, pattern="^color_selected$"))
    app.add_handler(CallbackQueryHandler(calc_services, pattern="^show_install_info$"))
    app.add_handler(CallbackQueryHandler(show_measurement_guide, pattern="^show_measure_info$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(send_portfolio_images, pattern="^port_"))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
