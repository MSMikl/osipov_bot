import os

from datetime import time

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CallbackContext, MessageHandler,
    Filters, CommandHandler, ConversationHandler, CallbackQueryHandler
)

from functions import get_manager_info, get_team_info, close_team


ALL_TEAMS = 1
DISTINCT_TEAM = 2
TIME_ASKING = 3
TIME_SELECT = 4

def start(update: Update, context: CallbackContext):
    context.user_data['data'] = get_manager_info(update.effective_user.name)
    if not context.user_data['data']:
        context.bot.send_message(
            update.effective_chat.id,
            text='Это чат только для менеджеров курсов Devman'
        )
        return

    if not context.user_data['data']['teams']:
        keyboard = [[InlineKeyboardButton('Выбрать часы работы', callback_data='timechange')]]
        context.bot.send_message(
            update.effective_chat.id,
            text=f"""
                У вас нет активных команд.
                Ваши часы: {time.strftime(context.user_data['data']['working_time'][0], '%H:%M')} - {time.strftime(context.user_data['data']['working_time'][1], '%H:%M')}
                Хотите поменять часы работы?
            """,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TIME_ASKING

    context.bot.send_message(
        update.effective_chat.id,
        text=f"{context.user_data['data']['name']}, у вас {len(context.user_data['data']['teams'])} активных команд"
    )

    for team in context.user_data['data']['teams']:
        keyboard = [[InlineKeyboardButton(
            f"Команда {team['team_id']}", callback_data=team['team_id']
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            update.effective_chat.id,
            text=f"""
                Команда {team['team_id']}
                {team.get('project_name', '')}
                время созвона {team['call_time']}
                доска в Trello {team.get('trello', 'Нет')}
                чат в Телеграм {team.get('tg_chat', 'Нет')}
            """,
            reply_markup=reply_markup
        )
    return ALL_TEAMS


def team_choosing(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(
            'Завершить проект',
            callback_data=update.callback_query.data
        )],
        [InlineKeyboardButton(
            'Вернуться к списку команд',
            callback_data='back'
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    team = get_team_info(int(update.callback_query.data))
    context.bot.send_message(
        update.effective_chat.id,
        text=f"""
            Команда {team['team_id']}
Состав {', '.join(team['students'])}
""",
        reply_markup=reply_markup
    )
    update.callback_query.answer()
    return DISTINCT_TEAM


def team_actions(update: Update, context: CallbackContext):
    if update.callback_query.data != 'back':
        close_team(int(update.callback_query.data), update.effective_user.name)
    update.callback_query.edit_message_reply_markup(reply_markup=None)
    start(update=update, context=context)
    return ALL_TEAMS


def time_asking(update: Update, context: CallbackContext):
    times = context.user_data['data'].get('working_time')
    update.callback_query.edit_message_reply_markup(reply_markup=None)
    if times:
        time10 = times == (time(hour=10), time(hour=12))
        time18 = times == (time(hour=18), time(hour=20))
        keyboard = [
            [InlineKeyboardButton(('\xF0\x9F\x98\x81' if time10 else '') + "10:00 - 12:00", callback_data=10)],
            [InlineKeyboardButton(('\xF0\x9F\x98\x81' if time18 else '') + "18:00 - 20:00", callback_data=18)],
            [InlineKeyboardButton("Другое время", callback_data=0)]
        ]
        context.bot.send_message(
            update.effective_chat.id,
            text='Выберите подходящие вам временные промежутки',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return TIME_SELECT


# def time_choosing(update: Update, context: CallbackContext):
#     if update.callback_query.data


def main():
    load_dotenv()
    tg_token = os.getenv('TG_PM_TOKEN')
    updater = Updater(token=tg_token)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    conversation = ConversationHandler(
        entry_points=[start_handler],
        states={
            ALL_TEAMS: [CallbackQueryHandler(team_choosing)],
            DISTINCT_TEAM: [CallbackQueryHandler(team_actions)],
            TIME_ASKING: [CallbackQueryHandler(time_asking)]
        },
        fallbacks=[],
        allow_reentry=True
    )

    dispatcher.add_handler(conversation)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
