import os
import math
import logging
import jdatetime
import http.server
import socketserver
import threading
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

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

USER_LIST = {} 

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

GET_WIDTH, GET_HEIGHT = range(2)
ORD_NAME, ORD_PHONE, ORD_TYPE, ORD_ADDRESS, ORD_PHOTO_CHOICE, ORD_PHOTO, ORD_WIDTH, ORD_HEIGHT = range(2, 10)
SET_PR_VAL = 10

PERSISTENT_KEYBOARD = ReplyKeyboardMarkup([
    ['شروع 🏠'],
    ['راهنمایی و پیشنهاد نوع پرده 💡', 'نمونه کارها 🖼'],
    ['ثبت سفارش و مشاوره مستقیم 📝', 'آموزش اندازه‌گیری 📐'],
    ['هزینه نصب و ارسال 🚚', 'وب سایت خرید آنلاین 🌐'],
    ['ساعات کاری 🕒', 'آدرس و شماره تماس 📍']
], resize_keyboard=True)

def get_jalali_date():
    return jdatetime.datetime.now().strftime('%Y/%m/%d')

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        return True

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
        "📞 شماره تماس مستقیم جهت مشاوره:\n09215657634\n\nدر خدمتتون هستیم! ✨"
    )

    try:
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=followup_kb)
    except Exception as e:
        logging.error(f"Failed to send follow-up message to {user_id}: {e}")

async def send_join_channel_message(update: Update):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال ما", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_join")]
    ])
    msg_text = "⚠️ دسترسی محدود است!\nلطفاً ابتدا در کانال عضو شوید."
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
        "میتوانید برای استعلام قیمت بر اساس ابعاد و اندازه پرده مورد نظر خود و همچنین ثبت سفارش از این ربات به راحتی استفاده کنید."
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

    await query.message.reply_text("لطفاً عرض پرده را به سانتی‌متر وارد کنید (مثال: 150):")
    return GET_WIDTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        width = float(text)
        context.user_data['width'] = width
        await update.message.reply_text("لطفاً ارتفاع پرده را به سانتی‌متر وارد کنید (مثال: 200):")
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
            f"قیمت امروز | 🗓 {get_jalali_date()}\n"
            f"{curtain_icon}\n"
            f"📐 عرض: {int(width)} سانتی‌متر | ارتفاع: {int(height)} سانتی‌متر\n"
            f"🧮 متراژ: {calc_area:.2f} متر مربع\n"
            f"{rules_text}"
            f"🪙 قیمت هر متر: {unit_price:,} تومان\n\n"
            f"💵 **قیمت نهایی: {total_price:,} تومان**\n\n"
            f"📦 ارسال به سراسر کشور | ⭐ کیفیت درجه ۱ | 🛡 5 سال ضمانت | 🚚 تحویل 3 روزه"
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
                InlineKeyboardButton("شروع دوباره 🔄", callback_data="start_inquiry")
            ],
            [
                InlineKeyboardButton("خرید آنلاین 🛒", url=buy_url)
            ]
        ])

        await update.message.reply_text(result_msg, reply_markup=inline_kb, parse_mode='Markdown')

        if context.job_queue:
            context.job_queue.run_once(
                send_followup_message,
                when=86400,
                chat_id=update.effective_chat.id,
                data={'curtain_type': curtain_type}
            )

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("⚠️ لطفاً ارتفاع را به صورت عدد وارد کنید (مثال: 200).")
        return GET_HEIGHT

# --- سیستم آموزش اندازه‌گیری اصلاح شده ---

async def show_measurement_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("زبرا - شیدرول ساده - شیدرول بلک‌اوت 🪟", callback_data="mtype_zebra_shid")],
        [InlineKeyboardButton("کرکره فلزی 🏢", callback_data="mtype_kerkere")]
    ])
    await msg_target.reply_text("📐 قصد اندازه‌گیری چه نوع پرده‌ای را دارید؟", reply_markup=kb)

