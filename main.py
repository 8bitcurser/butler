from json import load

from telegram.ext import Application, CommandHandler

from commands import start

def main():
    with open('envs.json') as env:
        env = load(env)
    application = Application.builder().token(
        env.get('bot_token')
    ).build()
    application.add_handler(CommandHandler(["start", "help"], start))
    application.run_polling()


if __name__ == '__main__':
    main()