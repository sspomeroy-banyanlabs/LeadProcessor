#!/usr/bin/env python3
"""
Universal ClickUp Discovery Engine
=================================

This script can analyze ANY ClickUp board and discover its field structure,
making it possible to build universal CSV-to-ClickUp processors.

Features:
- Auto-discovers field types, IDs, and dropdown options
- Works with any ClickUp API token and list ID
- Builds intelligent CSV column mapping
- Handles any field structure dynamically

Usage:
    python universal_discovery.py --token YOUR_TOKEN --list-id YOUR_LIST_ID
"""

import requests
import json
import os
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
import argparse
import re
from dataclasses import dataclass

# Load environment variables
load_dotenv()

@dataclass
class ClickUpField:
    """Represents a ClickUp custom field"""
    id: str
    name: str
    type: str
    required: bool = False
    options: Dict[str, str] = None  # For dropdowns: {option_name: option_id}

class UniversalClickUpDiscovery:
    """
    Universal ClickUp field discovery engine.
    Can analyze any ClickUp board and understand its structure.
    """
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            'Authorization': api_token,
            'Content-Type': 'application/json'
        }
        self.base_url = "https://api.clickup.com/api/v2"
        self.discovered_fields = {}
    
    def discover_list_structure(self, list_id: str) -> Dict[str, ClickUpField]:
        """
        Discover the complete field structure of any ClickUp list.
        Returns a mapping of field names to ClickUpField objects.
        """
        print(f"🔍 Discovering field structure for list {list_id}...")
        
        # Get list basic info
        list_info = self._get_list_info(list_id)
        if not list_info:
            return {}
        
        print(f"📋 List: {list_info['name']}")
        print(f"   Tasks: {list_info['task_count']}")
        
        # Get field structure from sample tasks
        fields = self._discover_fields_from_tasks(list_id)
        
        print(f"\n🎯 Discovered {len(fields)} custom fields:")
        for field_name, field in fields.items():
            print(f"   📝 {field_name}")
            print(f"      Type: {field.type}")
            print(f"      ID: {field.id}")
            
            if field.options:
                print(f"      Options ({len(field.options)}):")
                for option_name, option_id in field.options.items():
                    print(f"        • {option_name} (ID: {option_id})")
            print()
        
        self.discovered_fields[list_id] = fields
        return fields
    
    def _get_list_info(self, list_id: str) -> Optional[Dict]:
        """Get basic list information"""
        url = f"{self.base_url}/list/{list_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error getting list info: {response.status_code}")
            return None
    
    def _discover_fields_from_tasks(self, list_id: str) -> Dict[str, ClickUpField]:
        """Discover fields by examining actual tasks"""
        url = f"{self.base_url}/list/{list_id}/task"
        params = {
            'page': 0,
            'limit': 5,  # Sample a few tasks
            'include_closed': True
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error getting tasks: {response.status_code}")
            return {}
        
        tasks = response.json().get('tasks', [])
        if not tasks:
            print("⚠️ No tasks found in list")
            return {}
        
        # Analyze fields from all sample tasks
        all_fields = {}
        
        for task in tasks:
            custom_fields = task.get('custom_fields', [])
            
            for field in custom_fields:
                field_name = field['name']
                field_id = field['id']
                field_type = field['type']
                
                # Handle dropdown options
                options = None
                if field_type == 'drop_down' and 'type_config' in field:
                    options = {}
                    for option in field['type_config'].get('options', []):
                        options[option['name']] = option['id']
                
                # Store field info
                all_fields[field_name] = ClickUpField(
                    id=field_id,
                    name=field_name,
                    type=field_type,
                    required=field.get('required', False),
                    options=options
                )
        
        return all_fields
    
    def intelligent_csv_mapping(self, csv_headers: List[str], discovered_fields: Dict[str, ClickUpField]) -> Dict[str, str]:
        """
        Intelligently map CSV columns to ClickUp fields using pattern matching.
        Returns mapping of csv_column -> clickup_field_id
        """
        print("\n🧠 Building intelligent CSV-to-ClickUp mapping...")
        
        mapping = {}
        
        # Define common patterns for automatic mapping
        field_patterns = {
            'email': ['email', 'email_address', 'e-mail', 'mail', 'contact_email'],
            'company': ['company', 'company_name', 'organization', 'business', 'firm'],
            'phone': ['phone', 'phone_number', 'telephone', 'mobile', 'cell'],
            'name': ['name', 'full_name', 'contact_name', 'person', 'lead_name'],
            'title': ['title', 'job_title', 'position', 'role'],
            'industry': ['industry', 'sector', 'business_type', 'category'],
            'website': ['website', 'url', 'web', 'site'],
            'address': ['address', 'location', 'street', 'city'],
            'notes': ['notes', 'comments', 'description', 'remarks']
        }
        
        # Try to match CSV columns to ClickUp fields
        for csv_header in csv_headers:
            csv_lower = csv_header.lower().strip()
            best_match = None
            best_score = 0
            
            # Check each ClickUp field
            for field_name, field in discovered_fields.items():
                field_lower = field_name.lower()
                
                # Direct match
                if csv_lower == field_lower:
                    mapping[csv_header] = field.id
                    print(f"   ✅ {csv_header} → {field_name} (exact match)")
                    break
                
                # Pattern matching
                for pattern_type, patterns in field_patterns.items():
                    if field_lower in patterns or any(pattern in field_lower for pattern in patterns):
                        for pattern in patterns:
                            if pattern in csv_lower:
                                score = len(pattern)  # Longer patterns score higher
                                if score > best_score:
                                    best_match = field
                                    best_score = score
            
            # Use best pattern match if no exact match
            if csv_header not in mapping and best_match:
                mapping[csv_header] = best_match.id
                print(f"   🎯 {csv_header} → {best_match.name} (pattern match)")
        
        # Show unmapped columns
        unmapped = [h for h in csv_headers if h not in mapping]
        if unmapped:
            print(f"\n⚠️ Unmapped CSV columns ({len(unmapped)}):")
            for col in unmapped:
                print(f"   • {col}")
            
            print("\n💡 Available ClickUp fields:")
            for field_name, field in discovered_fields.items():
                if field.id not in mapping.values():
                    print(f"   • {field_name} ({field.type})")
        
        return mapping
    
    def detect_industry_options(self, source_filename: str, company_name: str, discovered_fields: Dict[str, ClickUpField]) -> Optional[str]:
        """
        Intelligently detect industry from available context and map to dropdown options.
        Returns the option ID for the detected industry.
        """
        # Find industry field
        industry_field = None
        for field_name, field in discovered_fields.items():
            if 'industry' in field_name.lower() and field.type == 'drop_down':
                industry_field = field
                break
        
        if not industry_field or not industry_field.options:
            return None
        
        # Industry detection logic
        source_lower = source_filename.lower() if source_filename else ""
        company_lower = company_name.lower() if company_name else ""
        
        # Map source indicators to industry options
        industry_indicators = {
            'real_estate': ['real estate', 'commercial', 'property', 'realty'],
            'technology': ['tech', 'software', 'cto', 'developer', 'it'],
            'food': ['restaurant', 'food', 'beverage', 'dining', 'cafe'],
            'healthcare': ['healthcare', 'dental', 'medical', 'health'],
            'nonprofit': ['nonprofit', 'non-profit', 'charity', 'foundation'],
            'home_services': ['landscaping', 'pool', 'construction', 'home'],
            'marketing': ['marketing', 'design', 'advertising', 'creative'],
            'business': ['business', 'entrepreneur', 'founder', 'owner']
        }
        
        # Check each available industry option
        for option_name, option_id in industry_field.options.items():
            option_lower = option_name.lower()
            
            # Check if any indicators match this option
            for category, indicators in industry_indicators.items():
                if any(keyword in option_lower for keyword in indicators):
                    if any(indicator in source_lower or indicator in company_lower for indicator in indicators):
                        print(f"🏭 Detected industry: {option_name}")
                        return option_id
        
        # Default to first option or "General Business" if available
        if 'general business' in [opt.lower() for opt in industry_field.options.keys()]:
            for opt_name, opt_id in industry_field.options.items():
                if 'general business' in opt_name.lower():
                    return opt_id
        
        # Fall back to first option
        return list(industry_field.options.values())[0] if industry_field.options else None
    
    def generate_universal_processor_config(self, list_id: str, csv_headers: List[str]) -> Dict:
        """
        Generate a complete configuration for the universal processor.
        This can be saved and reused for processing CSVs to this specific ClickUp list.
        """
        # Discover fields
        fields = self.discover_list_structure(list_id)
        
        # Generate CSV mapping
        csv_mapping = self.intelligent_csv_mapping(csv_headers, fields)
        
        # Build complete config
        config = {
            'list_id': list_id,
            'api_token': self.api_token,
            'discovered_fields': {
                name: {
                    'id': field.id,
                    'type': field.type,
                    'options': field.options
                }
                for name, field in fields.items()
            },
            'csv_mapping': csv_mapping,
            'industry_field': None,
            'timestamp': str(pd.Timestamp.now()) if 'pd' in globals() else 'unknown'
        }
        
        # Find industry field for special handling
        for field_name, field in fields.items():
            if 'industry' in field_name.lower() and field.type == 'drop_down':
                config['industry_field'] = {
                    'id': field.id,
                    'name': field_name,
                    'options': field.options
                }
                break
        
        return config
    
    def save_config(self, config: Dict, filename: str = None):
        """Save configuration to JSON file"""
        if not filename:
            filename = f"clickup_config_{config['list_id']}.json"
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"💾 Configuration saved to {filename}")
        return filename

