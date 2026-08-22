import os
import math
import logging
import jdatetime
import http.server
import socketserver
import threading
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand, BotCommandScopeChat, InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

# ---------------------------------------------------------
# پیکربندی اولیه و ثوابت
# ---------------------------------------------------------
ADMIN_ID = 333050909  
ADMIN_USERNAME = "@arhnh"
CHANNEL_USERNAME = "@irandecoration_gallery"

BOT_FOOTER = "\n\nمحاسبه قیمت پرده در ربات تلگرام فارس گالری\n@farsgallery_bot"

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

USER_LIST = {} 

PORTFOLIO_POSTS = {
    'پرده زبرا': list(range(1263, 1285)),
    'پرده شید ساده': list(range(1285, 1305)),
    'پرده کرکره فلزی': list(range(1305, 1324)),
    'پرده شید بلک اوت': list(range(1324, 1334))
}

# ---------------------------------------------------------
# سرور مجازی برای نگهداری ربات بر روی سرورهای ابری
# ---------------------------------------------------------
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Web server error: {e}")

threading.Thread(target=run_dummy_server, daemon=True).start()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ---------------------------------------------------------
# وضعیت‌های ConversationHandler
# ---------------------------------------------------------
GET_WIDTH, GET_HEIGHT = range(2)
ORD_NAME, ORD_PHONE, ORD_TYPE, ORD_ADDRESS, ORD_PHOTO_CHOICE, ORD_PHOTO, ORD_WIDTH, ORD_HEIGHT = range(2, 10)
SET_PR_VAL = 10

PERSISTENT_KEYBOARD = ReplyKeyboardMarkup([
    ['شروع 🏠'],
    ['پیشنهاد نوع پرده 💡', 'نمونه کارها 🖼'],
    ['ثبت سفارش و مشاوره مستقیم 📝', 'آموزش اندازه‌گیری 📐'],
    ['هزینه نصب و ارسال 🚚', 'وب سایت خرید آنلاین 🌐'],
    ['ساعات کاری 🕒', 'آدرس و شماره تماس 📍']
], resize_keyboard=True)

# ---------------------------------------------------------
# توابع کمکی
# ---------------------------------------------------------
def convert_to_english_digits(text: str) -> str:
    persian_digits = '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩'
    english_digits = '01234567890123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return text.translate(translation_table)

def get_jalali_date():
    return jdatetime.datetime.now().strftime('%Y/%m/%d')

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        return True

# ---------------------------------------------------------
# سیستم یادآوری و پیگیری خودکار
# ---------------------------------------------------------
async def send_followup_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.chat_id
    curtain_type = job.data.get('curtain_type', 'پرده')

    followup_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("ثبت سفارش و مشاوره 📝", callback_data="start_direct_order_cb")],
        [InlineKeyboardButton("ورود به وب‌سایت 🌐", url="https://farsgallery.com")]
    ])

    text = (
        "سلام روزتون بخیر🌸\n\n"
        f"امیدوارم حالتون عالی باشه. دیروز برای {curtain_type} استعلام قیمت گرفته بودید؛ "
        "خواستم پیگیری کنم ببینم تصمیمتون برای ثبت سفارش چی شد؟ 😊\n\n"
        "اگر سوالی در مورد رنگ‌بندی، کیفیت یا اندازه‌گیری دارید یا احتیاج به راهنمایی بیشتری هست، خوشحال می‌شیم کمکتون کنیم.\n\n"
        "📞 شماره تماس مستقیم جهت مشاوره:\n09215657634\n\nدر خدمتتون هستیم! ✨" + BOT_FOOTER
    )

    try:
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=followup_kb)
    except Exception as e:
        logging.error(f"Failed to send follow-up message to {user_id}: {e}")

# ---------------------------------------------------------
# پیام‌ها و منوهای اصلی
# ---------------------------------------------------------
async def send_join_channel_message(update: Update):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال ما", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_join")]
    ])
    msg_text = "⚠️ دسترسی محدود است!\nلطفاً ابتدا در کانال عضو شوید." + BOT_FOOTER
    if update.message:
        await update.message.reply_text(msg_text, reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg_text, reply_markup=keyboard)

