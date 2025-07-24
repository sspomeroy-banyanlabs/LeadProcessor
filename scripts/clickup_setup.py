#!/usr/bin/env python3
"""
ClickUp Setup Helper
Get your ClickUp field IDs and test API connection
"""

import requests
import json
from dotenv import load_dotenv
import os
import sys

# Load environment variables from parent directory
load_dotenv('../.env')

class ClickUpSetup:
    def __init__(self, token: str = None):
        self.token = token or os.getenv('CLICKUP_TOKEN')
        if not self.token:
            print("❌ No CLICKUP_TOKEN found!")
            print("💡 Make sure your .env file contains: CLICKUP_TOKEN=your_token_here")
            sys.exit(1)
            
        self.headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }
        self.base_url = "https://api.clickup.com/api/v2"

    def test_connection(self):
        """Test ClickUp API connection"""
        print("🔌 Testing ClickUp API connection...")
        
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers)
            
            if response.status_code == 200:
                user = response.json()['user']
                print(f"✅ Connected successfully!")
                print(f"👤 User: {user['username']} ({user['email']})")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False

    def get_teams(self):
        """Get all teams (workspaces)"""
        print("\n📋 Getting teams...")
        
        try:
            response = requests.get(f"{self.base_url}/team", headers=self.headers)
            
            if response.status_code == 200:
                teams = response.json()['teams']
                print(f"Found {len(teams)} teams:")
                
                for i, team in enumerate(teams, 1):
                    print(f"  {i}. 🏢 {team['name']} (ID: {team['id']})")
                
                return teams
            else:
                print(f"❌ Failed to get teams: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error getting teams: {str(e)}")
            return []

    def get_spaces(self, team_id: str):
        """Get spaces in a team"""
        print(f"\n📁 Getting spaces for team {team_id}...")
        
        try:
            response = requests.get(f"{self.base_url}/team/{team_id}/space", headers=self.headers)
            
            if response.status_code == 200:
                spaces = response.json()['spaces']
                print(f"Found {len(spaces)} spaces:")
                
                for i, space in enumerate(spaces, 1):
                    print(f"  {i}. 📂 {space['name']} (ID: {space['id']})")
                
                return spaces
            else:
                print(f"❌ Failed to get spaces: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error getting spaces: {str(e)}")
            return []

    def get_folders_and_lists(self, space_id: str):
        """Get folders and lists in a space"""
        print(f"\n📋 Getting folders and lists for space {space_id}...")
        
        all_lists = []
        
        try:
            # Get folders first
            response = requests.get(f"{self.base_url}/space/{space_id}/folder", headers=self.headers)
            
            if response.status_code == 200:
                folders = response.json()['folders']
                if folders:
                    print(f"Found {len(folders)} folders:")
                    
                    for folder in folders:
                        print(f"  📁 {folder['name']} (ID: {folder['id']})")
                        
                        # Get lists in this folder
                        list_response = requests.get(f"{self.base_url}/folder/{folder['id']}/list", headers=self.headers)
                        if list_response.status_code == 200:
                            lists = list_response.json()['lists']
                            for lst in lists:
                                print(f"    📝 {lst['name']} (ID: {lst['id']})")
                                all_lists.append(lst)
            
            # Also get folderless lists
            list_response = requests.get(f"{self.base_url}/space/{space_id}/list", headers=self.headers)
            if list_response.status_code == 200:
                lists = list_response.json()['lists']
                if lists:
                    print(f"\nFolderless lists:")
                    for lst in lists:
                        print(f"  📝 {lst['name']} (ID: {lst['id']})")
                        all_lists.append(lst)
            
            return all_lists
            
        except Exception as e:
            print(f"❌ Error getting folders/lists: {str(e)}")
            return []

    def get_custom_fields(self, list_id: str):
        """Get custom fields for a list"""
        print(f"\n🔧 Getting custom fields for list {list_id}...")
        
        try:
            response = requests.get(f"{self.base_url}/list/{list_id}/field", headers=self.headers)
            
            if response.status_code == 200:
                fields = response.json()['fields']
                print(f"Found {len(fields)} custom fields:")
                
                field_mapping = {}
                for field in fields:
                    field_type = field.get('type', {}).get('name', 'unknown') if isinstance(field.get('type'), dict) else 'unknown'
                    print(f"  🏷️  {field['name']} (ID: {field['id']}, Type: {field_type})")
                    
                    # Map common field names to IDs
                    field_name_lower = field['name'].lower()
                    if 'company' in field_name_lower:
                        field_mapping['company'] = field['id']
                    elif 'email' in field_name_lower:
                        field_mapping['email'] = field['id']
                    elif 'phone' in field_name_lower:
                        field_mapping['phone'] = field['id']
                    elif 'value' in field_name_lower or 'amount' in field_name_lower:
                        field_mapping['estimated_value'] = field['id']
                    elif 'contact' in field_name_lower and 'last' in field_name_lower:
                        field_mapping['last_contact'] = field['id']
                    elif 'stage' in field_name_lower and 'opportunity' in field_name_lower:
                        field_mapping['opportunity_stage'] = field['id']
                    elif 'type' in field_name_lower and 'opportunity' in field_name_lower:
                        field_mapping['opportunity_type'] = field['id']
                
                print(f"\n🎯 Auto-detected field mappings:")
                for key, field_id in field_mapping.items():
                    print(f"  {key}: {field_id}")
                
                return fields, field_mapping
            else:
                print(f"❌ Failed to get custom fields: {response.status_code} - {response.text}")
                return [], {}
                
        except Exception as e:
            print(f"❌ Error getting custom fields: {str(e)}")
            return [], {}

    def create_test_task(self, list_id: str, field_mapping: dict):
        """Create a test task to verify everything works"""
        print(f"\n🧪 Creating test task in list {list_id}...")
        
        payload = {
            "name": "🧪 Test Lead - DELETE ME",
            "description": "This is a test lead created by the setup script. You can delete this task after verifying the setup works.",
            "assignees": [],
            "tags": ["test", "setup"],
            "status": "new",
            "priority": 3,
            "custom_fields": []
        }
        
        # Add custom fields if we found them
        if field_mapping:
            custom_fields = []
            
            if 'company' in field_mapping:
                custom_fields.append({
                    "id": field_mapping['company'],
                    "value": "Test Company Inc."
                })
            
            if 'email' in field_mapping:
                custom_fields.append({
                    "id": field_mapping['email'],
                    "value": "test@testcompany.com"
                })
            
            if 'phone' in field_mapping:
                custom_fields.append({
                    "id": field_mapping['phone'],
                    "value": "(555) 123-4567"
                })
            
            if 'estimated_value' in field_mapping:
                custom_fields.append({
                    "id": field_mapping['estimated_value'],
                    "value": 25000
                })
            
            payload["custom_fields"] = custom_fields
        
        try:
            response = requests.post(
                f"{self.base_url}/list/{list_id}/task",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                task_id = response.json()['id']
                print(f"✅ Test task created successfully! Task ID: {task_id}")
                print(f"🔗 View at: https://app.clickup.com/t/{task_id}")
                return task_id
            else:
                print(f"❌ Failed to create test task: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating test task: {str(e)}")
            return None

    def generate_config_update(self, field_mapping: dict, list_id: str):
        """Generate the code to update your processor"""
        print(f"\n📄 COPY THIS INTO YOUR leadgen_processor.py FILE:")
        print("=" * 60)
        
        print("# Replace the clickup_field_mapping section with this:")
        print("self.clickup_field_mapping = {")
        print(f"    'company': '{field_mapping.get('company', 'FIELD_NOT_FOUND')}',")
        print(f"    'email': '{field_mapping.get('email', 'FIELD_NOT_FOUND')}',")
        print(f"    'phone': '{field_mapping.get('phone', 'FIELD_NOT_FOUND')}',")
        print(f"    'estimated_value': '{field_mapping.get('estimated_value', 'FIELD_NOT_FOUND')}',")
        print(f"    'last_contact': '{field_mapping.get('last_contact', 'FIELD_NOT_FOUND')}',")
        print(f"    'opportunity_stage': '{field_mapping.get('opportunity_stage', 'FIELD_NOT_FOUND')}',")
        print(f"    'opportunity_type': '{field_mapping.get('opportunity_type', 'FIELD_NOT_FOUND')}'")
        print("}")
        
        print(f"\n# And uncomment/update the upload section at the bottom:")
        print(f"list_id = \"{list_id}\"")
        print("task_ids = processor.upload_to_clickup(processed_leads, list_id)")
        print("print(f\"✅ Created {len(task_ids)} tasks in ClickUp!\")")
        
        # Save to file for easy reference
        with open('field_mapping.txt', 'w') as f:
            f.write(f"# ClickUp Field Mapping for leadgen_processor.py\n")
            f.write(f"# Generated on {__import__('datetime').datetime.now()}\n\n")
            f.write("self.clickup_field_mapping = {\n")
            f.write(f"    'company': '{field_mapping.get('company', 'FIELD_NOT_FOUND')}',\n")
            f.write(f"    'email': '{field_mapping.get('email', 'FIELD_NOT_FOUND')}',\n")
            f.write(f"    'phone': '{field_mapping.get('phone', 'FIELD_NOT_FOUND')}',\n")
            f.write(f"    'estimated_value': '{field_mapping.get('estimated_value', 'FIELD_NOT_FOUND')}',\n")
            f.write(f"    'last_contact': '{field_mapping.get('last_contact', 'FIELD_NOT_FOUND')}',\n")
            f.write(f"    'opportunity_stage': '{field_mapping.get('opportunity_stage', 'FIELD_NOT_FOUND')}',\n")
            f.write(f"    'opportunity_type': '{field_mapping.get('opportunity_type', 'FIELD_NOT_FOUND')}'\n")
            f.write("}\n\n")
            f.write(f"# Your List ID: {list_id}\n")
        
        print(f"\n💾 Field mapping also saved to: field_mapping.txt")

def interactive_setup():
    """Interactive setup wizard"""
    print("🚀 ClickUp LeadGen Setup Wizard")
    print("=" * 40)
    
    setup = ClickUpSetup()
    
    # Test connection
    if not setup.test_connection():
        return
    
    # Get teams
    teams = setup.get_teams()
    if not teams:
        return
    
    # Let user select team
    if len(teams) == 1:
        selected_team = teams[0]
        print(f"\n✅ Auto-selected team: {selected_team['name']}")
    else:
        while True:
            try:
                choice = input(f"\nEnter team number (1-{len(teams)}): ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(teams):
                    selected_team = teams[choice_idx]
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(teams)}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    # Get spaces
    spaces = setup.get_spaces(selected_team['id'])
    if not spaces:
        return
    
    # Let user select space
    if len(spaces) == 1:
        selected_space = spaces[0]
        print(f"\n✅ Auto-selected space: {selected_space['name']}")
    else:
        while True:
            try:
                choice = input(f"\nEnter space number (1-{len(spaces)}): ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(spaces):
                    selected_space = spaces[choice_idx]
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(spaces)}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    # Show folders and lists
    lists = setup.get_folders_and_lists(selected_space['id'])
    
    # Get list ID for leads
    print(f"\n📋 Enter the List ID where you want to import leads:")
    print("💡 Look for your 'Banyan CRM' or similar list above")
    print("💡 You can also get this from the ClickUp URL when viewing the list")
    
    while True:
        list_id = input("List ID: ").strip()
        if list_id:
            break
        print("❌ List ID required")
    
    # Get custom fields
    fields, field_mapping = setup.get_custom_fields(list_id)
    
    if not fields:
        print("⚠️  No custom fields found. Make sure your list has the required fields:")
        print("   - Company, Email, Phone, Estimated Value, etc.")
        return
    
    # Create test task
    test_choice = input(f"\n🧪 Create a test task to verify setup? (y/n): ").lower().strip()
    if test_choice == 'y':
        test_task_id = setup.create_test_task(list_id, field_mapping)
        if test_task_id:
            print(f"🎉 Setup verification successful!")
    
    # Generate config
    setup.generate_config_update(field_mapping, list_id)
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Copy the field mapping code above into leadgen_processor.py")
    print(f"2. Uncomment the upload section at the bottom of leadgen_processor.py")
    print(f"3. Run: python leadgen_processor.py")
    print(f"4. Check ClickUp for your imported leads!")

if __name__ == "__main__":
    interactive_setup()
