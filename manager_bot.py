import os

from datetime import datetime


from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater, CallbackContext, MessageHandler,
    Filters, CommandHandler, ConversationHandler
)

from functions import get_manager_info, set_new_time


def start(update: Update, context: CallbackContext):
    context.user_data['data'] = get_manager_info(update.effective_user.name)
    if not context.user_data['data']:
        context.bot.send_message(
            update.effective_chat.id,
            text='Это чат только для менеджеров курсов Devman'
        )
        return

    context.bot.send_message(
        update.effective_chat.id,
        text=f"{context.user_data['data']['name']}, у вас {len(context.user_data['data']['teams'])} активных команд"
    )

    for team in context.user_data['data']['teams']:
        teammates = '\n'.join(team['students'])
        context.bot.send_message(
            update.effective_chat.id,
            text=f"""
Команда {team['team_id']}
{team.get('project_name', '')}
Состав: \n {teammates}
время созвона {team['call_time']}
доска в Trello {team.get('trello', 'Нет')}
чат в Телеграм {team.get('tg_chat', 'Нет')}
            """
        )


def ask_time(update: Update, context: CallbackContext):
    worktime = context.user_data['data']['working_time']
    context.bot.send_message(
        update.effective_chat.id,
        text=f"""
        Сейчас ваши часы работы с командами: {worktime[0].strftime('%H:%M')} - {worktime[1].strftime('%H:%M')}
        Если хотите их поменять, то напишите новый период в формате 'HH:MM - HH:MM'
        """
    )
    return 1


def change_time(update: Update, context: CallbackContext):
    try:
        start, finish = update.message.text.split('-', maxsplit=1)
        starttime = datetime.strptime(start.strip(), '%H:%M')
        finishtime = datetime.strptime(finish.strip(), '%H:%M')
    except ValueError:
        context.bot.send_message(
            update.effective_chat.id,
            text='Пожалуйста, введите время в корректном формате'
        )
        return 1
    set_new_time(update.effective_user.name, starttime=starttime, finishtime=finishtime)
    context.user_data['data']['working_time'] = (starttime, finishtime)
    context.bot.send_message(
        update.effective_chat.id,
        text=f"Вы поменяли время на {starttime.strftime('%H:%M')} - {finishtime.strftime('%H:%M')}"
    )
    return ConversationHandler.END


def main():
    load_dotenv()
    tg_token = os.getenv('TG_PM_TOKEN')
    updater = Updater(token=tg_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('change_time', ask_time)],
            states={
                1: [MessageHandler((Filters.text & ~Filters.command), change_time)]
            },
            fallbacks=[],
            allow_reentry=True
        )
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