async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ میخواهم فقط استعلام قیمت پرده بگیرم", callback_data="start_inquiry")],
        [InlineKeyboardButton("2️⃣ ثبت سفارش و خرید در سایت فارس گالری", callback_data="start_order")],
        [InlineKeyboardButton("3️⃣ مشاوره انتخاب پرده با کارشناسان مجموعه ما", callback_data="start_direct_order_cb")]
    ])
    welcome_msg = (
        "به ربات مجموعه هُنری فارس گالری خوش آمدید 🎨\n\n"
        "میتوانید برای استعلام قیمت بر اساس ابعاد و اندازه پرده مورد نظر خود و همچنین ثبت سفارش از این ربات به راحتی استفاده کنید." + BOT_FOOTER
    )
    if update.message:
        await update.message.reply_text(welcome_msg, reply_markup=PERSISTENT_KEYBOARD)
        await update.message.reply_text("👇 یکی از گزینه ها را انتخاب کنید:", reply_markup=inline_kb)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_msg, reply_markup=inline_kb)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_handle = f"@{user.username}" if user.username else f"{user.first_name} (بدون یوزرنیم)"
    USER_LIST[user.id] = user_handle

    if not await is_user_member(user.id, context):
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

# ---------------------------------------------------------
# استعلام قیمت و محاسبات آنلاین
# ---------------------------------------------------------
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

    await query.message.reply_text("📐 لطفاً عرض پرده را به سانتی‌متر وارد کنید (مثلاً: 150):")
    return GET_WIDTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = convert_to_english_digits(update.message.text.strip()).replace(',', '.')
    
    try:
        width = float(text)
        if width <= 0:
            raise ValueError()
        context.user_data['width'] = width
        await update.message.reply_text("📐 لطفاً ارتفاع پرده را به سانتی‌متر وارد کنید (مثلاً: 200):")
        return GET_HEIGHT
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً عرض را فقط به صورت عدد سانتی‌متر وارد کنید (مثال: 150).")
        return GET_WIDTH

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = convert_to_english_digits(update.message.text.strip()).replace(',', '.')

    try:
        height = float(text)
        if height <= 0:
            raise ValueError()

        width = context.user_data.get('width', 100)
        curtain_type = context.user_data.get('curtain_type', 'پرده زبرا')
        curtain_icon = context.user_data.get('curtain_icon', curtain_type)
        
        unit_price = PRICES.get(curtain_type, 2000000)
        rules_applied = []

        if curtain_type in ['پرده شید ساده', 'پرده شید بلک اوت']:
            min_height, min_area = 200, 2.0
            calc_height = max(height, min_height)
            if height < min_height:
                rules_applied.append("⚠️ طبق قانون محاسباتی پرده شید، ارتفاع زیر ۲۰۰ سانتی‌متر، حداقل ۲۰۰ سانتی‌متر محاسبه می‌شود.")
            area = (width / 100.0) * (calc_height / 100.0)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("⚠️ طبق قانون محاسباتی پرده شید، متراژ زیر ۲ متر مربع، حداقل ۲ متر مربع محاسبه می‌شود.")

        elif curtain_type == 'پرده زبرا':
            min_height, min_area = 150, 1.5
            calc_height = max(height, min_height)
            if height < min_height:
                rules_applied.append("⚠️ طبق قانون محاسباتی پرده زبرا، ارتفاع زیر ۱۵۰ سانتی‌متر، حداقل ۱۵۰ سانتی‌متر محاسبه می‌شود.")
            area = (width / 100.0) * (calc_height / 100.0)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("⚠️ طبق قانون محاسباتی پرده زبرا، متراژ زیر ۱.۵ متر مربع، حداقل ۱.۵ متر مربع محاسبه می‌شود.")

        elif curtain_type == 'پرده کرکره فلزی':
            min_area = 1.5
            area = (width / 100.0) * (height / 100.0)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("⚠️ طبق قانون محاسباتی کرکره فلزی، متراژ زیر ۱.۵ متر مربع، حداقل ۱.۵ متر مربع محاسبه می‌شود.")

        total_price = int(round(calc_area * unit_price))
        
        rules_text = "\n".join([f"{r}" for r in rules_applied])
        if rules_text:
            rules_text = "\n" + rules_text + "\n"

        buy_url = PRODUCT_LINKS.get(curtain_type, 'https://farsgallery.com')

        result_msg = (
            f"قیمت امروز | 🗓 {get_jalali_date()}\n"
            f"{curtain_icon}\n"
            f"📐 عرض: {int(width)} سانتی‌متر | ارتفاع: {int(height)} سانتی‌متر\n"
            f"🧮 متراژ محاسبه شده: {calc_area:.2f} متر مربع\n"
            f"{rules_text}\n"
            f"🪙 قیمت هر متر مربع: {unit_price:,} تومان\n\n"
            f"💵 قیمت نهایی با همه لوازم پرده: {total_price:,} تومان\n\n"
            f"📦 ارسال به سراسر کشور | ⭐ کیفیت درجه ۱ | 🛡 5 سال ضمانت | 🚚 تحویل 3 روز کاری"
            f"{BOT_FOOTER}"
        )

        inline_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("رنگ بندی 🎨", callback_data=f"colors_{curtain_type}"),
                InlineKeyboardButton("نمونه کارها 🖼", callback_data=f"port_{curtain_type}")
            ],
            [
                InlineKeyboardButton("آموزش اندازه‌گیری 📐", callback_data=f"mtype_{curtain_type}"),
                InlineKeyboardButton("هزینه نصب و ارسال 🚚", callback_data="show_install_info")
            ],
            [
                InlineKeyboardButton("ثبت سفارش و مشاوره 📝", callback_data="start_direct_order_cb"),
                InlineKeyboardButton("محاسبه جدید 🔄", callback_data="start_inquiry")
            ],
            [
                InlineKeyboardButton("خرید آنلاین 🛒", url=buy_url)
            ]
        ])

        await update.message.reply_text(result_msg, reply_markup=inline_kb)

        if context.job_queue:
            context.job_queue.run_once(
                send_followup_message,
                when=86400,
                chat_id=update.effective_chat.id,
                data={'curtain_type': curtain_type}
            )

        return ConversationHandler.END

    except Exception as e:
        logging.error(f"Calculation error: {e}")
        await update.message.reply_text("⚠️ لطفاً ارتفاع را فقط به صورت عدد سانتی‌متر وارد کنید (مثال: 200).")
        return GET_HEIGHT

