import logging
import os
import http.server
import socketserver
import threading
import jdatetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)

# --- تنظیمات عمومی ---
ADMIN_ID = 333050909
CHANNEL_USERNAME = "@irandecoration_gallery"
USER_LIST = {}  # {user_id: {"username": "@...", "name": "..."}}

PRICES = {
    'پرده شید ساده': 1300000,
    'پرده شید بلک اوت': 1600000,
    'پرده زبرا': 1300000,
    'پرده کرکره فلزی': 2100000
}

PRODUCT_LINKS = {
    'پرده شید ساده': 'https://farsgallery.com/product-category/blind/shade-blind/',
    'پرده شید بلک اوت': 'https://farsgallery.com/product-category/blind/blackout-blind/',
    'پرده زبرا': 'https://farsgallery.com/product-category/blind/zebra-blind/',
    'پرده کرکره فلزی': 'https://farsgallery.com/product-category/blind/venetian-blinds/'
}

# --- لیست کامل لینک نمونه‌کارها ---
PORTFOLIO_IMAGES = {
    'پرده زبرا': [
        "https://t.me/irandecoration_gallery/1263", "https://t.me/irandecoration_gallery/1264",
        "https://t.me/irandecoration_gallery/1265", "https://t.me/irandecoration_gallery/1266",
        "https://t.me/irandecoration_gallery/1267", "https://t.me/irandecoration_gallery/1268",
        "https://t.me/irandecoration_gallery/1269", "https://t.me/irandecoration_gallery/1270",
        "https://t.me/irandecoration_gallery/1271", "https://t.me/irandecoration_gallery/1272",
        "https://t.me/irandecoration_gallery/1273", "https://t.me/irandecoration_gallery/1274",
        "https://t.me/irandecoration_gallery/1275", "https://t.me/irandecoration_gallery/1276",
        "https://t.me/irandecoration_gallery/1277", "https://t.me/irandecoration_gallery/1278",
        "https://t.me/irandecoration_gallery/1279", "https://t.me/irandecoration_gallery/1280",
        "https://t.me/irandecoration_gallery/1281", "https://t.me/irandecoration_gallery/1282",
        "https://t.me/irandecoration_gallery/1283", "https://t.me/irandecoration_gallery/1284"
    ],
    'پرده شید ساده': [
        "https://t.me/irandecoration_gallery/1285", "https://t.me/irandecoration_gallery/1286",
        "https://t.me/irandecoration_gallery/1287", "https://t.me/irandecoration_gallery/1288",
        "https://t.me/irandecoration_gallery/1289", "https://t.me/irandecoration_gallery/1290",
        "https://t.me/irandecoration_gallery/1291", "https://t.me/irandecoration_gallery/1292",
        "https://t.me/irandecoration_gallery/1293", "https://t.me/irandecoration_gallery/1294",
        "https://t.me/irandecoration_gallery/1295", "https://t.me/irandecoration_gallery/1296",
        "https://t.me/irandecoration_gallery/1297", "https://t.me/irandecoration_gallery/1298",
        "https://t.me/irandecoration_gallery/1299", "https://t.me/irandecoration_gallery/1300",
        "https://t.me/irandecoration_gallery/1301", "https://t.me/irandecoration_gallery/1302",
        "https://t.me/irandecoration_gallery/1303", "https://t.me/irandecoration_gallery/1304"
    ],
    'پرده کرکره فلزی': [
        "https://t.me/irandecoration_gallery/1305", "https://t.me/irandecoration_gallery/1306",
        "https://t.me/irandecoration_gallery/1307", "https://t.me/irandecoration_gallery/1308",
        "https://t.me/irandecoration_gallery/1309", "https://t.me/irandecoration_gallery/1310",
        "https://t.me/irandecoration_gallery/1311", "https://t.me/irandecoration_gallery/1312",
        "https://t.me/irandecoration_gallery/1313", "https://t.me/irandecoration_gallery/1314",
        "https://t.me/irandecoration_gallery/1315", "https://t.me/irandecoration_gallery/1316",
        "https://t.me/irandecoration_gallery/1317", "https://t.me/irandecoration_gallery/1318",
        "https://t.me/irandecoration_gallery/1319", "https://t.me/irandecoration_gallery/1320",
        "https://t.me/irandecoration_gallery/1321", "https://t.me/irandecoration_gallery/1322",
        "https://t.me/irandecoration_gallery/1323"
    ],
    'پرده شید بلک اوت': [
        "https://t.me/irandecoration_gallery/1324", "https://t.me/irandecoration_gallery/1325",
        "https://t.me/irandecoration_gallery/1326", "https://t.me/irandecoration_gallery/1327",
        "https://t.me/irandecoration_gallery/1328", "https://t.me/irandecoration_gallery/1329",
        "https://t.me/irandecoration_gallery/1330", "https://t.me/irandecoration_gallery/1331",
        "https://t.me/irandecoration_gallery/1332", "https://t.me/irandecoration_gallery/1333"
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
ORD_NAME, ORD_PHONE, ORD_TYPE, ORD_ADDRESS, ORD_OPTIONS, ORD_PHOTO, ORD_WIDTH, ORD_HEIGHT = range(2, 10)
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

def append_specific_footer(text: str) -> str:
    header = f"📅 تاریخ امروز: {get_jalali_date()}\n\n"
    footer = (
        "\n\n🧮 محاسبه قیمت پرده در ربات تلگرام فارس گالری\n"
        "@farsgallery_bot"
    )
    return header + text + footer

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
        "میتوانید برای استعلام قیمت بر اساس ابعاد و اندازه پرده مورد نظر خود و همچنین ثبت سفارش از این ربات به راحتی استفاده کنید.\n\n"
        "👇 یکی از گزینه ها را انتخاب کنید:"
    )
    if update.message:
        await update.message.reply_text(welcome_msg, reply_markup=inline_kb)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_msg, reply_markup=inline_kb)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_handle = f"@{user.username}" if user.username else "بدون یوزرنیم"
    USER_LIST[user.id] = {"username": user_handle, "name": user.first_name}

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

