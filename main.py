# main.py
import logging
import asyncio
import nest_asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TOKEN, NOTIFICATION_CHANNEL, DEFAULT_OWNERS
from database import init_db, add_admin
from handlers import (
    start, callback_query_handler, message_handler, claim_key_command,
    ban_command, unban_command, add_owner_command
)

# Patch the event loop (useful in Termux)
nest_asyncio.apply()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

def add_default_owners():
    """Adds default owner IDs from the config into the database."""
    for owner_id in DEFAULT_OWNERS:
        add_admin(owner_id, role='owner')

# Update scheduled_notification to be a synchronous function that creates a task.
def scheduled_notification(context):
    import asyncio
    asyncio.create_task(
        context.bot.send_message(
            chat_id=NOTIFICATION_CHANNEL,
            text="Scheduled Notification: Please check the admin panel for updates."
        )
    )

async def main():
    # 1. Initialize database & add default owners
    init_db()
    add_default_owners()

    # 2. Build the Application
    application = ApplicationBuilder().token(TOKEN).build()

    # 3. Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("claim", claim_key_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("addowner", add_owner_command))
    application.add_handler(CommandHandler("help", lambda update, context: update.message.reply_text(
        "Commands:\n/start\n/claim <key>\n/ban <user_id>\n/unban <user_id>\n/addowner <user_id>"
    )))

    # 4. Register callback query and text message handlers
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # 5. Schedule notifications using the job queue
    job_queue = application.job_queue
    job_queue.run_repeating(scheduled_notification, interval=3600, first=10)

    # 6. Run the bot using run_polling()
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
    