# ---------------------------------------------------------
# بخش آموزش اندازه‌گیری (مطابق با متن‌های ارسالی)
# ---------------------------------------------------------
async def show_measurement_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("اندازه گیری پرده زبرا / شیدرول ساده / شید رول بلک اوت", callback_data="mtype_zebra_shid")],
        [InlineKeyboardButton("اندازه گیری پرده کرکره فلزی 16 میل و 25 میل", callback_data="mtype_kerkere")]
    ])
    await msg_target.reply_text("📐 نوع پرده مورد نظر را انتخاب کنید:", reply_markup=kb)

async def handle_mtype_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    raw_type = query.data.replace("mtype_", "")
    
    if raw_type in ["zebra_shid", "پرده شید ساده", "پرده شید بلک اوت", "پرده زبرا", "پرده زبرا و شید"]:
        ctype = "zebra_shid"
    else:
        ctype = "kerkere"
        
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("داخل چهار چوب (توکار)", callback_data=f"mpos_{ctype}_inside")],
        [InlineKeyboardButton("خارج چهار چوب (روکار)", callback_data=f"mpos_{ctype}_outside")]
    ])
    await query.message.reply_text("محل نصب را انتخاب کنید:", reply_markup=kb)

async def handle_mpos_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.replace("mpos_", "").split("_")
    ctype = data_parts[0]
    pos = data_parts[1]

    if ctype == "zebra_shid":
        if pos == "inside":
            exact_text = (
                "اندازه گیری پرده زبرا / شیدرول ساده / شید رول بلک اوت\n"
                "داخل چهار چوب (توکار)\n"
                "📏 **نحوه اندازه گیری پرده زبرا / شیدرول ساده / شید رول بلک اوت (نصب داخل چهارچوب):**\n"
                "🛠 **ابزار اندازه‌گیری:**استفاده از متر فلزی برای دقت بالا و جلوگیری از خطا ضروری است.\n"
                "• **عرض:** عرض چهارچوب را دقیق اندازه گرفته و 2 سانتیمتر کم میکنیم\n"
                "• **ارتفاع:** ارتفاع چهارچوب را دقیق اندازه گرفته و 15 سانتیمتر اضافه میکنیم"
            )
        else:
            exact_text = (
                "اندازه گیری پرده زبرا / شیدرول ساده / شید رول بلک اوت\n"
                "خارج چهار چوب (روکار)\n"
                "📏 **نحوه اندازه گیری پرده زبرا / شیدرول ساده / شید رول بلک اوت (نصب خارج چهارچوب):**\n"
                "🛠 **ابزار اندازه‌گیری:**استفاده از متر فلزی برای دقت بالا و جلوگیری از خطا ضروری است.\n"
                "• **عرض:** عرض چهارچوب را دقیق اندازه گرفته و 10 سانتیمتر اضافه میکنیم\n"
                "• **ارتفاع:** ارتفاع چهارچوب را دقیق اندازه گرفته و 20 سانتیمتر اضافه میکنیم"
            )
    else:
        if pos == "inside":
            exact_text = (
                "اندازه گیری پرده کرکره فلزی 16 میل و 25 میل\n"
                "داخل چهار چوب (توکار)\n"
                "📏 **نحوه اندازه گیری پرده کرکره فلزی 16 میل و 25 میل (نصب داخل چهارچوب):**\n"
                "🛠 **ابزار اندازه‌گیری:**استفاده از متر فلزی برای دقت بالا و جلوگیری از خطا ضروری است.\n"
                "• **عرض:** عرض چهارچوب را دقیق اندازه گرفته و 2 سانتیمتر کم میکنیم\n"
                "• **ارتفاع:** ارتفاع چهارچوب را دقیق اندازه گرفته و 3 سانتیمتر کم میکنیم"
            )
        else:
            exact_text = (
                "اندازه گیری پرده کرکره فلزی 16 میل و 25 میل\n"
                "خارج چهار چوب (روکار)\n"
                "📏 **نحوه اندازه گیری پرده کرکره فلزی 16 میل و 25 میل (نصب خارج چهارچوب):**\n"
                "🛠 **ابزار اندازه‌گیری:**استفاده از متر فلزی برای دقت بالا و جلوگیری از خطا ضروری است.\n"
                "• **عرض:** عرض چهارچوب را دقیق اندازه گرفته و 10 سانتیمتر اضافه میکنیم\n"
                "• **ارتفاع:** ارتفاع چهارچوب را دقیق اندازه گرفته و 10 سانتیمتر اضافه میکنیم"
            )

    await query.message.reply_text(exact_text + BOT_FOOTER)

