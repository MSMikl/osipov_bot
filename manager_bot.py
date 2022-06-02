from ast import In
import os

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CallbackContext, MessageHandler,
    Filters, CommandHandler, ConversationHandler, CallbackQueryHandler
)

from functions import get_manager_info, get_team_info, close_team


ALL_TEAMS = 1
DISTINCT_TEAM = 2

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
    if update.callback_query.data == 'back':
        start(update=update, context=context)
        return ALL_TEAMS
    else:
        close_team(int(update.callback_query.data), update.effective_user.name)
        start(update=update, context=context)
        return ALL_TEAMS


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
            DISTINCT_TEAM: [CallbackQueryHandler(team_actions)]
        },
        fallbacks=[]
    )

    dispatcher.add_handler(conversation)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