# --- استعلام قیمت ---

async def show_curtains_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    curtains_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="select_پرده شید ساده")],
        [InlineKeyboardButton("پرده شید بلک اوت 🕶️", callback_data="select_پرده شید بلک اوت")],
        [InlineKeyboardButton("پرده زبرا 🦓", callback_data="select_پرده زبرا")],
        [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="select_پرده کرکره فلزی")]
    ])
    await query.message.reply_text("👇 نوع پرده را انتخاب کنید:", reply_markup=curtains_kb)

async def select_curtain_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    curtain_type = query.data.replace("select_", "").strip()
    context.user_data['curtain_type'] = curtain_type
    
    icon_map = {
        'پرده شید ساده': 'پرده شید ساده 🪟',
        'پرده شید بلک اوت': 'پرده شید بلک اوت 🕶️',
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
        width = context.user_data.get('width', 100)
        curtain_type = context.user_data.get('curtain_type', 'پرده زبرا')
        curtain_icon = context.user_data.get('curtain_icon', curtain_type)
        
        unit_price = PRICES.get(curtain_type, 1300000)
        rules_applied = []

        if curtain_type in ['پرده شید ساده', 'پرده شید بلک اوت']:
            min_height, min_area = 200, 2.0
            calc_height = max(height, min_height)
            if height < min_height:
                rules_applied.append("به خاطر قانون پرده شید ارتفاع کمتر از 200، ما 200 در نظر میگیریم.")
            area = (width / 100) * (calc_height / 100)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("به خاطر قانون پرده شید، متراژ کمتر 2 مترمربع همان 2 مترمربع در نظر میگیریم.")

        elif curtain_type == 'پرده زبرا':
            min_height, min_area = 150, 1.5
            calc_height = max(height, min_height)
            if height < min_height:
                rules_applied.append("به خاطر قانون پرده زبرا ارتفاع کمتر از 150، ما 150 در نظر میگیریم.")
            area = (width / 100) * (calc_height / 100)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("به خاطر قانون پرده زبرا، متراژ کمتر 1.5 مترمربع همان 1.5 مترمربع در نظر میگیریم.")

        elif curtain_type == 'پرده کرکره فلزی':
            min_area = 1.5
            area = (width / 100) * (height / 100)
            calc_area = max(area, min_area)
            if area < min_area:
                rules_applied.append("به خاطر قانون پرده کرکره فلزی، متراژ کمتر از 1.5 متر مربع همان 1.5 در نظر گرفتیم.")

        total_price = int(calc_area * unit_price)
        
        rules_text = "\n".join([f"⚠️ {r}" for r in rules_applied])
        if rules_text:
            rules_text = "\n" + rules_text + "\n"

        buy_url = PRODUCT_LINKS.get(curtain_type, 'https://farsgallery.com')

        result_msg = (
            f"{curtain_icon}\n"
            f"📐 عرض: {int(width)} سانتی‌متر | ارتفاع: {int(height)} سانتی‌متر\n"
            f"🧮 متراژ: {calc_area:.2f} متر مربع\n"
            f"{rules_text}"
            f"🪙 قیمت هر متر: {unit_price:,} تومان\n\n"
            f"💵 قیمت نهایی: {total_price:,} تومان\n\n"
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

        await update.message.reply_text(append_specific_footer(result_msg), reply_markup=inline_kb)

        if context.job_queue:
            context.job_queue.run_once(
                send_followup_message,
                when=86400,
                chat_id=update.effective_chat.id,
                data={'curtain_type': curtain_type}
            )

        return ConversationHandler.END

    except Exception as e:
        logging.error(f"Error calculating price: {e}")
        await update.message.reply_text("⚠️ لطفاً ارتفاع را به صورت عدد وارد کنید (مثال: 200).")
        return GET_HEIGHT

# --- سیستم آموزش اندازه‌گیری ---

async def show_measurement_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("زبرا - شیدرول ساده - شیدرول بلک‌اوت 🪟", callback_data="mtype_zebra_shid")],
        [InlineKeyboardButton("کرکره فلزی 16میل و 25میل 🏢", callback_data="mtype_kerkere")]
    ])
    await msg_target.reply_text("📐 قصد اندازه‌گیری چه نوع پرده‌ای را دارید؟", reply_markup=kb)

