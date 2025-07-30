#!/usr/bin/env python3
"""
Minimal Phone Field Test
========================

This script tests ONLY the phone field with the exact same logic/format as v2
to isolate the phone validation issue.
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_minimal_phone_only():
    """Test with ONLY phone field - no other fields"""
    token = os.getenv('CLICKUP_TOKEN')
    list_id = os.getenv('CLICKUP_LIST_ID', '901316698136')
    
    if not token:
        print("❌ No CLICKUP_TOKEN found")
        return
    
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    
    # EXACT v2 phone format that works
    phone_number = "+1 555 123 4567"  # This format works in v2
    
    # Minimal payload - ONLY phone field
    payload = {
        "name": "Minimal Phone Test",
        "description": "Testing only phone field",
        "custom_fields": [
            {
                "id": "6eff29cc-d7b8-4517-8d4e-ff0ba486973a",  # Phone field ID
                "value": phone_number
            }
        ]
    }
    
    print("🧪 MINIMAL PHONE TEST")
    print("=" * 30)
    print(f"List ID: {list_id}")
    print(f"Phone: {phone_number}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Make the API call
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    
    print(f"\n📞 Making API call...")
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        task_id = response.json().get('id')
        print(f"✅ SUCCESS! Created task: {task_id}")
        print("✅ Phone field accepts this format when isolated!")
    else:
        print(f"❌ FAILED: {response.text}")
        
        # Try Shannon's format
        print(f"\n🔄 Trying Shannon's format...")
        payload['custom_fields'][0]['value'] = "(555) 123-4567"
        print(f"New phone: {payload['custom_fields'][0]['value']}")
        
        response2 = requests.post(url, headers=headers, json=payload)
        print(f"Status: {response2.status_code}")
        
        if response2.status_code == 200:
            task_id = response2.json().get('id')
            print(f"✅ SUCCESS with Shannon's format! Task: {task_id}")
        else:
            print(f"❌ Also failed: {response2.text}")

def test_minimal_company_plus_phone():
    """Test with company + phone (minimal combo that fails)"""
    token = os.getenv('CLICKUP_TOKEN')
    list_id = os.getenv('CLICKUP_LIST_ID', '901316698136')
    
    if not token:
        print("❌ No CLICKUP_TOKEN found")
        return
    
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    
    # Test company + phone combo (your summary mentioned this fails)
    payload = {
        "name": "Company + Phone Test",
        "description": "Testing company + phone combo",
        "custom_fields": [
            {
                "id": "0945b0ab-20e6-4f19-9667-a0d11ab32f0e",  # Company field
                "value": "Test Company"
            },
            {
                "id": "6eff29cc-d7b8-4517-8d4e-ff0ba486973a",  # Phone field
                "value": "+1 555 123 4567"
            }
        ]
    }
    
    print("\n🏢 COMPANY + PHONE TEST")
    print("=" * 30)
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        task_id = response.json().get('id')
        print(f"✅ SUCCESS! Created task: {task_id}")
    else:
        print(f"❌ FAILED: {response.text}")

def extract_v2_working_phone():
    """Check exactly what phone format v2 is actually sending"""
    print("\n🔍 V2 PHONE FORMAT ANALYSIS")
    print("=" * 35)
    
    # This is the exact v2 logic from leadgen_processor_v2.py
    def clean_phone_number_v2(phone):
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
    
    # Test with various inputs
    test_inputs = [
        "5551234567",
        "(555) 123-4567",
        "555-123-4567",
        "15551234567",
        "+1 555 123 4567"
    ]
    
    print("V2 would format these as:")
    for test_input in test_inputs:
        result = clean_phone_number_v2(test_input)
        print(f"  {test_input} → {result}")

def main():
    print("📞 MINIMAL PHONE TESTING")
    print("=" * 40)
    
    # Analyze v2 formatting
    extract_v2_working_phone()
    
    # Test phone only
    test_minimal_phone_only()
    
    # Test company + phone
    test_minimal_company_plus_phone()
    
    print("\n💡 DEBUGGING INSIGHTS:")
    print("- If phone-only works but company+phone fails → field interaction issue")
    print("- If both fail → phone format issue")
    print("- If both work → issue is in universal processor logic somewhere else")

if __name__ == "__main__":
    main()
