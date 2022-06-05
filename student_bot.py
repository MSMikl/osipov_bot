#!/usr/bin/env python

import logging
import os
from datetime import date, timedelta, time

from dotenv import load_dotenv
from telegram import (KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          DispatcherHandlerStop, Filters, MessageHandler,
                          Updater)

from functions import check_for_new_date, get_student_info, set_student

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


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
    CANCEL_PROJECT,
    NO_ACTIVE_PROJECT,
    NEW_PROJECT,
    WAIT_REGISTRATION,
    ACTIVE_PROJECT,
) = range(5)

##### Для отладки #####
text_status = {
    NO_ACTIVE_PROJECT: "Нет активного проекта",
    NEW_PROJECT: "Стартует новый проект",
    WAIT_REGISTRATION: "Ожидание формирования групп",
    ACTIVE_PROJECT: "Группы сформированы"
}


def change_status(update: Update, context: CallbackContext):
    if context.user_data['status'] == ACTIVE_PROJECT:
        context.user_data['status'] = NO_ACTIVE_PROJECT
    else:
        context.user_data['status'] += 1
    update.message.reply_text(
        f"статус изменен на {text_status[context.user_data['status']]}")
########################


def get_active_project_status(context) -> int:
    return context.user_data.get("project_status", NO_ACTIVE_PROJECT)


def get_group_description(data: dict) -> str:
    desc = [
        f"Созвон вашей группы в {data['call_time']:%H:%M}",
        f"Проект менеджер: {data['PM']}",
        f"Вот описание проекта: {data.get('description', 'отсутствует')}",
        f"Доска в Trello: {data.get('trello', 'отсутствует')}",
        "",
        "Состав группы:",
        '\n'.join(data['students']),
    ]
    return "\n".join(desc)


def get_weeks(project_date: date) -> dict:
    second_date = project_date + timedelta(days=7)
    return {
        f"с {project_date:%d.%m}": project_date,
        f"с {second_date:%d.%m}": second_date,
    }


def get_time_ranges():
    return {
        "c 10 до 12": (time(10, 0), time(12, 0)),
        "с 18 до 20": (time(18, 0), time(20, 0)),
    }


def get_adjust_time_ranges(range_id):
    return {
        "c 10 до 12": {
            "c 10 до 11": (time(10, 0), time(11, 0)),
            "с 11 до 12": (time(11, 0), time(12, 0)),
        },
        "с 18 до 20": {
            "c 18 до 19": (time(18, 0), time(19, 0)),
            "с 19 до 20": (time(19, 0), time(20, 0)),
        }
    }[range_id]


def check_user(update: Update, context: CallbackContext) -> None:
    base_response = get_student_info(
        update.effective_user.name, update.effective_chat.id)
    if not base_response:
        update.message.reply_markdown(
            "Этот чат только для студентов курсов [Devman](https://dvmn.org)")
        raise DispatcherHandlerStop()
    context.user_data.update(base_response)


def check_project_status(update: Update, context: CallbackContext) -> None:
    if context.user_data['status'] == NO_ACTIVE_PROJECT:
        update.message.reply_text(
            "Сейчас нет активного проекта. Как только он появится, я тебе напишу")
        raise DispatcherHandlerStop()
    if context.user_data['status'] == WAIT_REGISTRATION:
        update.message.reply_text(
            "Подожди пока формируем группы, как будет готово - напишу")
        raise DispatcherHandlerStop()
    if context.user_data['status'] == ACTIVE_PROJECT:
        group_description = get_group_description(context.user_data)
        update.message.reply_text(group_description)
        raise DispatcherHandlerStop()


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        f"Привет {context.user_data['name']}.",
        reply_markup=ReplyKeyboardRemove())


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Я не умею поддерживать разговор")


def unknow_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Таким командам не обучен")


def start_conversation(update: Update, context: CallbackContext) -> int:
    context.chat_data.clear()
    context.chat_data["weeks"] = get_weeks(context.user_data["project_date"])
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
    week_date = context.chat_data["weeks"].get(answer)
    if not week_date:
        update.message.reply_text("Выбери неделю для участия в проекте")
        return SELECT_WEEK
    context.chat_data["selected_date"] = week_date
    context.chat_data["selected_week"] = answer
    context.chat_data["time_ranges"] = get_time_ranges()
    keyboard = [[KeyboardButton(time_range)]
                for time_range in context.chat_data["time_ranges"].keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "На этой неделе есть время для созвонов",
        reply_markup=reply_markup)
    return SELECT_TIME_RANGE


def select_time_range(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    if not context.chat_data["time_ranges"].get(answer):
        update.message.reply_text("Выбери время для созвонов")
        return SELECT_TIME_RANGE
    context.chat_data["selected_time_range"] = answer
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
        context.chat_data["selected_time"] = context.chat_data["time_ranges"].get(
            context.chat_data["selected_time_range"])
        finish_registration(update, context)
        return ConversationHandler.END
    if answer == "уточнить":
        context.chat_data["time_ranges"] = get_adjust_time_ranges(
            context.chat_data["selected_time_range"])
        keyboard = [[KeyboardButton(
            time_range)] for time_range in context.chat_data["time_ranges"].keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            "Уточни время",
            reply_markup=reply_markup)
        return ADJUST_TIME
    update.message.reply_text(
        f"В промежутке {context.chat_data['selected_time_range']} ты доступен в любое время?")
    return ASK_ANY_TIME


def adjust_time(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    selected_time = context.chat_data["time_ranges"].get(answer)
    if not selected_time:
        update.message.reply_text("Уточни время")
        return ADJUST_TIME
    context.chat_data["selected_time_range"] = answer
    context.chat_data["selected_time"] = selected_time
    finish_registration(update, context)
    return ConversationHandler.END


def finish_registration(update: Update, context: CallbackContext):
    if not context.chat_data.get("cancel_project"):
        text = [
            "Ок, подытожим:",
            "ты хочешь принять участие в проекте",
            f"на неделе {context.chat_data['selected_week']},",
            f"время созвонов {context.chat_data['selected_time_range']}",
        ]
        update.message.reply_text(
            "\n".join(text), reply_markup=ReplyKeyboardRemove())
    change_status(update, context)
    data = {
        'id': context.user_data["id"],
        'week': context.chat_data.get("selected_date"),
        'start_time': context.chat_data.get("selected_time", (None, None))[0],
        'end_time': context.chat_data.get("selected_time", (None, None))[1],
        'status': (CANCEL_PROJECT if context.chat_data.get("cancel_project") else WAIT_REGISTRATION)
    }
    set_student(data)


def job_calback(context: CallbackContext):
    new_project = check_for_new_date()
    if new_project:
        keyboard = [
            [KeyboardButton("/start")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        for chat_id in new_project:
            context.bot.send_message(
                chat_id=chat_id,
                text='Есть новая информация. Начнем?',
                reply_markup=reply_markup,
            )


def main() -> None:
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue
    job = job_queue.run_repeating(job_calback, 60, 5)

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