async def handle_mtype_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    raw_type = query.data.replace("mtype_", "").strip()
    
    if raw_type in ["zebra_shid", "پرده شید ساده", "پرده شید بلک اوت", "پرده زبرا"]:
        ctype = "zebra"
        label = "زبرا - شیدرول ساده - شیدرول بلک‌اوت"
    else:
        ctype = "kerkere"
        label = "کرکره فلزی 16میل و 25میل"
        
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("داخل چهارچوب (توکار) 🚪", callback_data=f"mpos_{ctype}_inside")],
        [InlineKeyboardButton("خارج چهارچوب (روکار) 🖼", callback_data=f"mpos_{ctype}_outside")]
    ])
    await query.message.reply_text(f"نصب {label} شما به چه صورت است؟", reply_markup=kb)

async def handle_mpos_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.replace("mpos_", "").split("_")
    ctype = data_parts[0]
    pos = data_parts[1] if len(data_parts) > 1 else "outside"

    tools_text = (
        "🛠 انتخاب وسیله اندازه‌گیری:\n"
        "مترهای فلزی بهترین وسیله برای اندازه‌گیری هستند. "
        "نوارهای پارچه‌ای و مترهای خیاطی برای اندازه‌گیری پرده‌های پنجره مناسب نیستند و ممکن است اندکی خطا در اثر کشش ایجاد کنند.\n\n"
    )

    if ctype == "zebra":
        notes = (
            "📌 نکات مهم درباره پرده های زبرا - شیدرول ساده - شیدرول بلک‌اوت:\n"
            "۱. این نوع پرده ها به دلیل مکانیزم بالابر نیاز به محاسبة خاصی دارند.\n"
            "۲. قاب بالای این پرده ها حدود ۱۰ سانتی‌متر فضا نیاز دارد. اندازه قاب پرده از آن جهت اهمیت دارد که شما باید بالای پنجره خود حداقل ۱۰ سانتی‌متر فضا داشته باشید تا هنگام باز کردن پنجره محدودیتی نداشته باشید.\n\n"
        )
        if pos == "inside":
            detail = (
                "📏 آموزش اندازه‌گیری داخل چهارچوب (توکار) (زبرا - شیدرول ساده - شیدرول بلک‌اوت):\n"
                "۱. ابتدا متر فلزی را آماده کنید.\n"
                "۲. عرض چهارچوب پنجره را به صورت کامل اندازه‌گیری کنید. برای مطمئن شدن پیشنهاد می‌شود عرض را در سه حالت (بالا، وسط و پایین) اندازه‌گیری کرده و کوچک‌ترین عرض را یادداشت کنید. سپس حداقل 2 سانتی‌متر برای اطمینان از قرار گرفتن قاب در چهارچوب از عرض پرده کم کنید.\n"
                "۳. و حالا ارتفاع را اندازه‌گیری کرده و 10 سانتی‌متر اضافه کنید."
            )
        else:
            detail = (
                "📏 آموزش اندازه‌گیری خارج چهارچوب (روکار) (زبرا - شیدرول ساده - شیدرول بلک‌اوت):\n"
                "۱. ابتدا متر فلزی را آماده کنید.\n"
                "۲. عرض پنجره را اندازه‌گیری کنید و برای اینکه پرده به صورت کامل پنجره را بپوشاند، 15 سانتی‌متر به عرض اندازه‌گیری شده اضافه کنید.\n"
                "۳. و حالا ارتفاع را اندازه‌گیری کرده و 20 سانتی‌متر به ارتفاع اضافه کنید تا از پوشش کامل پنجره اطمینان داشته باشید.\n"
                "*(نکته: در صورتی که ریل پرده روی دیوار بالای پنجره نصب میشود 5 سانتیمتر دیگر به 20 سانتیمتر اضافه شود)*"
            )
        final_msg = tools_text + notes + detail

    else:
        if pos == "inside":
            detail = (
                "📏 آموزش اندازه‌گیری داخل چهارچوب (توکار) (کرکره فلزی 16میل - 25میل):\n"
                "۱. ابتدا متر فلزی را آماده کنید.\n"
                "۲. عرض چهارچوب پنجره را به صورت کامل اندازه‌گیری کنید. برای مطمئن شدن پیشنهاد می‌شود عرض را در سه حالت (بالا، وسط و پایین) اندازه‌گیری کرده و کوچک‌ترین عرض را یادداشت کنید.\n"
                "۳. از مقدار عرض 2 سانتی‌متر جهت جا شدن پرده کم کنید و از ارتفاع 3 سانتی‌متر کم کنید تا پرده کف پنجره قرار گیرد.\n"
                "۴. به جهت بازشو پنجره و جهت قرارگیری زنجیر بازشوی پرده دقت کنید؛ طناب و میله خلاف بازشو و سمت قسمت ثابت پنجره قرار می‌گیرد.\n\n"
                "⚠️ نکات: در حالت داخل چهارچوب (توکار) دقت کنید دستگیره پنجره به پرده گیر نکند."
            )
        else:
            detail = (
                "📏 آموزش اندازه‌گیری خارج چهارچوب (روکار) (کرکره فلزی 16میل - 25میل):\n"
                "۱. ابتدا متر فلزی را آماده کنید.\n"
                "۲. عرض چهارچوب پنجره را به صورت کامل اندازه‌گیری کنید. برای مطمئن شدن پیشنهاد می‌شود عرض را در سه حالت (بالا، وسط و پایین) اندازه‌گیری کرده و کوچک‌ترین عرض را یادداشت کنید.\n"
                "۳. به عرض 10 سانتی‌متر اضافه کنید و به ارتفاع هم 10 سانتی‌متر اضافه کنید.\n"
                "۴. به جهت بازشو پنجره و جهت قرارگیری زنجیر بازشوی پرده دقت کنید؛ طناب و میله خلاف بازشو و سمت قسمت ثابت پنجره قرار می‌گیرد."
            )
        final_msg = tools_text + detail

    await query.message.reply_text(append_specific_footer(final_msg))

