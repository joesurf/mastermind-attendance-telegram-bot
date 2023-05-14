from telegram_imports import *

from database import read_one_query, read_all_query, execute_query
from supabase_db import supabase, convertSupabaseDatetime
from unknown import cancel

# mastermind flow
ATTENDANCE, CONFIRMATION, AVAILABLE, UNAVAILABLE, UNSURE, QUESTIONNAIRE, COMPLETE = range(7)
END = ConversationHandler.END


async def information(chat_id):
    person = {
        'contact_info': {
            'email': '',
            'first_name': ''     
        },
        'mastermind_group_name': '',
        'invited': False
    }

    response = supabase.table('profiles').select("firstName, email, mastermind").eq("telegram_bot_id", chat_id).execute()

    if response.data:
        person['contact_info']['first_name'] = response.data[0]['firstName']
        person['contact_info']['email'] = response.data[0]['email']
        person['mastermind_group_name'] = response.data[0]['mastermind']

        return person
    else:
        return None


async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    # verify person
    if 'person' not in context.user_data or not context.user_data['person']:

        chat_id = update.effective_chat.id 

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text='Please wait while we verify your status...', 
        )

        person = await information(chat_id)
        context.user_data['person'] = person

    else:
        person = context.user_data['person']


    if not person:

        bot_mastermind_unverified = \
f"""
Hello there, it seems that you haven't been verified. Click any of the options below and our team will respond shortly.

Please verify before continuing: /verify 
"""
        await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_mastermind_unverified)

        return END

    person = context.user_data['person']

    if person['invited']:
        other_group = person['mastermind_info']['similar_group']
        response = supabase.table('mastermindgroup').select("group_name, session_datetime, session_location, calendar_link, similar_group").eq("group_name", other_group).execute()

    else:
        mastermind_group_name = person['mastermind_group_name']
        response = supabase.table('mastermindgroup').select("group_name, session_datetime, session_location, calendar_link, similar_group").eq("group_name", mastermind_group_name).execute()

    if response:
        result = response.data[0]

        mastermind_info = {
            'group_name': result['group_name'],
            'date': convertSupabaseDatetime(result['session_datetime']).strftime('%A, %d %B %Y'),
            'time': convertSupabaseDatetime(result['session_datetime']).strftime('%I:%-M %p') + ' onwards',
            'location': result['session_location'],
            'similar_group': result['similar_group'],
            'calendar_link': result['calendar_link'],
            'full_date': result['session_datetime']
        },

        person['mastermind_info'] = mastermind_info[0] # for some reason this is in a tuple

        bot_mastermind_verified = \
f"""
Morning {person['contact_info']['first_name']}, 

Your monthly mastermind session is coming up. Please confirm your attendance by selecting one of the options provided in this message.

Here are the details for your mastermind session:
Date: {person['mastermind_info']['date']}
Time: {person['mastermind_info']['time']}
Location: {person['mastermind_info']['location']}

The details are already in your calendar. Otherwise, click this link: <a href='{person['mastermind_info']['calendar_link']}'>Google Calendar Invite Link</a>

P.s. For members, go for your core group session as much as possible. Indicate your availability as of now - if you're unsure, you may update your availability again in the future by entering /mastermind and redo the entire process.

#attendance #{person['mastermind_info']['group_name']}
"""
        
        keyboard = [['Will be there', 'Unavailable']]

        
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=bot_mastermind_verified, 
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, input_field_placeholder='Can you make it?'),
            parse_mode=ParseMode.HTML
        )

        return CONFIRMATION
    
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="There's a techincal issue - the team has been informed and will get back to you shortly.", 
        )

        return END