def main():
    parser = argparse.ArgumentParser(description='Universal ClickUp Discovery Engine')
    parser.add_argument('--token', help='ClickUp API token')
    parser.add_argument('--list-id', required=True, help='ClickUp list ID to analyze')
    parser.add_argument('--csv-headers', nargs='*', help='CSV headers to map (optional)')
    parser.add_argument('--save-config', action='store_true', help='Save configuration to JSON file')
    
    args = parser.parse_args()
    
    # Get token from args or environment
    token = args.token or os.getenv('CLICKUP_TOKEN')
    if not token:
        print("❌ No ClickUp token provided")
        print("💡 Use --token YOUR_TOKEN or set CLICKUP_TOKEN in .env")
        return
    
    # Initialize discovery engine
    discovery = UniversalClickUpDiscovery(token)
    
    # Discover field structure
    fields = discovery.discover_list_structure(args.list_id)
    
    if not fields:
        print("❌ No fields discovered")
        return
    
    # If CSV headers provided, generate mapping
    if args.csv_headers:
        print(f"\n🔗 Mapping {len(args.csv_headers)} CSV columns...")
        mapping = discovery.intelligent_csv_mapping(args.csv_headers, fields)
        
        if args.save_config:
            config = discovery.generate_universal_processor_config(args.list_id, args.csv_headers)
            discovery.save_config(config)
    else:
        print("\n💡 To test CSV mapping, use: --csv-headers 'Email' 'Company' 'Phone'")
    
    print("\n🎉 Discovery complete!")

if __name__ == "__main__":
    main()
