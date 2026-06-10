from bale import Bot, Message, CallbackQuery
from bale import InlineKeyboardMarkup, InlineKeyboardButton
from bale.handlers import CommandHandler, CallbackQueryHandler
from bale.checks import Data

TOKEN = "1707286533:8RiZ3SLHubKYeU9qMV3WVWx2cKHuGVDIiMg"

bot = Bot(TOKEN)


@bot.handle(CommandHandler("start"))
async def start(message: Message):

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="💰 استعلام قیمت",
            callback_data="price"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 خرید",
            callback_data="buy"
        ),
        row=2
    )

    await message.reply(
        "🎨 به ربات فارس گالری خوش آمدید\n\nیکی از گزینه‌ها را انتخاب کنید:",
        components=keyboard
    )


@bot.handle(CallbackQueryHandler(Data("price")))
async def price(callback: CallbackQuery):

    await callback.answer("استعلام قیمت")

    await callback.message.reply(
        "💰 بخش استعلام قیمت\n\nاینجا بعداً انتخاب پرده و محاسبه قیمت را اضافه می‌کنیم."
    )


@bot.handle(CallbackQueryHandler(Data("buy")))
async def buy(callback: CallbackQuery):

    await callback.answer("خرید")

    await callback.message.reply(
        "🛒 لینک خرید:\nhttps://farsgallery.com"
    )


bot.run()
