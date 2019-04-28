from telegram.ext import Updater, CommandHandler, Filters
import logging
import configparser
import databaseuse
import sqlite3

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

base = databaseuse.DatabaseUse(config['Database']['way'])


def start(bot, update):
    logger.debug('Started new chat')
    answer = """Hello! This is a tasks-reserving bot. Do not use it before the teacher registers. All names should be alnum.
                There are possible commands:
                
                for teacher: 
                /teacher_register name surname - registers a teacher (there can be only one)
                /add_student name surname group - adds a student who have added application
                /add_task name send_limit - adds a task
                /complete_task task name surname group - confirms a completed task
                /delete_reservation task name surname group - deletes a reservation
                
                for student:
                /student_register name surname group - adds student register application.
                /add_reservation task - adds a reservation to task.
    
                for all:
                /students_info - shows information about students and made tasks
                /tasks_info - shows tasks and the limit of completing it"""

    if answer is not None:
        return bot.send_message(chat_id=update.message.chat_id, text=answer)    


def student_register(bot, update):
    inp = update.message.text.split()
    for i in inp[1:]:
        if not(i.isalnum()):
            return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    if len(inp) != 4:
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    with sqlite3.connect(config['Database']['way']) as conn:
        if base.check_student(inp[1], inp[2], inp[3], conn):
            return bot.send_message(chat_id=update.message.chat_id, text="You've already sent the application")
        base.add_student(inp[1], inp[2], inp[3], str(update.message.chat_id), conn)
        conn.commit()
        return bot.send_message(chat_id=update.message.chat_id, text="Done")


def teacher_register(bot, update):
    inp = update.message.text.split()
    for i in inp[1:]:
        if not(i.isalnum()):
            return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    if len(inp) != 3:
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    with sqlite3.connect(config['Database']['way']) as conn:
        if base.check_teacher( conn):
            return bot.send_message(chat_id=update.message.chat_id, text="The teacher already exists")
        base.set_teacher(inp[1], inp[2], str(update.message.chat_id), conn)
        conn.commit()
        return bot.send_message(chat_id=update.message.chat_id, text="Done")


def add_task(bot, update):
    inp = update.message.text.split()
    for i in inp[1:]:
        if not(i.isalnum()):
            return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    if len(inp) != 3:
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    if not(inp[2].isdigit()):
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    with sqlite3.connect(config['Database']['way']) as conn:
        if base.check_task(inp[1], conn):
            return bot.send_message(chat_id=update.message.chat_id, text="The task already exists")
        base.add_task(inp[1], inp[2], conn)
        conn.commit()
        return bot.send_message(chat_id=update.message.chat_id, text="Done")


def add_student(bot, update):
    inp = update.message.text.split()
    for i in inp[1:]:
        if not(i.isalnum()):
            return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    if len(inp) != 4:
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    with sqlite3.connect(config['Database']['way']) as conn:
        if not(base.check_student(inp[1], inp[2], inp[3], conn)):
            return bot.send_message(chat_id=update.message.chat_id, text="There's no application")
        if base.is_active(inp[1], inp[2], inp[3], conn):
            return bot.send_message(chat_id=update.message.chat_id, text="Application already confirmed")
        base.set_active(inp[1], inp[2], inp[3], conn)
        conn.commit()
        return bot.send_message(chat_id=update.message.chat_id, text="Done")


def add_reservation(bot, update):
    inp = update.message.text.split()
    if len(inp) != 2:
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    if not (inp[1].isalnum()):
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    with sqlite3.connect(config['Database']['way']) as conn:
        if base.check_reservation(inp[1], str(update.message.chat_id), conn):
            return bot.send_message(chat_id=update.message.chat_id, text="You've already reserved this task")
        if not(base.check_valid_reservation(inp[1], conn)):
            return bot.send_message(chat_id=update.message.chat_id, text="The task doesn't exist.")
        base.add_reservation(inp[1], str(update.message.chat_id), conn)
        conn.commit()
        return bot.send_message(chat_id=update.message.chat_id, text="Done")


def complete_task(bot, update):
    inp = update.message.text.split()
    for i in inp[1:]:
        if not (i.isalnum()):
            return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    if len(inp) != 5:
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    with sqlite3.connect(config['Database']['way']) as conn:
        if not(base.is_active(inp[2], inp[3], inp[4], conn)):
            return bot.send_message(chat_id=update.message.chat_id, text="There's no active students with this data")
        student_chat_id = base.get_student_chat_id(inp[2], inp[3], inp[4], conn)
        if not (base.check_reservation(inp[1], student_chat_id, conn)):
            return bot.send_message(chat_id=update.message.chat_id,
                                    text="No reservations to this task from this student")
        base.confirm_reservation(inp[1], inp[2], inp[3], inp[4], conn)
        conn.commit()
        return bot.send_message(chat_id=update.message.chat_id, text="Done")


def delete_reservation(bot, update):
    inp = update.message.text.split()
    for i in inp[1:]:
        if not (i.isalnum()):
            return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    if len(inp) != 5:
        return bot.send_message(chat_id=update.message.chat_id, text="Wrong input")
    with sqlite3.connect(config['Database']['way']) as conn:
        if not(base.is_active(inp[2], inp[3], inp[4], conn)):
            return bot.send_message(chat_id=update.message.chat_id, text="There's no active students with this data")
        student_chat_id = base.get_student_chat_id(inp[2], inp[3], inp[4], conn)
        if not (base.check_reservation(inp[1], student_chat_id, conn)):
            return bot.send_message(chat_id=update.message.chat_id,
                                    text="No reservations to this task from this student")
        base.delete_reservation(inp[1], inp[2], inp[3], inp[4], conn)
        conn.commit()
        return bot.send_message(chat_id=update.message.chat_id, text="Done")


def students_info(bot, update):
    with sqlite3.connect(config['Database']['way']) as conn:
        return bot.send_message(chat_id=update.message.chat_id, text=base.get_students(conn))


def tasks_info(bot, update):
    with sqlite3.connect(config['Database']['way']) as conn:
        return bot.send_message(chat_id=update.message.chat_id, text=base.get_tasks(conn))


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():

    updater = Updater(token=config['Bot']['token'])

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('tasks_info', tasks_info))
    dp.add_handler(CommandHandler('students_info', students_info))
    dp.add_handler(CommandHandler('delete_reservation', delete_reservation))
    dp.add_handler(CommandHandler('complete_task', complete_task))
    dp.add_handler(CommandHandler('add_reservation', add_reservation))
    dp.add_handler(CommandHandler('add_student', add_student))
    dp.add_handler(CommandHandler('add_task', add_task))
    dp.add_handler(CommandHandler('teacher_register', teacher_register))
    dp.add_handler(CommandHandler('student_register', student_register))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