async def update_availability(status, chat_id, challenge=None, context=None, session_datetime=None, telegram_context=None):

    response = supabase.table('mastermindattendance').select("group_name, session_datetime").eq("telegram_bot_id", chat_id).execute()

    existing_questionnaire_date = None
    update = False

    if response.data:
        for item in response.data:
            if convertSupabaseDatetime(session_datetime).month == convertSupabaseDatetime(item['session_datetime']).month:
                existing_questionnaire_date = item['session_datetime']

    if existing_questionnaire_date:    
        update = True    

        print(status, challenge, context, session_datetime, chat_id)
        
        try:
            response = supabase.table('mastermindattendance').update({"session_status": status, "challenge": challenge, "context": context, "session_datetime": session_datetime}).eq("telegram_bot_id", chat_id).eq("session_datetime", existing_questionnaire_date).execute()

        except Exception as e:
            print('Update Error: ' + str(e))

    else:

        try:
            response = supabase.table('mastermindattendance').insert({"telegram_bot_id": chat_id, "session_status": status, "challenge": challenge, "context": context, "session_datetime": session_datetime}).execute()

        except Exception as e:
            print('Insert Error: ' + str(e))

    person = telegram_context.user_data['person']
    group_name = person['mastermind_info']['group_name']

    await telegram_context.bot.send_message(
        chat_id='797737829', 
        text=f"""
{person['contact_info']['first_name']} just checked in.

Status: {status}
Challenge: {challenge}
Context: {context}

#attendance #{group_name} #{'update' if update else 'new'}
        """, 
    )

async def available(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
    attending_message = \
f"""
Awesome, before you go off, help us complete this questionnaire in preparation for the session.

First, state your challenge / problem in one sentence:

_E.g. I'm facing difficulty using email marketing to target my audience_
"""

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=attending_message,
        parse_mode=ParseMode.MARKDOWN 
    )

    # TODO initial update of availability

    person = context.user_data['person']

    questionnaire = {
        'challenge': '',
        'context': '',
        'session_date': person['mastermind_info']['full_date'],
        'session_status': 'WBT'
    }

    person['questionnaire'] = questionnaire
    context.user_data['person'] = person

    await update_availability(
        'WBT', 
        update.effective_chat.id,
        session_datetime=context.user_data['person']['mastermind_info']['full_date'], 
        telegram_context=context
    )

    return QUESTIONNAIRE

async def unavailable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    person = context.user_data['person']

    await update_availability(
        'UNA', 
        update.effective_chat.id,
        session_datetime=context.user_data['person']['mastermind_info']['full_date'], 
        telegram_context=context
    )

    if person['mastermind_info']['similar_group'] and not person['invited']:
        person['invited'] = True

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Checking other available dates...", 
            reply_markup=ReplyKeyboardRemove()
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Before that, let us know why you can't make it for your core group session so we can plan better:",
            reply_markup=ReplyKeyboardRemove() 
        )

        return ATTENDANCE
    
    else:

        mastermind_unavailable = \
f"""
Unfortunately, we are unable to find other dates. Please keep a lookout for next month's session or request a group change if this issue is recurring.
"""

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=mastermind_unavailable, 
            reply_markup=ReplyKeyboardRemove()
        )   

        return END  

async def unsure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    # TODO choose option: reminder or invitation
    # TODO invited condition

    return END


async def questionnaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['person']['questionnaire']['challenge'] = update.message.text

    mastermind_questionnaire_message = \
f"""
Next, share with us some context about this challenge:

_E.g. I have tried other forms of marketing to raise awareness of my product with the goal of converting sales but all have failed. Recently I tried email due to suggestions from others but I'm not sure how to work it best_
"""
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=mastermind_questionnaire_message,
        parse_mode=ParseMode.MARKDOWN ,
        reply_markup=ReplyKeyboardRemove()
    )      

    return COMPLETE


async def complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mastermind_end_message = \
f"""
Got it, will be sharing this with the facilitator for the session. See you there!
"""
    
    context.user_data['person']['questionnaire']['context'] = update.message.text        
    
    await update_availability(
        'WBT', 
        update.effective_chat.id, 
        session_datetime=context.user_data['person']['mastermind_info']['full_date'], 
        challenge=context.user_data['person']['questionnaire']['challenge'], 
        context=context.user_data['person']['questionnaire']['context'],
        telegram_context=context)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=mastermind_end_message,
        reply_markup=ReplyKeyboardRemove()
    )

    return END


mastermind_handler = ConversationHandler(
    entry_points=[CommandHandler('mastermind', attendance)],
    states={
        ATTENDANCE: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^q$")), attendance)],
        CONFIRMATION: [
            MessageHandler(
                filters.Regex("^Will be there$"), 
                available),
            MessageHandler(
                filters.Regex("^Unavailable$"),
                unavailable),
            MessageHandler(
                filters.Regex("^Unsure$"),
                unsure)
        ],
        QUESTIONNAIRE: [MessageHandler(filters.TEXT & (~filters.COMMAND), questionnaire)],
        COMPLETE: [MessageHandler(filters.TEXT & (~filters.COMMAND), complete)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)