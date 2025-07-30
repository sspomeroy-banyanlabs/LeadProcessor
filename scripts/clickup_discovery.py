"""
ClickUp Board Discovery Tool
===========================

This script discovers and analyzes ClickUp board structures for the UniversalProcessor.
It will help us understand what fields exist on any ClickUp board so we can build
universal CSV-to-ClickUp mapping.

Usage:
    python clickup_discovery.py --list-id <your_list_id>
"""

import requests
import json
import os
from dotenv import load_dotenv
from typing import Dict, List, Any
import argparse

# Load environment variables
load_dotenv()

class ClickUpDiscovery:
    def __init__(self, token: str = None):
        self.token = token or os.getenv('CLICKUP_TOKEN')
        self.headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }
        self.base_url = "https://api.clickup.com/api/v2"
    
    def get_teams(self):
        """Get all teams (workspaces) user has access to"""
        print("🔍 Discovering your ClickUp teams...")
        
        url = f"{self.base_url}/team"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            teams = response.json()['teams']
            print(f"Found {len(teams)} teams:")
            for team in teams:
                print(f"  🏢 {team['name']} (ID: {team['id']})")
            return teams
        else:
            print(f"❌ Error getting teams: {response.status_code}")
            return []
    
    def get_spaces(self, team_id: str):
        """Get all spaces in a team"""
        print(f"\n🔍 Discovering spaces in team {team_id}...")
        
        url = f"{self.base_url}/team/{team_id}/space"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            spaces = response.json()['spaces']
            print(f"Found {len(spaces)} spaces:")
            for space in spaces:
                print(f"  📁 {space['name']} (ID: {space['id']})")
            return spaces
        else:
            print(f"❌ Error getting spaces: {response.status_code}")
            return []
    
    def get_folders_and_lists(self, space_id: str):
        """Get all folders and lists in a space"""
        print(f"\n🔍 Discovering folders and lists in space {space_id}...")
        
        url = f"{self.base_url}/space/{space_id}/folder"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            folders = response.json()['folders']
            print(f"Found {len(folders)} folders:")
            for folder in folders:
                print(f"  📂 {folder['name']} (ID: {folder['id']})")
                
                # Get lists in this folder
                for list_item in folder.get('lists', []):
                    print(f"    📋 {list_item['name']} (ID: {list_item['id']})")
            
            return folders
        else:
            print(f"❌ Error getting folders: {response.status_code}")
            return []
    
    def get_list_details(self, list_id: str):
        """Get detailed information about a specific list"""
        print(f"\n🔍 Analyzing list {list_id}...")
        
        url = f"{self.base_url}/list/{list_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            list_data = response.json()
            print("🔍 DEBUG: Raw API Response:")
            print(json.dumps(list_data, indent=2))
            print("=" * 50)
            
            print(f"📋 List: {list_data['name']}")
            print(f"   Status: {list_data.get('status', 'Unknown')}")
            print(f"   Task Count: {list_data['task_count']}")
            
            # Analyze custom fields
            custom_fields = list_data.get('custom_fields', [])
            print(f"\n🎯 Custom Fields ({len(custom_fields)}):")
            
            field_analysis = {}
            
            for field in custom_fields:
                field_type = field['type']
                field_name = field['name']
                field_id = field['id']
                
                print(f"   📝 {field_name}")
                print(f"      Type: {field_type}")
                print(f"      ID: {field_id}")
                
                # Store for analysis
                field_analysis[field_name] = {
                    'id': field_id,
                    'type': field_type,
                    'required': field.get('required', False)
                }
                
                # If it's a dropdown, show options
                if field_type == 'drop_down' and 'type_config' in field:
                    options = field['type_config'].get('options', [])
                    print(f"      Options ({len(options)}):")
                    for option in options:
                        print(f"        • {option['name']} (ID: {option['id']})")
                        if field_name not in field_analysis:
                            field_analysis[field_name] = {}
                        if 'options' not in field_analysis[field_name]:
                            field_analysis[field_name]['options'] = {}
                        field_analysis[field_name]['options'][option['name']] = option['id']
                
                print()
            
            return {
                'list_info': list_data,
                'field_analysis': field_analysis
            }
        else:
            print(f"❌ Error getting list details: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def full_discovery(self):
        """Run complete discovery of all accessible ClickUp structures"""
        print("🚀 Starting full ClickUp discovery...")
        print("=" * 50)
        
        # Get teams
        teams = self.get_teams()
        
        discovery_data = {}
        
        for team in teams:
            team_id = team['id']
            team_name = team['name']
            
            print(f"\n🏢 Analyzing team: {team_name}")
            print("-" * 40)
            
            # Get spaces
            spaces = self.get_spaces(team_id)
            
            discovery_data[team_name] = {}
            
            for space in spaces:
                space_id = space['id']
                space_name = space['name']
                
                print(f"\n📁 Analyzing space: {space_name}")
                
                # Get folders and lists
                folders = self.get_folders_and_lists(space_id)
                
                discovery_data[team_name][space_name] = {}
                
                for folder in folders:
                    folder_name = folder['name']
                    discovery_data[team_name][space_name][folder_name] = {}
                    
                    for list_item in folder.get('lists', []):
                        list_name = list_item['name']
                        list_id = list_item['id']
                        
                        print(f"\n📋 Analyzing list: {list_name} ({list_id})")
                        list_details = self.get_list_details(list_id)
                        
                        if list_details:
                            discovery_data[team_name][space_name][folder_name][list_name] = {
                                'list_id': list_id,
                                'field_analysis': list_details['field_analysis']
                            }
        
        # Save discovery data
        with open('clickup_discovery.json', 'w') as f:
            json.dump(discovery_data, f, indent=2)
        
        print(f"\n💾 Discovery data saved to 'clickup_discovery.json'")
        print(f"🎉 Discovery complete!")
        
        return discovery_data

def main():
    parser = argparse.ArgumentParser(description='Discover ClickUp board structures')
    parser.add_argument('--list-id', help='Analyze specific list ID')
    parser.add_argument('--full', action='store_true', help='Run full discovery of all accessible boards')
    
    args = parser.parse_args()
    
    discovery = ClickUpDiscovery()
    
    if not discovery.token:
        print("❌ No CLICKUP_TOKEN found in environment")
        print("💡 Make sure your .env file has: CLICKUP_TOKEN=your_token_here")
        return
    
    if args.list_id:
        # Analyze specific list
        discovery.get_list_details(args.list_id)
    elif args.full:
        # Full discovery
        discovery.full_discovery()
    else:
        # Default: show teams and basic structure
        print("🔍 Quick discovery - showing teams and spaces...")
        teams = discovery.get_teams()
        
        for team in teams:
            spaces = discovery.get_spaces(team['id'])
            for space in spaces:
                discovery.get_folders_and_lists(space['id'])

if __name__ == "__main__":
    main()
