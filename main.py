import datetime
import os.path
import logging

from json import load
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from telegram import __version__ as TG_VER


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

with open('envs.json') as env:
    env = load(env)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_html(
        rf"Hello! I will alert you on any scheduled daily event.",
        reply_markup=ForceReply(selective=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def events(context: CallbackContext = None) -> None:
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    # Call the Calendar API
    now = datetime.datetime.utcnow()
    now_iso = now.isoformat() + 'Z'  # 'Z' indicates UTC time
    tomorrow = now + datetime.timedelta(days=30) 
    tomorrow_iso = tomorrow.isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=env.get('calendar_id'),
        timeMin=now_iso,
        timeMax=tomorrow_iso,
        maxResults=100, singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    events_clean = {}
    upcoming_events = "These are your upcoming events:\n"
    for event in events:
        date = event['start'].get('dateTime', event['start'].get('date'))
        if events_clean.get(date):
            events_clean[date].append(event['summary'])
        else:
            events_clean[date] = [event['summary']]
    for event in events_clean:
        upcoming_events += f"For {event}:\n"
        for data in events_clean[event]:
            upcoming_events += f"* {data}\n"
    
    if events_clean:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=upcoming_events
        )
    else:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="No events for this week"
        )

async def launch(update: Update, context: CallbackContext):
    context.job_queue.run_daily(
        events,
        time=datetime.time(hour=12),
        chat_id=update.message.chat_id
    )
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Start scheduler"
    )

def main():
    application = Application.builder().token(
        env.get('bot_token')
    ).build()

    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler(["launch"], launch))
    
    application.run_polling()
    


if __name__ == '__main__':
    main()