# ---------------------------------------------------------
# ثبت سفارش و مشاوره مستقیم
# ---------------------------------------------------------
async def start_direct_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    await msg_target.reply_text("📝 جهت ثبت سفارش یا مشاوره، لطفاً نام و نام خانوادگی خود را وارد کنید:")
    return ORD_NAME

async def start_direct_order_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await start_direct_order(update, context)

async def get_ord_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_name'] = update.message.text
    await update.message.reply_text("📞 لطفاً شماره تماس خود را وارد کنید:")
    return ORD_PHONE

async def get_ord_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_phone'] = update.message.text
    await update.message.reply_text("🪟 نوع پرده مورد نظر را وارد کنید:")
    return ORD_TYPE

async def get_ord_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_type'] = update.message.text
    await update.message.reply_text("📍 لطفاً شهر و آدرس خود را وارد کنید:")
    return ORD_ADDRESS

async def get_ord_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_address'] = update.message.text
    username = update.effective_user.username
    user_handle = f"@{username}" if username else "بدون یوزرنیم"

    admin_init_msg = (
        "📥 سفارش / مشاوره جدید\n\n"
        f"👤 نام: {context.user_data.get('order_name')}\n"
        f"📞 تلفن: {context.user_data.get('order_phone')}\n"
        f"🪟 نوع پرده: {context.user_data.get('order_type')}\n"
        f"📍 آدرس: {context.user_data.get('order_address')}\n"
        f"👤 یوزرنیم: {user_handle}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_init_msg)

    next_step_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("میخوام عکس پنجره ارسال کنم 📸", callback_data="choice_send_photo")],
        [InlineKeyboardButton("میخوام اندازه پنجره رو بگم 📐", callback_data="choice_send_dim")]
    ])
    
    await update.message.reply_text(
        "✅ مشخصات شما با موفقیت ثبت شد.\nلطفاً گام بعدی خود را انتخاب کنید:",
        reply_markup=next_step_kb
    )
    return ORD_PHOTO_CHOICE

