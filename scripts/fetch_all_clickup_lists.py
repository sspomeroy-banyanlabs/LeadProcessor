import os
import requests
from dotenv import load_dotenv

load_dotenv()

# 🔐 API keys
api_keys = {
    "Shannon": os.getenv("CLICKUP_API_KEY_SHANNON"),
    "Banyan": os.getenv("CLICKUP_API_KEY_BANYAN")
}

# 📋 List IDs grouped by their associated API key
list_groups = {
    "Shannon": {
        "Automation Reactions": os.getenv("CLICKUP_LIST_ID_AUTOMATION_REACTIONS"),
        "Bad Formatting & Missing Fields": os.getenv("CLICKUP_LIST_ID_BAD_FORMATTING"),
        "Dirty Data & Duplicates": os.getenv("CLICKUP_LIST_ID_DIRTY_DATA"),
        "Base Template": os.getenv("CLICKUP_LIST_ID_BASE_TEMPLATE"),
    },
    "Banyan": {
        "LeadGen Tool": os.getenv("CLICKUP_LIST_ID_LEADGEN_TOOL")
    }
}

# 🔄 Loop through each group
for owner, lists in list_groups.items():
    api_key = api_keys[owner]
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    for name, list_id in lists.items():
        print(f"\n🔍 Fetching: {name} (List ID: {list_id}) using {owner}'s API key")
        url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Failed to fetch: {response.status_code}")
            continue

        data = response.json()
        tasks = data.get("tasks", [])
        print(f"✅ {len(tasks)} task(s) found")

        for task in tasks:
            print(f"— {task.get('name')}")
            for field in task.get("custom_fields", []):
                print(f"   🔸 Field: {field.get('name')} (Type: {field.get('type')})")
