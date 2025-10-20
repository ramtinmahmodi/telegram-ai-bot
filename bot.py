import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@YourChannelUsername"
CHANNEL_LINK = "https://t.me/YourChannelUsername"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            welcome_text = "🎉 Welcome to AI Bot!\n\nNow you can use the bot. Send me any message and I'll help you!"
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
        else:
            await send_join_required_message(update, context)
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        await send_join_required_message(update, context)

async def send_join_required_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ I Joined", callback_data="check_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "👋 Welcome!\n\n"
        "To use this AI bot, you need to join our channel first.\n"
        "Please join the channel below and then click 'I Joined' button."
    )
    
    if update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_membership":
        user_id = query.from_user.id
        
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
            if member.status in ['member', 'administrator', 'creator']:
                success_text = "✅ Perfect! Now you can use the bot.\n\nSend me any message and I'll help you!"
                await query.edit_message_text(success_text, parse_mode='Markdown')
            else:
                await query.answer("❌ You haven't joined the channel yet!", show_alert=True)
        except Exception as e:
            logging.error(f"Error in callback: {e}")
            await query.answer("❌ Error checking membership!", show_alert=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await send_join_required_message(update, context)
            return
    except Exception as e:
        logging.error(f"Error checking membership: {e}")
        await update.message.reply_text("❌ Error verifying channel membership!")
        return

    user_message = update.message.text

    try:
        API_URL = "https://api.groq.com/openai/v1/chat/completions"
        API_KEY = "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"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7
        }

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            bot_reply = response_data["choices"][0]["message"]["content"]
            await update.message.reply_text(bot_reply)
        else:
            await update.message.reply_text("❌ AI service is temporarily unavailable.")

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Please try again later!")

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

logging.info("🤖 Bot is starting...")
application.run_polling()