async def handle_photo_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "choice_send_photo":
        await query.message.reply_text("📸 لطفاً تصویر پنجره مورد نظر را ارسال کنید:")
        return ORD_PHOTO
    else:
        await query.message.reply_text("📐 لطفاً عرض پنجره را به سانتی‌متر وارد کنید (مثال: 180):")
        return ORD_WIDTH

async def get_ord_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    user_handle = f"@{username}" if username else "بدون یوزرنیم"

    caption_text = f"📸 تصویر جدید از مشتری\n👤 نام: {context.user_data.get('order_name')}\n👤 یوزرنیم: {user_handle}"

    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=caption_text)
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        doc_file_id = update.message.document.file_id
        await context.bot.send_document(chat_id=ADMIN_ID, document=doc_file_id, caption=caption_text)
    
    await update.message.reply_text("✅ عکس دریافت شد.\n📐 حالا لطفاً عرض پنجره را به سانتی‌متر وارد کنید (مثال: 180):")
    return ORD_WIDTH

async def get_ord_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_width'] = convert_to_english_digits(update.message.text.strip())
    await update.message.reply_text("📐 لطفاً ارتفاع پنجره را به سانتی‌متر وارد کنید (مثال: 220):")
    return ORD_HEIGHT

async def get_ord_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_height'] = convert_to_english_digits(update.message.text.strip())
    width_val = context.user_data.get('order_width')
    height_val = context.user_data.get('order_height')
    username = update.effective_user.username
    user_handle = f"@{username}" if username else "بدون یوزرنیم"

    admin_dim_msg = (
        "📐 ابعاد تکمیلی سفارش:\n\n"
        f"👤 نام: {context.user_data.get('order_name')}\n"
        f"📏 عرض: {width_val} سانتی‌متر | ارتفاع: {height_val} سانتی‌متر\n"
        f"👤 یوزرنیم: {user_handle}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_dim_msg)

    await update.message.reply_text(
        "✅ ابعاد با موفقیت ثبت شد.\n🎉 کارشناسان ما جهت تأیید نهایی به زودی با شما تماس خواهند گرفت." + BOT_FOOTER,
        reply_markup=PERSISTENT_KEYBOARD
    )
    return ConversationHandler.END

# ---------------------------------------------------------
# پنل مدیریت ربات
# ---------------------------------------------------------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats")],
        [InlineKeyboardButton("💵 تغییر قیمت محصولات", callback_data="admin_change_price")],
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users")]
    ])
    await update.message.reply_text("⚙️ پنل مدیریت فارس گالری:", reply_markup=kb)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "admin_stats":
        await query.message.reply_text(f"📊 تعداد کل کاربران: {len(USER_LIST)} نفر")
    elif query.data == "admin_users":
        if not USER_LIST:
            await query.message.reply_text("👥 هیچ کاربر فعالی ثبت نشده است.")
        else:
            users_text = "👥 لیست کاربران:\n\n" + "\n".join([f"• {u}" for u in USER_LIST.values()])
            await query.message.reply_text(users_text)
    elif query.data == "admin_change_price":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="setp_پرده شید ساده")],
            [InlineKeyboardButton("پرده شید بلک اوت 🌚", callback_data="setp_پرده شید بلک اوت")],
            [InlineKeyboardButton("پرده زبرا 🦓", callback_data="setp_پرده زبرا")],
            [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="setp_پرده کرکره فلزی")]
        ])
        await query.message.reply_text("محصول را انتخاب کنید:", reply_markup=kb)