# --- ثبت سفارش و مشاوره مستقیم ---

async def start_direct_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    context.user_data.clear()
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

async def show_order_options_menu(update_or_msg, context: ContextTypes.DEFAULT_TYPE):
    options_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("ارسال عکس پنجره 📸", callback_data="opt_send_photo")],
        [InlineKeyboardButton("وارد کردن ابعاد (عرض و ارتفاع) 📐", callback_data="opt_send_dim")],
        [InlineKeyboardButton("✅ ثبت نهایی سفارش", callback_data="opt_finish_order")]
    ])
    
    msg_text = (
        "✅ مشخصات شما ثبت شد.\n\n"
        "اکنون می‌توانید به دلخواه **عکس پنجره** یا **ابعاد** را وارد کنید، یا در صورت تمام شدن مراحل روی **ثبت نهایی سفارش** بزنید:"
    )
    if hasattr(update_or_msg, 'reply_text'):
        await update_or_msg.reply_text(msg_text, reply_markup=options_kb)
    else:
        await update_or_msg.message.reply_text(msg_text, reply_markup=options_kb)

async def get_ord_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_address'] = update.message.text
    await show_order_options_menu(update.message, context)
    return ORD_OPTIONS

async def handle_order_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "opt_send_photo":
        await query.message.reply_text(
            "📸 لطفاً تصویر پنجره مورد نظر را ارسال کنید:\n"
            "(می‌توانید عکس را فرستاده و سپس مراحل را ادامه دهید)"
        )
        return ORD_PHOTO
    elif query.data == "opt_send_dim":
        await query.message.reply_text("📐 لطفاً عرض پنجره را به سانتی‌متر وارد کنید (مثال: 180):")
        return ORD_WIDTH
    elif query.data == "opt_finish_order":
        return await finalize_direct_order(update, context)

