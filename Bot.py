import os
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

# --- تنظیمات مدیر و وب‌سایت ---
ADMIN_ID = 265825395  # آیدی مدیریت
ADMIN_USERNAME = "@irdglry"
CHANNEL_USERNAME = "@irandecoration_gallery"

PRODUCT_LINKS = {
    'پرده شید ساده': 'https://farsgallery.com/product-category/curtains/shid/',
    'پرده شید بلک اوت': 'https://farsgallery.com/product-category/curtains/shid/',
    'پرده زبرا': 'https://farsgallery.com/product-category/curtains/zebra/simple/',
    'پرده کرکره فلزی': 'https://farsgallery.com/product-category/curtains/cercere/'
}

# لیست متغیر قیمت‌ها (قابل تغییر از پنل مدیریت)
PRICES = {
    'پرده شید ساده': 1980000,
    'پرده شید بلک اوت': 3350000,
    'پرده زبرا': 2325000,
    'پرده کرکره فلزی': 2970000
}

# آمار کاربران
USER_LIST = set()

# تصاویر نمونه کارها
PORTFOLIO_IMAGES = {
    'پرده زبرا': [
        'https://s6.uupload.ir/files/zebra1_123.jpg',
        'https://s6.uupload.ir/files/zebra2_123.jpg'
    ],
    'پرده شید ساده': ['https://s6.uupload.ir/files/shid1_123.jpg'],
    'پرده شید بلک اوت': ['https://s6.uupload.ir/files/blackout1_123.jpg'],
    'پرده کرکره فلزی': ['https://s6.uupload.ir/files/kerkere1_123.jpg']
}

# وب‌سرور مجازی Render
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

# وضعیت‌های Conversation
GET_WIDTH, GET_HEIGHT = range(2)
ORD_NAME, ORD_PHONE, ORD_TYPE, ORD_ADDRESS = range(2, 6)
SET_PR_VAL = 6

# کیبورد اصلی بدون تغییر فرم
PERSISTENT_KEYBOARD = ReplyKeyboardMarkup([
    ['شروع 🏠', 'استعلام قیمت 💰'],
    ['نمونه کارها 🖼', 'ثبت سفارش و مشاوره 📝'],
    ['آموزش اندازه‌گیری 📐', 'محاسبه هزینه نصب و ارسال 🚚'],
    ['وب سایت خرید آنلاین 🌐', 'ساعات کاری 🕒'],
    ['آدرس و شماره تماس 📍']
], resize_keyboard=True)

def get_jalali_date():
    return jdatetime.datetime.now().strftime('%Y/%m/%d')

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_LIST.add(user_id)

    if not await is_user_member(user_id, context):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_join")]
        ])
        await update.message.reply_text("⚠️ **لطفاً ابتدا در کانال ما عضو شوید.**", reply_markup=keyboard, parse_mode='Markdown')
        return

    await update.message.reply_text("به ربات مجموعه هنری فارس گالری خوش آمدید 🎨", reply_markup=PERSISTENT_KEYBOARD)

# --- منوی استعلام قیمت (مشابه قبل) ---
async def start_inquiry_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("پرده شید ساده", callback_data="select_پرده شید ساده")],
        [InlineKeyboardButton("پرده شید بلک اوت", callback_data="select_پرده شید بلک اوت")],
        [InlineKeyboardButton("پرده زبرا", callback_data="select_پرده زبرا")],
        [InlineKeyboardButton("پرده کرکره فلزی", callback_data="select_پرده کرکره فلزی")]
    ])
    await update.message.reply_text("لطفاً نوع پرده مورد نظر را برای استعلام قیمت انتخاب کنید:", reply_markup=kb)

async def select_curtain_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['curtain_type'] = query.data.replace("select_", "")
    await query.message.reply_text("لطفاً **عرض** پرده را به **سانتی‌متر** وارد کنید (مثال: 150):", parse_mode='Markdown')
    return GET_WIDTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['width'] = float(update.message.text)
        await update.message.reply_text("لطفاً **ارتفاع** پرده را به **سانتی‌متر** وارد کنید (مثال: 200):", parse_mode='Markdown')
        return GET_HEIGHT
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً عدد معتبر وارد کنید.")
        return GET_WIDTH

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        width = context.user_data['width']
        curtain_type = context.user_data['curtain_type']

        unit_price = PRICES.get(curtain_type, 2000000)
        calc_area = max((width / 100) * (height / 100), 1.5 if 'زبرا' in curtain_type or 'کرکره' in curtain_type else 2.0)
        total_price = int(calc_area * unit_price)

        result_msg = (
            f"🗓 **تاریخ:** {get_jalali_date()}\n"
            f"🪟 **نوع پرده:** {curtain_type}\n"
            f"📐 **ابعاد:** {int(width)} × {int(height)} سانتی‌متر\n"
            f"🧮 **متراژ محاسبه‌شده:** {calc_area:.2f} مترمربع\n"
            f"🪙 **قیمت هر مترمربع:** {unit_price:,} تومان\n"
            f"💵 **قیمت نهایی حدودی:** {total_price:,} تومان\n\n"
            f"🛡 **2 سال ضمانت** | 🚚 **ارسال سراسری**"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 خرید آنلاین", url=PRODUCT_LINKS.get(curtain_type, 'https://farsgallery.com'))]])
        await update.message.reply_text(result_msg, reply_markup=kb, parse_mode='Markdown')
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً عدد معتبر وارد کنید.")
        return GET_HEIGHT

# --- ثبت سفارش مستقیم (مدیریت) ---
async def start_order_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 جهت ثبت سفارش یا مشاوره تلفنی، لطفاً **نام و نام خانوادگی** خود را وارد کنید:")
    return ORD_NAME

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
    await update.message.reply_text("✅ درخواست شما ثبت شد. کارشناسان ما با شما تماس خواهند گرفت.", reply_markup=PERSISTENT_KEYBOARD)
    return ConversationHandler.END

# --- نمونه کارها ---
async def show_portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("پرده زبرا", callback_data="port_پرده زبرا")],
        [InlineKeyboardButton("پرده شید ساده", callback_data="port_پرده شید ساده")],
        [InlineKeyboardButton("پرده شید بلک اوت", callback_data="port_پرده شید بلک اوت")],
        [InlineKeyboardButton("پرده کرکره فلزی", callback_data="port_پرده کرکره فلزی")]
    ])
    await update.message.reply_text("🖼 نمونه کار کدام محصول را می‌خواهید مشاهده کنید؟", reply_markup=kb)

