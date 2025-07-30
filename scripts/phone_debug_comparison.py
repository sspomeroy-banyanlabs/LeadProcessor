#!/usr/bin/env python3
"""
Phone Number Debug Comparison Tool
==================================

This script will help us figure out exactly what's different between v2 and universal
processor API calls when handling phone numbers.
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_v2_phone_format():
    """Test v2 phone formatting logic"""
    def clean_phone_number_v2(phone):
        """v2 logic - format: +1 XXX XXX XXXX"""
        import re
        import pandas as pd
        
        if pd.isna(phone) or not phone:
            return None
            
        # Remove all non-digit characters
        cleaned = re.sub(r'[^\d]', '', str(phone))
        
        # Format exactly like Emily Cox: +1 XXX XXX XXXX
        if len(cleaned) == 10:
            return f"+1 {cleaned[:3]} {cleaned[3:6]} {cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned[0] == '1':
            clean_10 = cleaned[1:]
            return f"+1 {clean_10[:3]} {clean_10[3:6]} {clean_10[6:]}"
        
        return None
    
    # Test with sample numbers
    test_numbers = [
        "1234567890",
        "(123) 456-7890", 
        "123-456-7890",
        "123.456.7890",
        "+1 123 456 7890"
    ]
    
    print("🔍 V2 Phone Formatting Results:")
    for num in test_numbers:
        formatted = clean_phone_number_v2(num)
        print(f"   {num} → {formatted}")

def test_universal_phone_format():
    """Test universal phone formatting logic"""
    def clean_phone_number_universal(phone):
        """Universal logic - Shannon's format with parentheses"""
        import re
        import pandas as pd
        
        if pd.isna(phone) or not phone:
            return None
        # Remove all non-digit characters
        cleaned = re.sub(r'[^\d]', '', str(phone))
        # Format with parentheses: (XXX) XXX-XXXX
        if len(cleaned) == 10:
            return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned[0] == '1':
            clean_10 = cleaned[1:]
            return f"({clean_10[:3]}) {clean_10[3:6]}-{clean_10[6:]}"
        return None
    
    # Test with sample numbers
    test_numbers = [
        "1234567890",
        "(123) 456-7890", 
        "123-456-7890",
        "123.456.7890",
        "+1 123 456 7890"
    ]
    
    print("\n🔍 Universal Phone Formatting Results:")
    for num in test_numbers:
        formatted = clean_phone_number_universal(num)
        print(f"   {num} → {formatted}")

def create_v2_payload(company_name, phone_number):
    """Create a v2-style payload"""
    field_mapping = {
        'company': '0945b0ab-20e6-4f19-9667-a0d11ab32f0e',
        'phone': '6eff29cc-d7b8-4517-8d4e-ff0ba486973a',
    }
    
    payload = {
        "name": f"Test Lead - {company_name}",
        "description": "Test lead for phone debugging",
        "custom_fields": [
            {
                "id": field_mapping['company'],
                "value": company_name
            },
            {
                "id": field_mapping['phone'],
                "value": phone_number
            }
        ]
    }
    return payload

def create_universal_payload(company_name, phone_number):
    """Create a universal-style payload"""
    field_mapping = {
        'company': '0945b0ab-20e6-4f19-9667-a0d11ab32f0e',
        'phone': '6eff29cc-d7b8-4517-8d4e-ff0ba486973a',
    }
    
    payload = {
        "name": f"Test Lead - {company_name}",
        "description": "Test lead for phone debugging",
        "custom_fields": []
    }
    
    # Add custom fields
    for field_id, value in [(field_mapping['company'], company_name), (field_mapping['phone'], phone_number)]:
        payload["custom_fields"].append({
            "id": field_id,
            "value": value
        })
    
    return payload

