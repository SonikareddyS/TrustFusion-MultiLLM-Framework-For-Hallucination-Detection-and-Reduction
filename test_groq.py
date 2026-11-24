import os
from dotenv import load_dotenv
import httpx

load_dotenv('backend/.env')

r = httpx.get(
    'https://api.groq.com/openai/v1/models',
    headers={'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}'}
)

models = r.json()['data']
for m in models:
    print(m['id'])