#!/usr/bin/env python

from datetime import datetime
import logging
import os

from dotenv import load_dotenv
from telegram import (KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          DispatcherHandlerStop, Filters, MessageHandler,
                          Updater)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

myusers = {
    'DontPanic_42': {
        'username': 'DontPanic_42',
        'first_name': 'Михаил',
        'id': '12345',
    },
    'belgorod_admin': {
        'username': 'belgorod_admin',
        'first_name': 'Александр',
        'id': '23456',
    },
    'gtimg': {
        'username': 'gtimg',
        'first_name': 'Тим',
        'id': '34567',
    },
    'Michalbl4': {
        'username': 'Michalbl4',
        'first_name': 'Михаил',
        'id': '45678',
    },
}

# states for conversation
(
    SELECT_WEEK,
    SELECT_TIME_RANGE,
    CANCEL,
    ASK_ANY_TIME,
    ADJUST_TIME,
    FINISH,
) = range(6)

# states for project
(
    NO_ACTIVE_PROJECT,
    NEW_PROJECT,
    WAIT_REGISTRATION,
    ACTIVE_PROJECT,
) = range(1, 5)

##### Для отладки #####
text_status = {
    NO_ACTIVE_PROJECT: "Нет активного проекта",
    NEW_PROJECT: "Стартует новый проект",
    WAIT_REGISTRATION: "Ожидание формирования групп",
    ACTIVE_PROJECT: "Группы сформированы"
}


def change_status(update: Update, context: CallbackContext):
    if context.user_data["project_status"] == ACTIVE_PROJECT:
        context.user_data["project_status"] = NO_ACTIVE_PROJECT
    else:
        context.user_data["project_status"] += 1
    update.message.reply_text(
        f"статус изменен на {text_status[context.user_data['project_status']]}")
########################


def find_student(tg_username: str) -> tuple[bool, str]:
    db_answer = {
        'id': '@Michalbl4',
        'name': 'Михаил Миронов',
        'level': 'novice',
        'status': 3,
        'start_time': datetime.time(19, 0),
        'finish_time': datetime.time(20, 45),
        'project_date': None,
        'in_project': True,
        'team_id': 2,
        'current_team': 'DVMN Май #1',
        'call_time': datetime.time(8, 47, 49),
        'students': [
            'Михаил @DontPanic_42',
            'Михаил Миронов @Michalbl4',
            ' @belgorod_admin'
        ],
        'PM': 'Тим Гайгеров'
    }
    
    myuser = myusers.get(tg_username)
    if myuser:
        return (True, myuser["id"], myuser["first_name"])
    return (False, "", "")


def get_active_project_status(context) -> int:
    return context.user_data.get("project_status", NO_ACTIVE_PROJECT)


def get_group_description(student_id: str) -> str:
    desc = [
        "Созвон вашей группы с 18:00 до 18:30",
        "Проект менеджер: @gtimg",
        "Вот описание проекта: https://docs.google.com/",
    ]
    return "\n".join(desc)


def get_weeks() -> dict:
    return {
        "с 01.06": "12345",
        "с 08.06": "23456"
    }


def get_time_ranges(week_id):
    return {
        "c 10 до 12": "1232",
        "с 15 до 17": "454545",
        "с 18 до 20": "34343",
    }


def get_adjust_time_ranges(range_id):
    return {
        "1232": {
            "c 10 до 11": "1232",
            "с 11 до 12": "454545",
        },
        "454545": {
            "c 15 до 16": "1232",
            "с 16 до 17": "454545",
        },
        "34343": {
            "c 18 до 19": "1232",
            "с 19 до 20": "454545",
        }
    }[range_id]


def check_user(update: Update, context: CallbackContext) -> None:
    is_student, student_id, student_name = find_student(user.username)
    if not is_student:
        update.message.reply_text(
            "Этот чат только для студентов курсов Devman")
        raise DispatcherHandlerStop()
    context.user_data["student_id"] = student_id
    context.user_data["student_name"] = student_name

    context.job_queue.run_repeating(
        calback_30,
        interval=30,
        first=10,
        context=update.message.chat_id
    )


def check_project_status(update: Update, context: CallbackContext) -> None:
    if context.user_data["project_status"] == NO_ACTIVE_PROJECT:
        update.message.reply_text(
            "Сейчас нет активного проекта. Как только он появится я тебе напишу")
        raise DispatcherHandlerStop()
    if context.user_data["project_status"] == WAIT_REGISTRATION:
        update.message.reply_text(
            "Подожди пока формируем группы, как будет готово - напишу")
        raise DispatcherHandlerStop()
    if context.user_data["project_status"] == ACTIVE_PROJECT:
        group_description = get_group_description(
            context.user_data["student_id"])
        update.message.reply_text(group_description)
        raise DispatcherHandlerStop


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Привет {context.user_data["student_name"]}.')


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Я не умею поддерживать разговор")