async def select_price_to_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("setp_", "")
    context.user_data['editing_product'] = p_name
    await query.message.reply_text(f"قیمت جدید {p_name} را به تومان وارد کنید:")
    return SET_PR_VAL

async def save_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p_name = context.user_data.get('editing_product')
    raw_text = convert_to_english_digits(update.message.text.strip())
    try:
        new_val = int(raw_text)
        PRICES[p_name] = new_val
        await update.message.reply_text(f"✅ قیمت {p_name} به {new_val:,} تومان تغییر یافت.")
    except ValueError:
        await update.message.reply_text("⚠️ عدد وارد شده نامعتبر است.")
    return ConversationHandler.END

# ---------------------------------------------------------
# نمونه‌کارها (ارسال آلبوم بر اساس پست‌های کانال)
# ---------------------------------------------------------
async def send_portfolio_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("port_", "")
    post_ids = PORTFOLIO_POSTS.get(p_name, [])
    
    if not post_ids:
        await query.message.reply_text(f"⚠️ هنوز تصویری برای {p_name} ثبت نشده است." + BOT_FOOTER)
        return

    await query.message.reply_text(f"🖼 در حال دریافت و ارسال آلبوم نمونه‌کارهای {p_name} ... لطفاً شکیبا باشید.")

    fetched_photos = []
    for msg_id in post_ids:
        try:
            msg = await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=CHANNEL_USERNAME,
                message_id=msg_id
            )
            if msg.photo:
                fetched_photos.append(msg.photo[-1].file_id)
            await context.bot.delete_message(chat_id=ADMIN_ID, message_id=msg.message_id)
        except Exception as e:
            logging.error(f"Error fetching photo for msg_id {msg_id}: {e}")

    if not fetched_photos:
        await query.message.reply_text("⚠️ متأسفانه تصاویری یافت نشد.")
        return

    chunk_size = 10
    for i in range(0, len(fetched_photos), chunk_size):
        chunk = fetched_photos[i:i + chunk_size]
        if len(chunk) >= 2:
            media_group = [InputMediaPhoto(media=photo_id) for photo_id in chunk]
            try:
                await context.bot.send_media_group(
                    chat_id=update.effective_chat.id,
                    media=media_group
                )
            except Exception as e:
                logging.error(f"Error sending media group: {e}")
        elif len(chunk) == 1:
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=chunk[0]
                )
            except Exception as e:
                logging.error(f"Error sending photo: {e}")

# ---------------------------------------------------------
# خدمات دیگر و منوهای ثانویه
# ---------------------------------------------------------
async def suggest_curtain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏢 اداری و تجاری", callback_data="sugg_office")],
        [InlineKeyboardButton("🏠 مسکونی", callback_data="sugg_home")]
    ])
    await update.message.reply_text("برای چه کاربردی پرده نیاز دارید؟ 🧐", reply_markup=keyboard)

async def handle_suggestion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'sugg_office':
        msg = "پیشنهاد ما برای محیط‌های اداری: پرده کرکره فلزی 🏢 است." + BOT_FOOTER
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📐 استعلام قیمت کرکره فلزی", callback_data="select_پرده کرکره فلزی")]])
    else:
        msg = "پیشنهاد ما برای مسکونی: پرده شید 🪟 یا زبرا 🦓 است." + BOT_FOOTER
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📐 استعلام قیمت پرده زبرا", callback_data="select_پرده زبرا")],
            [InlineKeyboardButton("📐 استعلام قیمت پرده شید", callback_data="select_پرده شید ساده")]
        ])
    await query.message.reply_text(msg, reply_markup=kb)