async def handle_mtype_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    raw_type = query.data.replace("mtype_", "")
    
    # نگاشت نام‌های فارسی یا انگلیسی به کلید استاندارد کوتاه
    if raw_type in ["zebra_shid", "پرده شیدرول ساده", "پرده شیدرول بلک اوت", "پرده زبرا"]:
        ctype = "zebra"
        label = "زبرا - شیدرول ساده - شیدرول بلک‌اوت"
    else:
        ctype = "kerkere"
        label = "کرکره فلزی"
        
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("داخل چهارچوب (توکار) 🚪", callback_data=f"mpos_{ctype}_inside")],
        [InlineKeyboardButton("خارج چهارچوب (روکار) 🖼", callback_data=f"mpos_{ctype}_outside")]
    ])
    await query.message.reply_text(f"نصب {label} شما به چه صورت است؟", reply_markup=kb)

async def handle_mpos_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # جداسازی امن دیتای کالبک
    data_parts = query.data.replace("mpos_", "").split("_")
    ctype = data_parts[0]
    pos = data_parts[1] if len(data_parts) > 1 else "outside"

    tools_text = (
        "🛠 **انتخاب وسیله اندازه‌گیری:**\n"
        "مترهای فلزی بهترین وسیله برای اندازه‌گیری هستند. "
        "نوارهای پارچه‌ای و مترهای خیاطی برای اندازه‌گیری پرده‌های پنجره مناسب نیستند و ممکن است اندکی خطا در اثر کشش ایجاد کنند.\n\n"
    )

    if ctype == "zebra":
        notes = (
            "📌 **نکات مهم درباره پرده های زبرا - شیدرول ساده - شیدرول بلک‌اوت:**\n"
            "۱. این نوع پرده ها به دلیل مکانیزم بالابر نیاز به محاسبة خاصی دارند.\n"
            "۲. قاب بالای این پرده ها حدود ۱۰ سانتی‌متر فضا نیاز دارد. اندازه قاب پرده از آن جهت اهمیت دارد که شما باید بالای پنجره خود حداقل ۱۰ سانتی‌متر فضا داشته باشید تا هنگام باز کردن پنجره محدودیتی نداشته باشید.\n\n"
        )
        if pos == "inside":
            detail = (
                "📏 **آموزش اندازه‌گیری داخل چهارچوب (زبرا - شیدرول ساده - شیدرول بلک‌اوت):**\n"
                "۱. ابتدا متر فلزی را آماده کنید.\n"
                "۲. عرض چهارچوب پنجره را به صورت کامل اندازه‌گیری کنید. برای مطمئن شدن پیشنهاد می‌شود عرض را در سه نوبت (بالا، وسط و پایین) اندازه‌گیری کرده و **کوچک‌ترین عرض** را یادداشت کنید. سپس حداقل **2 سانتی‌متر** برای اطمینان از قرار گرفتن قاب در چهارچوب از عرض پرده کم کنید.\n"
                "۳. بعد از اندازه‌گیری عرض، ارتفاع را اندازه‌گیری کرده و **20 سانتی‌متر** اضافه کنید."
            )
        else:
            detail = (
                "📏 **آموزش اندازه‌گیری خارج چهارچوب (زبرا - شیدرول ساده - شیدرول بلک‌اوت):**\n"
                "۱. ابتدا متر فلزی را آماده کنید.\n"
                "۲. عرض پنجره را اندازه‌گیری کنید و برای اینکه پرده به صورت کامل پنجره را بپوشاند، **15 سانتی‌متر** به عرض اندازه‌گیری شده اضافه کنید.\n"
                "۳. بعد از اندازه‌گیری عرض، ارتفاع را اندازه‌گیری کرده و **20 سانتی‌متر** به ارتفاع اضافه کنید تا از پوشش کامل پنجره اطمینان داشته باشید.\n"
                "*(نکته: در صورتی که ریل پرده روی دیوار بالای پنجره نصب میشود 5 سانتیمتر دیگر به 20 اضافه شود)*"
            )
        final_msg = tools_text + notes + detail

    else:  # kerkere
        if pos == "inside":
            detail = (
                "📏 **آموزش اندازه‌گیری داخل چهارچوب - توکار (کرکره فلزی):**\n"
                "۱. ابتدا دقت کنید در این حالت به دلیل نیاز به نصب پایه پرده به بالای درگاه پنجره، از استحکام این قسمت از دیوار جهت انجام سوراخ‌کاری با دریل برای پیچ کردن پایه‌ها مطمئن شوید.\n"
                "۲. عرض و ارتفاع پنجره را در سه جا اندازه‌گیری کنید (چپ، وسط، راست برای ارتفاع و بالا، وسط، پایین برای عرض) و مبنا را **عدد کوچک‌تر** بگیرید.\n"
                "۳. از مقدار عرض **2 سانتی‌متر** جهت جا شدن پرده کم کنید و به ارتفاع **3 سانتی‌متر** کم کنید تا پرده کف پنجره قرار گیرد.\n"
                "۴. به جهت بازشو پنجره و جهت قرارگیری زنجیر بازشوی پرده دقت کنید؛ طناب و میله خلاف بازشو و سمت قسمت ثابت پنجره قرار می‌گیرد.\n\n"
                "⚠️ *نکات:* ممکن است قاب پنجره دیده شود. دقت کنید دستگیره پنجره به پرده گیر نکند."
            )
        else:
            detail = (
                "📏 **آموزش اندازه‌گیری خارج چهارچوب - روکار (کرکره فلزی):**\n"
                "۱. همانند روش قبلی عرض و ارتفاع پنجره را در سه جا اندازه‌گیری کرده و مبنا را **عدد کوچک‌تر** بگیرید.\n"
                "۲. **در عرض پرده:** جهت جلوگیری از عبور نور از کنار پرده در چپ یا راست، حداقل از هر طرف ۵ سانتی‌متر (در مجموع **۱۰ سانتی‌متر**) اضافه کنید.\n"
                "۳. **در ارتفاع پرده:** اگر مانعی در پایین پرده مثل رادیاتور، پیشخوان یا کابینت قرار ندارد، جهت همپوشانی در حالت سایه و نیمه‌سایه حتماً **10 سانتی‌متر** به ارتفاع اضافه کنید.\n"
                "۴. فاصله بالای پرده (محل نصب پایه) باید به اندازه کافی جهت سوراخ‌کاری باشد. در این حالت می‌توانید پرده را به صورت دیواری یا سقفی نصب کنید."
            )
        final_msg = tools_text + detail

    await query.message.reply_text(final_msg, parse_mode='Markdown')

