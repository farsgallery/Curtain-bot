import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

PRICES = {"shid": 1980000, "zara": 2325000, "karkareh": 2970000}
MIN_HEIGHT = {"shid": 2.0, "zara": 1.5, "karkareh": 0}
MIN_AREA = {"shid": 2.0, "zara": 1.5, "karkareh": 1.5}

SELECTING_TYPE, ENTERING_WIDTH, ENTERING_HEIGHT = range(3)

app = Flask(__name__)

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("پرده شید", callback_data="shid")],
        [InlineKeyboardButton("پرده زبرا", callback_data="zara")],
        [InlineKeyboardButton("پرده کرکره", callback_data="karkareh")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("سلام! 👋\nنوع پرده رو انتخاب کن:", reply_markup=reply_markup)
    return SELECTING_TYPE

async def select_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data["curtain_type"] = query.data
    type_name = {"shid": "شید", "zara": "زبرا", "karkareh": "کرکره"}[query.data]
    await query.edit_message_text(f"پرده {type_name} انتخاب شد.\n\nعرض پرده رو به متر وارد کن (مثلاً 2.5):")
    return ENTERING_WIDTH

async def get_width(update: Update, context: CallbackContext):
    try:
        width = float(update.message.text)
        if width <= 0:
            await update.message.reply_text("لطفاً عدد مثبت وارد کن:")
            return ENTERING_WIDTH
        context.user_data["width"] = width
        curtain_type = context.user_data["curtain_type"]
        min_height = MIN_HEIGHT[curtain_type]
        if min_height > 0:
            await update.message.reply_text(f"ارتفاع پرده رو به متر وارد کن (حداقل {min_height}m):")
            return ENTERING_HEIGHT
        else:
            return await calculate_price(update, context)
    except ValueError:
        await update.message.reply_text("لطفاً عدد وارد کن:")
        return ENTERING_WIDTH

async def get_height(update: Update, context: CallbackContext):
    try:
        height = float(update.message.text)
        if height <= 0:
            await update.message.reply_text("لطفاً عدد مثبت وارد کن:")
            return ENTERING_HEIGHT
        context.user_data["height"] = height
        return await calculate_price(update, context)
    except ValueError:
        await update.message.reply_text("لطفاً عدد وارد کن:")
        return ENTERING_HEIGHT

async def calculate_price(update: Update, context: CallbackContext):
    ctype = context.user_data["curtain_type"]
    width = context.user_data["width"]
    height = context.user_data.get("height", 0)
    area = width * height
    min_h = MIN_HEIGHT[ctype]
    min_a = MIN_AREA[ctype]
    if min_h > 0 and height < min_h:
        await update.message.reply_text(f"❌ حداقل ارتفاع {min_h} متر است.")
        return ConversationHandler.END
    if area < min_a:
        await update.message.reply_text(f"❌ حداقل متراژ {min_a} متر مربع است.")
        return ConversationHandler.END
    price_per_sqm = PRICES[ctype]
    total_price = area * price_per_sqm
    type_name = {"shid": "شید", "zara": "زبرا", "karkareh": "کرکره"}[ctype]
    result = f"""✅ محاسبه قیمت پرده {type_name}:

📐 ابعاد:
   عرض: {width} متر
   ارتفاع: {height} متر
   مساحت: {area:.2f} متر مربع

💰 قیمت هر متر مربع: {price_per_sqm:,} تومان

💵 قیمت نهایی: {total_price:,} تومان"""
    await update.message.reply_text(result)
    keyboard = [[InlineKeyboardButton("🔄 محاسبه مجدد", callback_data="restart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("میخوای دوباره حساب کنی؟", reply_markup=reply_markup)
    return ConversationHandler.END

BOT_TOKEN = os.environ.get("BOT_TOKEN")

application = Application.builder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", sta…