def unknow_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Таким командам не обучен")


def start_conversation(update: Update, context: CallbackContext) -> int:
    context.chat_data.clear()
    context.chat_data["weeks"] = get_weeks()
    keyboard = [[KeyboardButton(week)]
                for week in context.chat_data["weeks"].keys()]
    keyboard.append([KeyboardButton("не смогу принять участие")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "Начинаем новый проект. На какой неделе тебе будет удобно участвовать?",
        reply_markup=reply_markup)
    return SELECT_WEEK


def select_week(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    if answer == "не смогу принять участие":
        update.message.reply_text(
            "Очень жаль. Тогда эту неделю работай со своим ментором",
            reply_markup=ReplyKeyboardRemove())
        context.chat_data["cancel_project"] = True
        finish_registration(update, context)
        return ConversationHandler.END
    week_id = context.chat_data["weeks"].get(answer)
    if not week_id:
        update.message.reply_text("Выбери неделю для участия в проекте")
        return SELECT_WEEK
    context.chat_data["select_week_id"] = week_id
    context.chat_data["select_week"] = answer

    context.chat_data["time_ranges"] = get_time_ranges(week_id)
    keyboard = [[KeyboardButton(time_range)]
                for time_range in context.chat_data["time_ranges"].keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "На этой неделе есть время для созвонов",
        reply_markup=reply_markup)
    return SELECT_TIME_RANGE


def select_time_range(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    time_range_id = context.chat_data["time_ranges"].get(answer)
    if not time_range_id:
        update.message.reply_text("Выбери время для созвонов")
        return SELECT_TIME_RANGE
    context.chat_data["select_time_range_id"] = time_range_id
    context.chat_data["select_time_range"] = answer
    keyboard = [
        [KeyboardButton("в любое")],
        [KeyboardButton("уточнить")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        f"В промежутке {answer} ты доступен в любое время?",
        reply_markup=reply_markup)
    return ASK_ANY_TIME


def ask_any_time(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    if answer == "в любое":
        finish_registration(update, context)
        return ConversationHandler.END
    if answer == "уточнить":
        context.chat_data["adjust_time_ranges"] = get_adjust_time_ranges(
            context.chat_data["select_time_range_id"])
        keyboard = [[KeyboardButton(
            time_range)] for time_range in context.chat_data["adjust_time_ranges"].keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            "Уточни время",
            reply_markup=reply_markup)
        return ADJUST_TIME
    update.message.reply_text(
        f"В промежутке {context.chat_data['select_time_range']} ты доступен в любое время?")
    return ASK_ANY_TIME


def adjust_time(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    time_range_id = context.chat_data["adjust_time_ranges"].get(answer)
    if not time_range_id:
        update.message.reply_text("Уточни время")
        return ADJUST_TIME
    context.chat_data["select_time_range_id"] = time_range_id
    context.chat_data["select_time_range"] = answer
    finish_registration(update, context)
    return ConversationHandler.END


def finish_registration(update: Update, context: CallbackContext):
    if not context.chat_data.get("cancel_project", False):
        text = [
            "Ок, подытожим:",
            "ты хочешь принять участие в проекте",
            f"на неделе {context.chat_data['select_week']},",
            f"время созвонов {context.chat_data['select_time_range']}",
        ]
        update.message.reply_text(
            "\n".join(text), reply_markup=ReplyKeyboardRemove())
    change_status(update, context)


def calback_30(context: CallbackContext):
    context.bot.send_message(
        chat_id=context.job.context, text='A single message with 30s delay')


def main() -> None:
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.all, check_user), 0)
    dispatcher.add_handler(CommandHandler("start", start), 1)
    dispatcher.add_handler(MessageHandler(
        Filters.command, check_project_status), 2)

    start_conversation_handler = MessageHandler(
        Filters.command, start_conversation)
    registration_states = {
        SELECT_WEEK: [MessageHandler(Filters.text & ~Filters.command, select_week)],
        SELECT_TIME_RANGE: [MessageHandler(Filters.text & ~Filters.command, select_time_range)],
        ASK_ANY_TIME: [MessageHandler(Filters.text & ~Filters.command, ask_any_time)],
        ADJUST_TIME: [MessageHandler(Filters.text & ~Filters.command, adjust_time)],
        FINISH: [MessageHandler(Filters.text & ~Filters.command, select_time_range)],
    }
    registration_handler = ConversationHandler(
        entry_points=[start_conversation_handler],
        states=registration_states,
        fallbacks=[start_conversation_handler])

    dispatcher.add_handler(CommandHandler("help", help_command), 3)
    dispatcher.add_handler(CommandHandler("changestatus", change_status), 1)
    dispatcher.add_handler(registration_handler, 3)

    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, echo), 3)
    dispatcher.update_persistence()
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
