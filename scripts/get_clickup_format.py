#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Your ClickUp token
token = os.getenv('CLICKUP_TOKEN')
headers = {
    'Authorization': token,
    'Content-Type': 'application/json'
}

# Get tasks from your sandbox list
list_id = "901316698136"
url = f"https://api.clickup.com/api/v2/list/{list_id}/task"

response = requests.get(url, headers=headers)

if response.status_code == 200:
    tasks = response.json()['tasks']
    print(f"Found {len(tasks)} tasks in the list")
    
    for task in tasks[:5]:  # Check first 5 tasks
        print(f"\n📋 Task: {task['name']}")
        
        # Look for custom fields
        if 'custom_fields' in task:
            for field in task['custom_fields']:
                if 'phone' in field.get('name', '').lower():
                    print(f"   📱 Phone field: {field}")
                    print(f"   📱 Phone value: {field.get('value')}")
        
        # Also check if there are any existing Emily Cox type tasks
        if 'emily' in task['name'].lower() or 'cox' in task['name'].lower():
            print(f"   🎯 FOUND EMILY COX TASK!")
            print(f"   Custom fields: {task.get('custom_fields', [])}")
else:
    print(f"Error: {response.status_code} - {response.text}")