async def get_ord_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = f"@{user.username}" if user.username else "بدون یوزرنیم"

    caption_text = (
        f"📸 **تصویر ارسالی از مشتری**\n\n"
        f"👤 نام: {context.user_data.get('order_name', 'ثبت نشده')}\n"
        f"📞 تلفن: {context.user_data.get('order_phone', 'ثبت نشده')}\n"
        f"🪟 نوع پرده: {context.user_data.get('order_type', 'ثبت نشده')}\n"
        f"📍 آدرس: {context.user_data.get('order_address', 'ثبت نشده')}\n"
        f"🆔 آیدی عددی: `{user.id}`\n"
        f"👤 یوزرنیم: {username}"
    )

    try:
        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=caption_text, parse_mode='Markdown')
            await update.message.reply_text("✅ عکس با موفقیت برای کارشناس ارسال شد.")
        elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('image/'):
            doc_file_id = update.message.document.file_id
            await context.bot.send_document(chat_id=ADMIN_ID, document=doc_file_id, caption=caption_text, parse_mode='Markdown')
            await update.message.reply_text("✅ عکس با موفقیت برای کارشناس ارسال شد.")
        else:
            await update.message.reply_text("⚠️ لطفاً تصویر معتبری ارسال کنید.")
            return ORD_PHOTO
    except Exception as e:
        logging.error(f"Error sending photo to admin: {e}")
        await update.message.reply_text("✅ عکس ثبت شد.")

    context.user_data['has_photo'] = True
    await show_order_options_menu(update.message, context)
    return ORD_OPTIONS

async def get_ord_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_width'] = update.message.text
    await update.message.reply_text("📐 لطفاً ارتفاع پنجره را به سانتی‌متر وارد کنید (مثال: 220):")
    return ORD_HEIGHT

async def get_ord_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_height'] = update.message.text
    await update.message.reply_text("✅ ابعاد با موفقیت ثبت شد.")
    await show_order_options_menu(update.message, context)
    return ORD_OPTIONS

