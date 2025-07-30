import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("CLICKUP_API_KEY_SHANNON")
list_id = os.getenv("CLICKUP_LIST_ID_AUTOMATION_REACTIONS")

headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}

url = f"https://api.clickup.com/api/v2/list/{list_id}/task"

response = requests.get(url, headers=headers)

print(f"Status: {response.status_code}")
print(response.json())