async def show_colors_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    curtain_type = query.data.replace("colors_", "")
    colors = ["⚪️ سفید", "🩶 طوسی", "🏷 کرم / 🟤 قهوه‌ای"]
    color_buttons = [[InlineKeyboardButton(c, callback_data="color_selected")] for c in colors]
    await query.message.reply_text(f"🎨 رنگ‌بندی‌های موجود برای {curtain_type}:", reply_markup=InlineKeyboardMarkup(color_buttons))

async def color_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("رنگ انتخاب شد!")
    await query.message.reply_text("✨ جهت ثبت سفارش می‌توانید از گزینه «ثبت سفارش و مشاوره مستقیم» استفاده کنید." + BOT_FOOTER)

async def start_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg = (
        "لینک‌های خرید مستقیم از سایت:\n\n"
        f"1️⃣ پرده شید ساده: {PRODUCT_LINKS['پرده شید ساده']}\n"
        f"2️⃣ پرده شید بلک اوت: {PRODUCT_LINKS['پرده شید بلک اوت']}\n"
        f"3️⃣ پرده زبرا: {PRODUCT_LINKS['پرده زبرا']}\n"
        f"4️⃣ پرده کرکره فلزی: {PRODUCT_LINKS['پرده کرکره فلزی']}" + BOT_FOOTER
    )
    await query.message.reply_text(msg, disable_web_page_preview=True)

async def show_portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("پرده زبرا 🦓", callback_data="port_پرده زبرا")],
        [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="port_پرده شید ساده")],
        [InlineKeyboardButton("پرده شید بلک اوت 🌚", callback_data="port_پرده شید بلک اوت")],
        [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="port_پرده کرکره فلزی")]
    ])
    await update.message.reply_text("🖼 نمونه کار کدام محصول را می‌خواهید؟", reply_markup=kb)

async def calc_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    text = (
        "🚚 هزینه خدمات:\n\n"
        "📏 اندازه‌گیری (شیراز): 500,000 تومان\n"
        "🛠 نصب: هر درگاه 500,000 تومان\n"
        "🚕 حمل (شیراز): 150,000 تومان\n"
        "📦 ارسال شهرستان: تیپاکس (پس‌کرایه)" + BOT_FOOTER
    )
    await msg_target.reply_text(text)

async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📍 آدرس: شیراز، خیابان قصردشت، چهارراه عفیف‌آباد، ابتدای بلوار آوینی، نبش کوچه ۱، گالری هنری ایران دکوراسیون\n📞 تلفن: 07136277172" + BOT_FOOTER
    await update.message.reply_text(msg)

async def show_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🕒 ساعات کاری:\n☀️ صبح: 09:00 تا 13:00\n🌙 عصر: 17:00 تا 21:00" + BOT_FOOTER
    await update.message.reply_text(msg)

async def show_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🌐 وب سایت رسمی:\nwww.FarsGallery.com" + BOT_FOOTER
    await update.message.reply_text(msg)

async def handle_menu_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'شروع 🏠':
        await start_command(update, context)
    elif text == 'پیشنهاد نوع پرده 💡':
        await suggest_curtain(update, context)
    elif text == 'وب سایت خرید آنلاین 🌐':
        await show_website(update, context)
    elif text == 'ساعات کاری 🕒':
        await show_hours(update, context)
    elif text == 'آدرس و شماره تماس 📍':
        await show_contact(update, context)
    elif text == 'نمونه کارها 🖼':
        await show_portfolio_menu(update, context)
    elif text == 'ثبت سفارش و مشاوره مستقیم 📝':
        await start_direct_order(update, context)
    elif text == 'آموزش اندازه‌گیری 📐':
        await show_measurement_guide(update, context)
    elif text == 'هزینه نصب و ارسال 🚚':
        await calc_services(update, context)
    return ConversationHandler.END