async def finalize_direct_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    width_val = context.user_data.get('order_width', 'ثبت نشده')
    height_val = context.user_data.get('order_height', 'ثبت نشده')
    name_val = context.user_data.get('order_name', 'ثبت نشده')
    phone_val = context.user_data.get('order_phone', 'ثبت نشده')
    type_val = context.user_data.get('order_type', 'ثبت نشده')
    address_val = context.user_data.get('order_address', 'ثبت نشده')
    has_photo = "بله 📸" if context.user_data.get('has_photo') else "خیر"

    user = update.effective_user
    user_handle = f"@{user.username}" if user.username else "بدون یوزرنیم"

    # فرم کامل ارسال برای ادمین
    admin_final_msg = (
        "📥 **ثبت سفارش / مشاوره جدید (تکمیل شد)**\n\n"
        f"👤 **نام:** {name_val}\n"
        f"📞 **تلفن:** {phone_val}\n"
        f"🪟 **نوع پرده:** {type_val}\n"
        f"📍 **آدرس:** {address_val}\n"
        f"📏 **عرض:** {width_val}\n"
        f"📏 **ارتفاع:** {height_val}\n"
        f"🖼 **ارسال عکس:** {has_photo}\n\n"
        f"🆔 **آیدی عددی:** `{user.id}`\n"
        f"👤 **یوزرنیم:** {user_handle}"
    )
    
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_final_msg, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error sending order to admin: {e}")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_final_msg)
        except Exception as ex:
            logging.error(f"Fallback admin message failed: {ex}")

    # متن خلاصه تایید برای مشتری
    customer_confirm_msg = (
        "🎉 **سفارش / درخواست مشاوره شما با موفقیت ثبت شد!**\n\n"
        "📋 **خلاصه اطلاعات شما:**\n"
        f"👤 نام: {name_val}\n"
        f"📞 شماره تماس: {phone_val}\n"
        f"🪟 نوع پرده: {type_val}\n"
        f"📍 آدرس: {address_val}\n"
        f"📐 ابعاد: {width_val} × {height_val}\n\n"
        "✨ کارشناسان ما جهت هماهنگی و تایید نهایی به زودی با شما تماس خواهند گرفت."
    )

    try:
        if update.callback_query:
            await update.callback_query.message.reply_text(
                customer_confirm_msg,
                reply_markup=PERSISTENT_KEYBOARD,
                parse_mode='Markdown'
            )
        elif update.message:
            await update.message.reply_text(
                customer_confirm_msg,
                reply_markup=PERSISTENT_KEYBOARD,
                parse_mode='Markdown'
            )
    except Exception as e:
        logging.error(f"Error sending confirmation to customer: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(customer_confirm_msg, reply_markup=PERSISTENT_KEYBOARD)
        elif update.message:
            await update.message.reply_text(customer_confirm_msg, reply_markup=PERSISTENT_KEYBOARD)

    return ConversationHandler.END

# --- پنل مدیریت کامل ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats")],
        [InlineKeyboardButton("💵 تغییر قیمت محصولات", callback_data="admin_change_price")],
        [InlineKeyboardButton("👥 لیست کاربران (یوزرنیم و آیدی)", callback_data="admin_users")]
    ])
    await update.message.reply_text("⚙️ **پنل مدیریت فارس گالری:**", reply_markup=kb, parse_mode='Markdown')

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "admin_stats":
        await query.message.reply_text(f"📊 **تعداد کل کاربران استارت زده:** {len(USER_LIST)} نفر", parse_mode='Markdown')
    elif query.data == "admin_users":
        if not USER_LIST:
            await query.message.reply_text("👥 هیچ کاربر فعالی ثبت نشده است.")
        else:
            users_text = "👥 **لیست کاربران ربات:**\n\n"
            for uid, info in USER_LIST.items():
                users_text += f"• **نام:** {info['name']} | **یوزرنیم:** {info['username']} | **آیدی:** `{uid}`\n"
            await query.message.reply_text(users_text, parse_mode='Markdown')
    elif query.data == "admin_change_price":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="setp_پرده شید ساده")],
            [InlineKeyboardButton("پرده شید بلک اوت 🕶️", callback_data="setp_پرده شید بلک اوت")],
            [InlineKeyboardButton("پرده زبرا 🦓", callback_data="setp_پرده زبرا")],
            [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="setp_پرده کرکره فلزی")]
        ])
        await query.message.reply_text("کدام محصول را جهت تغییر قیمت انتخاب می‌کنید؟", reply_markup=kb)