# --- ثبت سفارش ---

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
        "📥 سفارش / مشاوره جدید (مشخصات اولیه)\n\n"
        f"👤 نام: {context.user_data.get('order_name')}\n"
        f"📞 تلفن: {context.user_data.get('order_phone')}\n"
        f"🪟 نوع پرده: {context.user_data.get('order_type')}\n"
        f"📍 آدرس: {context.user_data.get('order_address')}\n"
        f"👤 یوزرنیم مشتری: {user_handle}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_init_msg)

    next_step_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("میخوام عکس پنجره ارسال کنم 📸", callback_data="choice_send_photo")],
        [InlineKeyboardButton("میخوام اندازه پنجره رو بگم 📐", callback_data="choice_send_dim")]
    ])
    
    await update.message.reply_text(
        "✅ مشخصات شما با موفقیت ثبت شد.\n\n"
        "لطفاً گام بعدی خود را انتخاب کنید:",
        reply_markup=next_step_kb
    )
    return ORD_PHOTO_CHOICE

async def handle_photo_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "choice_send_photo":
        await query.message.reply_text(
            "📸 لطفاً تصویر پنجره مورد نظر را ارسال کنید:\n"
            "⚠️ اگر چند تصویر دارید، همه را یکجا ارسال کنید."
        )
        return ORD_PHOTO
    else:
        await query.message.reply_text("📐 لطفاً عرض پنجره را به سانتی‌متر وارد کنید (مثال: 180):")
        return ORD_WIDTH

async def get_ord_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    user_handle = f"@{username}" if username else "بدون یوزرنیم"

    caption_text = (
        f"📸 تصویر ارسال شده توسط مشتری\n\n"
        f"👤 نام: {context.user_data.get('order_name')}\n"
        f"👤 یوزرنیم مشتری: {user_handle}"
    )

    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=caption_text)
        await update.message.reply_text("✅ عکس با موفقیت دریافت و برای کارشناس ارسال شد.")
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        doc_file_id = update.message.document.file_id
        await context.bot.send_document(chat_id=ADMIN_ID, document=doc_file_id, caption=caption_text)
        await update.message.reply_text("✅ عکس با موفقیت دریافت و برای کارشناس ارسال شد.")
    
    await update.message.reply_text("📐 حالا لطفاً عرض پنجره را به سانتی‌متر وارد کنید (مثال: 180):")
    return ORD_WIDTH

