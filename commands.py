import datetime
import logging

from json import load

from google_client import get_events
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

with open('envs.json') as env:
    env = load(env)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def events(context: CallbackContext = None) -> None:
    events = get_events(env.get('calendar_id'))
    upcoming_events = "Next events:\n"
    for event in events:
        upcoming_events += f"{event}:\n"
        upcoming_events += f"```\n"
        for data in events[event]:
            upcoming_events += f"* {data}\n"
        upcoming_events += f"```\n"

    if events:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=upcoming_events
        )
    else:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="No events for this week"
        )

async def start(update: Update, context: CallbackContext):
    context.job_queue.run_daily(
        events,
        time=datetime.time(hour=12),
        chat_id=update.message.chat_id
    )
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="I'll start watching over your calendar."
    )