async def post_init(application):
    try:
        await application.bot.set_my_commands([
            BotCommand("start", "شروع مجدد ربات"),
            BotCommand("admin", "ورود به پنل مدیریت")
        ], scope=BotCommandScopeChat(chat_id=ADMIN_ID))
    except Exception as e:
        logging.error(f"Failed to set admin commands: {e}")

# ---------------------------------------------------------
# تابع اصلی اجرای ربات (main)
# ---------------------------------------------------------
def main():
    TOKEN = os.environ.get("BOT_TOKEN", "8737297309:AAEBL9XPR9JKGZoLyw4PPIAtV2UFPAQ6lkc")
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    MENU_REGEX = '^(شروع 🏠|پیشنهاد نوع پرده 💡|وب سایت خرید آنلاین 🌐|ساعات کاری 🕒|آدرس و شماره تماس 📍|نمونه کارها 🖼|ثبت سفارش و مشاوره مستقیم 📝|آموزش اندازه‌گیری 📐|هزینه نصب و ارسال 🚚)$'

    price_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(select_curtain_callback, pattern="^select_")
        ],
        states={
            GET_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_width)],
            GET_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_height)]
        },
        fallbacks=[
            CommandHandler('start', start_command),
            MessageHandler(filters.Regex(MENU_REGEX), handle_menu_fallback)
        ],
        per_message=False,
        conversation_timeout=180
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
            ORD_PHOTO_CHOICE: [CallbackQueryHandler(handle_photo_choice, pattern="^(choice_send_photo|choice_send_dim)$")],
            ORD_PHOTO: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, get_ord_photo)],
            ORD_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_ord_width)],
            ORD_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_ord_height)]
        },
        fallbacks=[
            CommandHandler('start', start_command),
            MessageHandler(filters.Regex(MENU_REGEX), handle_menu_fallback)
        ],
        per_message=False,
        conversation_timeout=300
    )

    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_price_to_change, pattern="^setp_")],
        states={SET_PR_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), save_new_price)]},
        fallbacks=[
            CommandHandler('start', start_command),
            MessageHandler(filters.Regex(MENU_REGEX), handle_menu_fallback)
        ],
        per_message=False
    )

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('admin', admin_panel))

    app.add_handler(price_conv_handler)
    app.add_handler(direct_order_conv)
    app.add_handler(admin_conv)
    
    app.add_handler(MessageHandler(filters.Regex('^شروع 🏠$'), start_command))
    app.add_handler(MessageHandler(filters.Regex('^پیشنهاد نوع پرده 💡$'), suggest_curtain))
    app.add_handler(MessageHandler(filters.Regex('^وب سایت خرید آنلاین 🌐$'), show_website))
    app.add_handler(MessageHandler(filters.Regex('^ساعات کاری 🕒$'), show_hours))
    app.add_handler(MessageHandler(filters.Regex('^آدرس و شماره تماس 📍$'), show_contact))
    app.add_handler(MessageHandler(filters.Regex('^نمونه کارها 🖼$'), show_portfolio_menu))
    app.add_handler(MessageHandler(filters.Regex('^آموزش اندازه‌گیری 📐$'), show_measurement_guide))
    app.add_handler(MessageHandler(filters.Regex('^هزینه نصب و ارسال 🚚$'), calc_services))
    
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(show_curtains_callback, pattern="^start_inquiry$"))
    app.add_handler(CallbackQueryHandler(start_order_callback, pattern="^start_order$"))
    app.add_handler(CallbackQueryHandler(handle_suggestion_callback, pattern="^sugg_"))
    app.add_handler(CallbackQueryHandler(show_colors_callback, pattern="^colors_"))
    app.add_handler(CallbackQueryHandler(color_selected_callback, pattern="^color_selected$"))
    app.add_handler(CallbackQueryHandler(calc_services, pattern="^show_install_info$"))
    app.add_handler(CallbackQueryHandler(handle_mtype_selection, pattern="^mtype_"))
    app.add_handler(CallbackQueryHandler(handle_mpos_selection, pattern="^mpos_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(send_portfolio_images, pattern="^port_"))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
