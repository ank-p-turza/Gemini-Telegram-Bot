import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import google.generativeai as genai


os.environ["GEMINI_API_KEY"] = 'YOUR_GEMINI_API_KEY'  
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_API'

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

user_conversations = {}

code_snippets = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! How can I assist you today?')

def contains_code(text):
    code_patterns = r'\b(function|def|class|if|else|for|while|return|import|from|var|let|const)\b'
    return re.search(code_patterns, text) is not None

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_input = update.message.text

    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append(f"Human: {user_input}")
    full_context = "\n".join(user_conversations[user_id])
    response = model.generate_content(full_context)
    user_conversations[user_id].append(f"Gemini: {response.text}")

    if len(user_conversations[user_id]) > 10:
        user_conversations[user_id] = user_conversations[user_id][-10:]

    if contains_code(response.text):
        code_match = re.findall(r'```[\s\S]*?```', response.text)
        if code_match:
            keyboard = []
            for i, code in enumerate(code_match):
                snippet_id = f"code_{len(code_snippets)}"
                code_snippets[snippet_id] = code.strip('```')
                keyboard.append([InlineKeyboardButton(f"Copy Code {i+1}", callback_data=snippet_id)])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(response.text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(response.text)
    else:
        await update.message.reply_text(response.text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    snippet_id = query.data
    if snippet_id in code_snippets:
        code = code_snippets[snippet_id]
        await query.message.reply_text(f"\n\n{code}")
    else:
        await query.message.reply_text("....")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_conversations:
        user_conversations[user_id] = []
    await update.message.reply_text("Conversation history cleared.")

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()