def compare_payloads():
    """Compare the exact payloads being generated"""
    company = "Test Company"
    phone_v2 = "+1 555 123 4567"  # v2 format
    phone_universal = "(555) 123-4567"  # Universal format
    
    v2_payload = create_v2_payload(company, phone_v2)
    universal_payload = create_universal_payload(company, phone_universal)
    
    print("\n📋 PAYLOAD COMPARISON:")
    print("=" * 50)
    
    print("V2 Payload:")
    print(json.dumps(v2_payload, indent=2))
    
    print("\nUniversal Payload:")
    print(json.dumps(universal_payload, indent=2))
    
    print("\n🔍 DIFFERENCES:")
    # Check for structural differences
    v2_fields = {f["id"]: f["value"] for f in v2_payload["custom_fields"]}
    universal_fields = {f["id"]: f["value"] for f in universal_payload["custom_fields"]}
    
    print(f"V2 phone field: {v2_fields.get('6eff29cc-d7b8-4517-8d4e-ff0ba486973a')}")
    print(f"Universal phone field: {universal_fields.get('6eff29cc-d7b8-4517-8d4e-ff0ba486973a')}")

def test_actual_api_call(test_mode=True):
    """Test actual API calls if token is available"""
    token = os.getenv('CLICKUP_TOKEN')
    list_id = os.getenv('CLICKUP_LIST_ID', '901316698136')  # Default to sample CRM
    
    if not token:
        print("\n⚠️ No CLICKUP_TOKEN found - skipping actual API test")
        return
    
    if not test_mode:
        print("\n⚠️ Set test_mode=False to run actual API calls")
        return
    
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    
    # Test both formats
    test_cases = [
        ("V2 Format", "+1 555 123 4567"),
        ("Universal Format", "(555) 123-4567"),
        ("Shannon Format", "(555) 123-4567")
    ]
    
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    
    print(f"\n🧪 TESTING ACTUAL API CALLS (List: {list_id}):")
    print("=" * 60)
    
    for format_name, phone_format in test_cases:
        payload = create_universal_payload(f"Debug Test {format_name}", phone_format)
        
        print(f"\n📞 Testing {format_name}: {phone_format}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Uncomment to make actual API calls
        # response = requests.post(url, headers=headers, json=payload)
        # print(f"Response: {response.status_code}")
        # if response.status_code != 200:
        #     print(f"Error: {response.text}")

def check_existing_phone_data():
    """Check what phone data exists in ClickUp already"""
    token = os.getenv('CLICKUP_TOKEN')
    list_id = os.getenv('CLICKUP_LIST_ID', '901316698136')
    
    if not token:
        print("\n⚠️ No CLICKUP_TOKEN found - cannot check existing data")
        return
    
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    
    # Get some existing tasks
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    params = {'page': 0, 'limit': 5, 'include_closed': True}
    
    print(f"\n📊 CHECKING EXISTING PHONE DATA (List: {list_id}):")
    print("=" * 50)
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            tasks = response.json().get('tasks', [])
            phone_field_id = '6eff29cc-d7b8-4517-8d4e-ff0ba486973a'
            
            for task in tasks[:3]:  # Check first 3 tasks
                task_name = task.get('name', 'Unknown')
                custom_fields = task.get('custom_fields', [])
                
                phone_value = None
                for field in custom_fields:
                    if field.get('id') == phone_field_id:
                        phone_value = field.get('value')
                        break
                
                print(f"Task: {task_name}")
                print(f"  Phone: {phone_value}")
                print(f"  Phone type: {type(phone_value)}")
                print()
        else:
            print(f"Error getting tasks: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("🔍 PHONE NUMBER DEBUG COMPARISON")
    print("=" * 50)
    
    # Test phone formatting
    test_v2_phone_format()
    test_universal_phone_format()
    
    # Compare payloads
    compare_payloads()
    
    # Check existing data
    check_existing_phone_data()
    
    # Test API calls (set to False by default for safety)
    test_actual_api_call(test_mode=True)
    
    print("\n💡 NEXT STEPS:")
    print("1. Check if existing leads actually have phone numbers")
    print("2. Try the exact same phone format that's working in v2")
    print("3. Compare request headers between v2 and universal")
    print("4. Test with minimal payload (just phone field)")

if __name__ == "__main__":
    main()
