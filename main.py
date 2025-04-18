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


@bot.message_handler(commands=["broadcast"])
def broadcast_command(message):
    # Only allow owners to use the broadcast command.
    if str(message.from_user.id) not in config.OWNERS:
        bot.reply_to(message, "🚫 You are not authorized to use this command.")
        return

    # Expecting the command in the format: /broadcast <message>
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /broadcast <message>")
        return

    broadcast_text = parts[1]

    # Retrieve all user Telegram IDs from the database.
    from db import get_connection
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users")
    rows = c.fetchall()
    c.close()
    conn.close()

    count = 0
    for row in rows:
        try:
            # Each row is a tuple; telegram_id is the first element.
            bot.send_message(row[0], broadcast_text)
            count += 1
        except Exception as e:
            print(f"Error sending broadcast to {row[0]}: {e}")

    bot.reply_to(message, f"Broadcast sent to {count} users.")

@bot.message_handler(commands=["deduct"])
def deduct_command(message):
    # Only allow owners to use the deduct command.
    if str(message.from_user.id) not in config.OWNERS:
        bot.reply_to(message, "🚫 You are not authorized to use this command.")
        return

    # Expecting the command in the format: /deduct <user_id> <points>
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /deduct <user_id> <points>")
        return

    user_id = parts[1]
    try:
        points = int(parts[2])
    except ValueError:
        bot.reply_to(message, "Points must be a number.")
        return

    from db import get_user, update_user_points
    user = get_user(user_id)
    if not user:
        bot.reply_to(message, f"User {user_id} not found.")
        return

    current_points = int(user.get("points", 0))
    new_points = current_points - points

    update_user_points(user_id, new_points)
    bot.reply_to(message, f"Deducted {points} points from user {user_id}. New balance: {new_points} pts.")


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
    