async def send_portfolio_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("port_", "")
    imgs = PORTFOLIO_IMAGES.get(p_name, [])
    await query.message.reply_text(f"📸 **نمونه کارهای {p_name}:**", parse_mode='Markdown')
    for img in imgs:
        await query.message.reply_photo(photo=img)

# --- محاسبه هزینه نصب و ارسال ---
async def calc_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚚 **محاسبه هزینه نصب، اندازه‌گیری و ارسال:**\n\n"
        "📏 **هزینه اندازه‌گیری (شیراز):** 500,000 تومان\n"
        "🛠 **هزینه نصب:** هر درگاه 500,000 تومان\n"
        "🚕 **کرایه حمل (شیراز):** 150,000 تومان\n"
        "📦 **ارسال به سایر شهرها:** با بسته‌بندی مقاوم توسط تیپاکس (پس‌کرایه)\n\n"
        "📞 جهت هماهنگی نصب در شهرستان‌ها تماس بگیرید."
    )
    await update.message.reply_text(text, parse_mode='Markdown')

# --- آموزش اندازه‌گیری ---
async def show_measurement_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = (
        "📐 **آموزش اندازه‌گیری پرده:**\n\n"
        "1️⃣ **خارج از چهارچوب:**\n"
        "• **عرض:** عرض پنجره + ۱۵ سانتی‌متر\n"
        "• **ارتفاع:** ارتفاع پنجره + ۲۰ سانتی‌متر\n\n"
        "2️⃣ **داخل چهارچوب:**\n"
        "• **عرض:** عرض چهارچوب منفی ۱ سانتی‌متر\n"
        "• **ارتفاع:** ارتفاع چهارچوب + ۲۰ سانتی‌متر\n\n"
        "📌 *توصیه می‌شود حتماً از متر فلزی استفاده کنید.*"
    )
    await update.message.reply_text(guide_text, parse_mode='Markdown')

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
            [InlineKeyboardButton("پرده شید ساده", callback_data="setp_پرده شید ساده")],
            [InlineKeyboardButton("پرده شید بلک اوت", callback_data="setp_پرده شید بلک اوت")],
            [InlineKeyboardButton("پرده زبرا", callback_data="setp_پرده زبرا")],
            [InlineKeyboardButton("پرده کرکره فلزی", callback_data="setp_پرده کرکره فلزی")]
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عمل لغو شد.", reply_markup=PERSISTENT_KEYBOARD)
    return ConversationHandler.END

def main():
    TOKEN = os.environ.get("BOT_TOKEN", "8737297309:AAGcH5LLdjnJB49V2r76cpnxE8qxYcVIz9o")
    app = ApplicationBuilder().token(TOKEN).build()

    price_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^استعلام قیمت 💰$'), start_inquiry_menu),
            CallbackQueryHandler(select_curtain_callback, pattern="^select_")
        ],
        states={
            GET_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_width)],
            GET_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    order_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^ثبت سفارش و مشاوره 📝$'), start_order_flow)],
        states={
            ORD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ord_name)],
            ORD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ord_phone)],
            ORD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ord_type)],
            ORD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ord_address)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_price_to_change, pattern="^setp_")],
        states={SET_PR_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_price)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('admin', admin_panel))
    app.add_handler(price_conv)
    app.add_handler(order_conv)
    app.add_handler(admin_conv)

    app.add_handler(MessageHandler(filters.Regex('^شروع 🏠$'), start_command))
    app.add_handler(MessageHandler(filters.Regex('^نمونه کارها 🖼$'), show_portfolio_menu))
    app.add_handler(MessageHandler(filters.Regex('^آموزش اندازه‌گیری 📐$'), show_measurement_guide))
    app.add_handler(MessageHandler(filters.Regex('^محاسبه هزینه نصب و ارسال 🚚$'), calc_services))

    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(send_portfolio_images, pattern="^port_"))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
