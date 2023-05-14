from supabase_db import supabase
from datetime import datetime

context = 'hi'


# response = supabase.table('mastermindattendance').insert({"telegram_bot_id": '797737829', "session_status": 'status', "identifier": f'{797737829}-{"hi"}'}).execute() 
response = supabase.table('mastermindattendance').update({"session_status": 'status', "challenge": 'challenge', "context": 'context'}).execute()



# data, error = supabase.table('mastermindattendance').update({'challenge': 'psda'}).eq('email', 'jozlpidc@gmail.com').execute()
# response = supabase.table('profiles').update({"telegram_bot_id": chat_id}).eq("email", email).execute()