async def select_price_to_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("setp_", "").strip()
    context.user_data['editing_product'] = p_name
    await query.message.reply_text(f"قیمت جدید {p_name} را به تومان (فقط عدد) وارد کنید:")
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

# --- منو و نمایش نمونه‌کارها (اصلاح شده و بدون اختلال) ---

async def show_portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_target = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    portfolio_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("پرده زبرا 🦓", callback_data="port_پرده زبرا")],
        [InlineKeyboardButton("پرده شید ساده 🪟", callback_data="port_پرده شید ساده")],
        [InlineKeyboardButton("پرده کرکره فلزی 🏢", callback_data="port_پرده کرکره فلزی")],
        [InlineKeyboardButton("پرده شید بلک اوت 🕶️", callback_data="port_پرده شید بلک اوت")]
    ])
    await msg_target.reply_text(
        "🖼 لطفاً جهت مشاهده نمونه‌کارها، نوع پرده را انتخاب کنید:",
        reply_markup=portfolio_kb
    )

async def send_portfolio_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # جداسازی دقیق کلید بدون تأثیرپذیری از ایموجی
    p_name = query.data.replace("port_", "").strip()
    imgs = PORTFOLIO_IMAGES.get(p_name, [])
    
    if not imgs:
        await query.message.reply_text(f"⚠️ هنوز تصویری برای {p_name} ثبت نشده است.")
        return
    
    chunk_size = 10
    for chunk_idx in range(0, len(imgs), chunk_size):
        chunk = imgs[chunk_idx:chunk_idx + chunk_size]
        media_group = []
        for i, img_url in enumerate(chunk):
            if chunk_idx == 0 and i == 0:
                caption = f"📸 نمونه کارهای {p_name}"
                media_group.append(InputMediaPhoto(media=img_url, caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=img_url))
        
        await update.effective_chat.send_media_group(media=media_group)

# --- هزینه نصب و ارسال ---

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
    await msg_target.reply_text(append_specific_footer(text))

# --- راهنمایی و پیشنهاد نوع پرده ---

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
        msg = "پیشنهاد ما برای محیط‌های اداری و تجاری: پرده کرکره فلزی 🏢 است."
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📐 استعلام قیمت و اندازه‌گیری کرکره فلزی", callback_data="select_پرده کرکره فلزی")]
        ])
    else:
        msg = "پیشنهاد ما برای محیط‌های مسکونی: پرده شید 🪟 یا پرده زبرا 🦓 است."
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📐 استعلام قیمت و اندازه‌گیری پرده زبرا", callback_data="select_پرده زبرا")],
            [InlineKeyboardButton("📐 استعلام قیمت و اندازه‌گیری پرده شید ساده", callback_data="select_پرده شید ساده")]
        ])
        
    await query.message.reply_text(msg, reply_markup=kb)

# --- سایر متدها ---

async def show_colors_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    curtain_type = query.data.replace("colors_", "").strip()

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
    TOKEN = os.environ.get("BOT_TOKEN", "8737297309:AAEO3ZII40K1T_q8-kdUGUBKx-HJKbdmQBo")
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
            ORD_OPTIONS: [
                CallbackQueryHandler(handle_order_options, pattern="^(opt_send_photo|opt_send_dim|opt_finish_order)$")
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

    # اولویت بالاتر هندلرهای مدیریت و ادمین
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    
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
    app.add_handler(CallbackQueryHandler(send_portfolio_images, pattern="^port_"))

    print("Bot is running...")
    app.run_polling(stop_signals=None)

if __name__ == '__main__':
    main()
