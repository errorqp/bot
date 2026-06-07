import asyncio
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "8292638533:AAHoOZcnduUbe7qVibwl1QTwN1dettHSv4c"
ADMIN_ID = 8108050804
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

PAGES = {
    "main": {
        "text": "✨ خوش اومدی ابوالفضل!\n────────────────────\nمنوی شیشه‌ای حرفه‌ای 😎",
        "buttons": [
            ("ℹ️ درباره من", "about"),
            ("📁 نمونه‌کارها", "portfolio"),
            ("📞 ارتباط با من", "contact"),
            ("🎫 ارسال تیکت پشتیبانی", "send_ticket"),
            ("🤖 چت با هوش مصنوعی", "ai_chat"),
        ]
    },
    "about": {"text": "✨ درباره من\n────────────────────\nمن ابوالفضل هستم 😎", "buttons": []},
    "contact": {"text": "📞 راه‌های ارتباط\n────────────────────\n📩 example@gmail.com", "buttons": []},
    "portfolio": {"text": "📁 نمونه‌کارها\n────────────────────\nیک پروژه انتخاب کن:", "buttons": []},
    "send_ticket": {"text": "🎫 ارسال تیکت\n────────────────────\nپیامت رو بنویس:", "buttons": []},
    "ai_chat": {"text": "🤖 چت با هوش مصنوعی\n────────────────────\nهر سؤالی داری بپرس.", "buttons": []},
}

def ask_ai_sync(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ خطا در ارتباط با Groq:\n{e}"

async def ask_ai(prompt: str) -> str:
    return await asyncio.to_thread(ask_ai_sync, prompt)

async def render_page(query, page, context):
    data = PAGES[page]
    keyboard = []

    for text, callback in data["buttons"]:
        keyboard.append([InlineKeyboardButton(text, callback_data=callback)])

    if page != "main":
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back")])

    try:
        await query.edit_message_text(
            data["text"],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        pass

async def start(update, context):
    context.user_data["stack"] = ["main"]
    context.user_data["waiting_ticket"] = False
    context.user_data["ai_mode"] = False

    await update.message.reply_text(
        PAGES["main"]["text"],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ℹ️ درباره من", callback_data="about")],
            [InlineKeyboardButton("📁 نمونه‌کارها", callback_data="portfolio")],
            [InlineKeyboardButton("📞 ارتباط با من", callback_data="contact")],
            [InlineKeyboardButton("🎫 ارسال تیکت پشتیبانی", callback_data="send_ticket")],
            [InlineKeyboardButton("🤖 چت با هوش مصنوعی", callback_data="ai_chat")],
        ])
    )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    stack = context.user_data.get("stack", ["main"])

    if data == "back":
        if len(stack) > 1:
            stack.pop()
        context.user_data["ai_mode"] = False
        context.user_data["waiting_ticket"] = False
        await render_page(query, stack[-1], context)
        return

    if stack[-1] != data:
        stack.append(data)
    context.user_data["stack"] = stack

    context.user_data["waiting_ticket"] = (data == "send_ticket")
    context.user_data["ai_mode"] = (data == "ai_chat")

    await render_page(query, data, context)

async def receive_message(update, context):
    user_id = update.effective_user.id
    text = update.message.text

    if context.user_data.get("waiting_ticket"):
        ticket_id = context.bot_data.get("ticket_counter", 1000) + 1
        context.bot_data["ticket_counter"] = ticket_id

        context.bot_data.setdefault("tickets", {})
        context.bot_data["tickets"][ticket_id] = {
            "user_id": user_id,
            "message": text,
            "status": "open"
        }

        await context.bot.send_message(
            ADMIN_ID,
            f"🎫 *تیکت جدید #{ticket_id}*\n👤 کاربر: {user_id}\n────────────────────\n{text}",
            parse_mode="Markdown"
        )

        await update.message.reply_text("✔️ تیکتت ثبت شد.")
        context.user_data["waiting_ticket"] = False
        return

    if context.user_data.get("ai_mode"):
        await update.message.reply_text("⏳ در حال فکر کردن…")
        answer = await ask_ai(text)
        await update.message.reply_text(answer)
        return

    await update.message.reply_text("از منوی شیشه‌ای استفاده کن 🙂")

def main():
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .concurrent_updates(False) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))

    print("Bot is running on Render…")
    app.run_polling(poll_interval=1.0)

if __name__ == "__main__":
    main()
