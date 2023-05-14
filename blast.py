from telegram_imports import *

from supabase_db import supabase, convertSupabaseDatetime
from functools import wraps
from mastermind import attendance


# TODO
# schedule a reminder for those who haven't completed 1 week before the session


LIST_OF_ADMINS = [797737829] 

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_chat.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped

@restricted
async def blast_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    blast_id:
    1 - start of month blast message
    2 - 1st reminder
    3 - 2nd reminder
    4 - cancelled session
    5 - custom message
    """

    try:
        _value, group_id, blast_id = update.message.text.split(' ')

    except Exception as e:
        await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text='Type in the following format: /blast [group_id] [blast_id]',
    )
        
    groups = []
        
    if group_id == 'ALL':

        # TODO retrieve info
        response = supabase.table('mastermindgroup').select('group_name, session_datetime, session_location, calendar_link').execute()
        groups = response.data

    else:

        # TODO retrieve info
        response = supabase.table('mastermindgroup').select('group_name, session_datetime, session_location, calendar_link').eq('group_name', group_id).execute()
        groups = response.data

    # TODO show info for checking
    information_check_message = \
f"""
Please verify the information below before sending:
"""
    for group in groups:
        mastermind_info = {
            'group_name': group['group_name'],
            'date': convertSupabaseDatetime(group['session_datetime']).strftime('%A, %d %B %Y'),
            'time': convertSupabaseDatetime(group['session_datetime']).strftime('%I:%-M %p') + ' onwards',
            'location': group['session_location'],
            'calendar_link': group['calendar_link'],
        },
    
        information_check_message += f"\n{mastermind_info}\n"

    # TODO send to function just for looping and messaging in attendance
    context.user_data['groups'] = groups
    context.user_data['blast_id'] = blast_id

    keyboard = [['Confirm', 'Cancel']]

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text='Check details before confirmation',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, input_field_placeholder='Confirm?'),
    )

    return BLAST


def select_blast_message(blast_id, person):
    
    if blast_id == 1:
        # start of month blast
        return 
f"""
Greetings from The 100 Club Team, 

This is the start of month blast for mastermind attendance confirmation.
"""    


def isValidChatID(chat_id):
    return len(chat_id) <= 20

async def send_blast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Retrieves all groups information and ask for blast confirmation
    """
    # TODO check data integrity in supabase plus logic

    groups = context.user_data['groups']

    for group in groups:
        response = supabase.table('profiles').select('firstName, telegram_bot_id').eq('group_id', group['group_name']).execute()

        for person in response.data:

            if isValidChatID(person['telegram_bot_id']): 

                blast_id = context.user_data['blast_id']
                message = select_blast_message(blast_id, person)

                await context.bot.send_message(
                    chat_id=person['telegram_bot_id'], 
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

                await attendance(update, context)


            else:

                await context.bot.send_message(
                    chat_id=person['telegram_bot_id'], 
                    text=f"{person['firstName']} has not joined the telegram bot yet. The blast cannot be sent to them.",
                )     

async def blast_cancelled(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Blast cancelled", 
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
    user = update.message.from_user
    # logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Something unexpected happened. Report this to The 100 Club team.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


BLAST = range(1)

blast_handler = ConversationHandler(
    entry_points=[CommandHandler('blast', blast_request)],
    states={
        BLAST: [
            MessageHandler(filters.Regex('^Confirm$'), send_blast),
            MessageHandler(filters.Regex('^Cancel$'), blast_cancelled)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)