async def get_ord_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_width'] = update.message.text
    await update.message.reply_text("📐 لطفاً ارتفاع پنجره را به سانتی‌متر وارد کنید (مثال: 220):")
    return ORD_HEIGHT

async def get_ord_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_height'] = update.message.text
    width_val = context.user_data.get('order_width')
    height_val = context.user_data.get('order_height')
    username = update.effective_user.username
    user_handle = f"@{username}" if username else "بدون یوزرنیم"

    admin_dim_msg = (
        "📐 ابعاد تکمیلی ثبت‌شده مشتری:\n\n"
        f"👤 نام: {context.user_data.get('order_name')}\n"
        f"📏 عرض: {width_val} سانتی‌متر\n"
        f"📏 ارتفاع: {height_val} سانتی‌متر\n"
        f"👤 یوزرنیم مشتری: {user_handle}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_dim_msg)

    await update.message.reply_text(
        "✅ ابعاد و اندازه‌ها با موفقیت ثبت گردید.\n\n"
        "🎉 کارشناسان ما جهت تأیید نهایی به زودی با شما تماس خواهند گرفت.",
        reply_markup=PERSISTENT_KEYBOARD
    )
    return ConversationHandler.END

# --- پنل مدیریت ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats")],
        [InlineKeyboardButton("💵 تغییر قیمت محصولات", callback_data="admin_change_price")],
        [InlineKeyboardButton("👥 لیست کاربران (یوزرنیم)", callback_data="admin_users")]
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
            users_text = "👥 لیست یوزرنیم کاربران ربات:\n\n" + "\n".join([f"• {u}" for u in USER_LIST.values()])
            await query.message.reply_text(users_text)
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
    await query.message.reply_text(f"قیمت جدید {p_name} را به تومان وارد کنید:")
    return SET_PR_VAL

async def save_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p_name = context.user_data.get('editing_product')
    try:
        new_val = int(update.message.text)
        PRICES[p_name] = new_val
        await update.message.reply_text(f"✅ قیمت {p_name} با موفقیت به {new_val:,} تومان تغییر یافت.")
    except ValueError:
        await update.message.reply_text("⚠️ عدد وارد شده نامعتبر است.")
    return ConversationHandler.END

# --- ارسال آلبومی تصاویر نمونه‌کار ---

async def send_portfolio_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("port_", "")
    imgs = PORTFOLIO_IMAGES.get(p_name, [])
    if not imgs:
        await query.message.reply_text(f"⚠️ هنوز تصویری برای {p_name} ثبت نشده است.")
        return
    
    media_group = []
    for i, img_id in enumerate(imgs):
        if i == 0:
            media_group.append(InputMediaPhoto(media=img_id, caption=f"📸 نمونه کارهای {p_name}"))
        else:
            media_group.append(InputMediaPhoto(media=img_id))

    await update.effective_chat.send_media_group(media=media_group)

# --- راهنمایی و پیشنهاد نوع پرده (به‌روزرسانی شده) ---

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
        msg = "پیشنهاد ما برای محیط‌های اداری و تجاری: **پرده کرکره فلزی 🏢** است."
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📐 استعلام قیمت و اندازه‌گیری کرکره فلزی", callback_data="select_پرده کرکره فلزی")]
        ])
    else:
        msg = "پیشنهاد ما برای محیط‌های مسکونی: **پرده شید 🪟** یا **پرده زبرا 🦓** است."
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📐 استعلام قیمت و اندازه‌گیری پرده زبرا", callback_data="select_پرده زبرا")],
            [InlineKeyboardButton("📐 استعلام قیمت و اندازه‌گیری پرده شید ساده", callback_data="select_پرده شید ساده")]
        ])
        
    await query.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')

# --- سایر متدها ---

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
    await query.message.reply_text("🎨 رنگ‌بندی‌های موجود:", reply_markup=InlineKeyboardMarkup(color_buttons))

async def color_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("رنگ انتخاب شد!")
    await query.message.reply_text("✨ جهت ثبت نهایی سفارش می‌توانید از دکمه «ثبت سفارش و مشاوره مستقیم» استفاده کنید.")

