# you can name this function anything you want, the name "logic" is arbitrary

import os
from pathlib import Path
from dotenv import load_dotenv
import openai

# Initialising credentials 
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Load your API key from an environment variable or secret management service
openai.api_key = os.environ.get('OPENAI_API_KEY')

response = openai.Completion.create(model="text-davinci-003", prompt="Say this is a test", temperature=0, max_tokens=7)