async def start_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    msg = (
        "لطفاً نوع پرده مورد نظر خود را جهت ورود به لینک خرید انتخاب کنید:\n\n"
        f"1️⃣ پرده شید ساده\n🔗 {PRODUCT_LINKS['پرده شید ساده']}\n\n"
        f"2️⃣ پرده شید بلک اوت\n🔗 {PRODUCT_LINKS['پرده شید بلک اوت']}\n\n"
        f"3️⃣ پرده زبرا\n🔗 {PRODUCT_LINKS['پرده زبرا']}\n\n"
        f"4️⃣ پرده کرکره فلزی\n🔗 {PRODUCT_LINKS['پرده کرکره فلزی']}"
    )
    await query.message.reply_text(msg, disable_web_page_preview=True)

async def show_portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("پرده زبرا 🦓", callback_data="port_پرده زبرا")],
        [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="port_پرده شید ساده")],
        [InlineKeyboardButton("پرده شید بلک اوت 🌚", callback_data="port_پرده شید بلک اوت")],
        [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="port_پرده کرکره فلزی")]
    ])
    await update.message.reply_text("🖼 نمونه کار کدام محصول را می‌خواهید مشاهده کنید؟", reply_markup=kb)

async def calc_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    text = (
        "🚚 محاسبه هزینه نصب، اندازه‌گیری و ارسال:\n\n"
        "📏 هزینه اندازه‌گیری (شیراز): 500,000 تومان\n"
        "🛠 هزینه نصب: هر درگاه 500,000 تومان\n"
        "🚕 کرایه حمل (شیراز): 150,000 تومان\n"
        "📦 ارسال به سایر شهرها: با تیپاکس (پس‌کرایه)"
    )
    await msg_target.reply_text(text)

async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📍 آدرس و شماره تماس:\n\n"
        "شیراز، خیابان قصردشت، چهارراه عفیف‌آباد، ابتدای بلوار آوینی، نبش کوچه یک، مجموعه گالری هنری ایران دکوراسیون (فارس گالری)\n\n"
        "📞 شماره تماس: 07136277172"
    )
    await update.message.reply_text(msg)

async def show_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🕒 ساعات کاری مجموعه:\n\n☀️ صبح: از 09:00 تا 13:00\n🌙 عصر: از 17:00 تا 21:00"
    await update.message.reply_text(msg)

async def show_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🌐 وب سایت خرید آنلاین:\nwww.FarsGallery.com"
    await update.message.reply_text(msg)

# مدیریت لغو هوشمند دکمه‌ها
async def handle_menu_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'شروع 🏠':
        await start_command(update, context)
    elif text == 'راهنمایی و پیشنهاد نوع پرده 💡':
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

def main():
    TOKEN = os.environ.get("BOT_TOKEN", "8737297309:AAGTYSqVz0vEDrMHgZCLfDAyglGCAuvOb8g")
    app = ApplicationBuilder().token(TOKEN).build()

    MENU_REGEX = '^(شروع 🏠|راهنمایی و پیشنهاد نوع پرده 💡|وب سایت خرید آنلاین 🌐|ساعات کاری 🕒|آدرس و شماره تماس 📍|نمونه کارها 🖼|ثبت سفارش و مشاوره مستقیم 📝|آموزش اندازه‌گیری 📐|هزینه نصب و ارسال 🚚)$'

    price_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(select_curtain_callback, pattern="^select_")
        ],
        states={
            GET_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_width)],
            GET_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_height)]
        },
        fallbacks=[MessageHandler(filters.Regex(MENU_REGEX), handle_menu_fallback)]
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
            ORD_PHOTO_CHOICE: [
                CallbackQueryHandler(handle_photo_choice, pattern="^(choice_send_photo|choice_send_dim)$")
            ],
            ORD_PHOTO: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, get_ord_photo)
            ],
            ORD_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_ord_width)],
            ORD_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), get_ord_height)]
        },
        fallbacks=[MessageHandler(filters.Regex(MENU_REGEX), handle_menu_fallback)]
    )

    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_price_to_change, pattern="^setp_")],
        states={SET_PR_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(MENU_REGEX), save_new_price)]},
        fallbacks=[MessageHandler(filters.Regex(MENU_REGEX), handle_menu_fallback)]
    )

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('admin', admin_panel))

    app.add_handler(price_conv_handler)
    app.add_handler(direct_order_conv)
    app.add_handler(admin_conv)
    
    app.add_handler(MessageHandler(filters.Regex('^شروع 🏠$'), start_command))
    app.add_handler(MessageHandler(filters.Regex('^راهنمایی و پیشنهاد نوع پرده 💡$'), suggest_curtain))
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
