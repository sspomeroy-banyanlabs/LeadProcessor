#!/usr/bin/env python3
"""
Universal CSV-to-ClickUp Processor v3 - FIXED
============================================

This processor can handle ANY ClickUp board with ANY field structure.
It automatically discovers field mappings and processes CSVs universally.

FIXED: Phone number validation issue solved with two-step upload approach

Features:
- Auto-discovers any ClickUp board structure
- Intelligent CSV column mapping
- Dynamic dropdown handling
- Universal industry/category detection
- Works with any API token and list ID
- Two-step phone upload (create task, then add phone)

Usage:
    python universal_processor.py --token YOUR_TOKEN --list-id YOUR_LIST_ID --csv-file your_data.csv
"""

import pandas as pd
import requests
import json
import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import argparse
from dataclasses import dataclass

# Import our discovery engine
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('universal_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ClickUpField:
    """Represents a ClickUp custom field"""
    id: str
    name: str
    type: str
    required: bool = False
    options: Dict[str, str] = None

class UniversalClickUpProcessor:
    """
    Universal CSV-to-ClickUp processor that works with any board structure.
    """
    
    def __init__(self, api_token: str, list_id: str):
        self.api_token = api_token
        self.list_id = list_id
        self.headers = {
            'Authorization': api_token,
            'Content-Type': 'application/json'
        }
        self.base_url = "https://api.clickup.com/api/v2"
        
        # Auto-discover board structure
        logger.info(f"🔍 Initializing Universal Processor for list {list_id}")
        self.discovered_fields = self._discover_board_structure()
        self.csv_mapping = {}
        
        logger.info(f"✅ Universal Processor ready! Discovered {len(self.discovered_fields)} fields")
    
    def _discover_board_structure(self) -> Dict[str, ClickUpField]:
        """Auto-discover the complete field structure of the ClickUp board"""
        logger.info("🔍 Auto-discovering board field structure...")
        
        # Get sample tasks to understand field structure
        url = f"{self.base_url}/list/{self.list_id}/task"
        params = {'page': 0, 'limit': 3, 'include_closed': True}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"❌ Failed to get tasks: {response.status_code}")
            return {}
        
        tasks = response.json().get('tasks', [])
        if not tasks:
            logger.warning("⚠️ No tasks found - cannot discover field structure")
            return {}
        
        # Analyze fields from sample tasks
        discovered_fields = {}
        
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
                discovered_fields[field_name] = ClickUpField(
                    id=field_id,
                    name=field_name,
                    type=field_type,
                    required=field.get('required', False),
                    options=options
                )
        
        # Log discovered structure
        logger.info(f"📋 Discovered fields for board:")
        for field_name, field in discovered_fields.items():
            logger.info(f"   📝 {field_name} ({field.type})")
            if field.options:
                logger.info(f"      Options: {list(field.options.keys())}")
        
        return discovered_fields
    
    def _intelligent_csv_mapping(self, csv_headers: List[str]) -> Dict[str, str]:
        """Intelligently map CSV columns to ClickUp fields"""
        logger.info("🧠 Building intelligent CSV-to-ClickUp mapping...")
        
        mapping = {}
        
        # Define patterns for common field types
        field_patterns = {
            'email': ['email', 'email_address', 'e-mail', 'mail', 'contact_email'],
            'company': ['company', 'company_name', 'organization', 'business', 'firm'],
            'phone': ['phone', 'phone_number', 'telephone', 'mobile', 'cell'],
            'name': ['name', 'full_name', 'contact_name', 'person', 'lead_name'],
            'title': ['title', 'job_title', 'position', 'role'],
            'website': ['website', 'url', 'web', 'site', 'linkedin'],
            'notes': ['notes', 'comments', 'description', 'remarks', 'lead_notes'],
            'source': ['source', 'import', 'origin', 'channel'],
            'industry': ['industry', 'sector', 'business_type', 'category'],
            'status': ['status', 'stage', 'opportunity_stage'],
            'value': ['value', 'estimated_value', 'deal_value', 'revenue']
        }
        
        # Try to match CSV columns to ClickUp fields
        for csv_header in csv_headers:
            csv_lower = csv_header.lower().strip()
            best_match = None
            best_score = 0
            
            # Check each discovered ClickUp field
            for field_name, field in self.discovered_fields.items():
                field_lower = field_name.lower()
                
                # Direct match (highest priority)
                if csv_lower == field_lower:
                    mapping[csv_header] = field.id
                    logger.info(f"   ✅ {csv_header} → {field_name} (exact match)")
                    break
                
                # Partial match
                if csv_lower in field_lower or field_lower in csv_lower:
                    score = min(len(csv_lower), len(field_lower))
                    if score > best_score:
                        best_match = field
                        best_score = score
                
                # Pattern matching
                for pattern_type, patterns in field_patterns.items():
                    field_matches_pattern = any(pattern in field_lower for pattern in patterns)
                    csv_matches_pattern = any(pattern in csv_lower for pattern in patterns)
                    
                    if field_matches_pattern and csv_matches_pattern:
                        score = max([len(p) for p in patterns if p in csv_lower])
                        if score > best_score:
                            best_match = field
                            best_score = score
            
            # Use best match if no exact match found
            if csv_header not in mapping and best_match:
                mapping[csv_header] = best_match.id
                logger.info(f"   🎯 {csv_header} → {best_match.name} (pattern match)")
        
        # Report unmapped columns
        unmapped = [h for h in csv_headers if h not in mapping]
        if unmapped:
            logger.warning(f"⚠️ Unmapped CSV columns: {unmapped}")
            logger.info("💡 Available ClickUp fields:")
            for field_name, field in self.discovered_fields.items():
                if field.id not in mapping.values():
                    logger.info(f"   • {field_name} ({field.type})")
        
        return mapping
    
    def _detect_dropdown_value(self, field_name: str, context_data: Dict[str, Any]) -> Optional[str]:
        """Intelligently detect the best dropdown value based on context"""
        field = self.discovered_fields.get(field_name)
        
        if not field or field.type != 'drop_down' or not field.options:
            return None
        
        # Get context for detection
        csv_filename = context_data.get('csv_filename', '').lower()
        company_name = context_data.get('company', '').lower()
        
        # Industry/Category detection patterns
        if 'industry' in field_name.lower() or 'category' in field_name.lower():
            return self._detect_industry(field.options, csv_filename, company_name)
        
        # Source/Import detection patterns  
        if 'source' in field_name.lower() or 'import' in field_name.lower():
            return self._detect_source(field.options, csv_filename)
        
        # Status/Stage detection (default to first option)
        if 'status' in field_name.lower() or 'stage' in field_name.lower():
            # Default to first option (usually "Prospect" or "New")
            return list(field.options.values())[0]
        
        # Default to first option for any unhandled dropdown
        return list(field.options.values())[0]
    
    def _detect_industry(self, options: Dict[str, str], filename: str, company: str) -> str:
        """Detect industry from filename and company context"""
        # Industry detection patterns
        industry_patterns = {
            'real estate': ['real_estate', 'commercial', 'property', 'realty'],
            'technology': ['tech', 'software', 'cto', 'developer', 'it'],
            'food': ['restaurant', 'food', 'beverage', 'dining', 'cafe'],
            'healthcare': ['healthcare', 'dental', 'medical', 'health'],
            'nonprofit': ['nonprofit', 'non-profit', 'charity', 'foundation'],
            'home services': ['landscaping', 'pool', 'construction', 'home'],
            'marketing': ['marketing', 'design', 'advertising', 'creative'],
            'business': ['business', 'entrepreneur', 'founder', 'owner']
        }
        
        # Check each available option
        for option_name, option_id in options.items():
            option_lower = option_name.lower()
            
            # Check if context matches this option
            for category, keywords in industry_patterns.items():
                if any(keyword in option_lower for keyword in keywords):
                    if any(keyword in filename or keyword in company for keyword in keywords):
                        logger.info(f"🏭 Detected category: {option_name}")
                        return option_id
        
        # Default to "General Business" or first option
        for option_name, option_id in options.items():
            if 'general' in option_name.lower() or 'business' in option_name.lower():
                return option_id
        
        return list(options.values())[0]
    
    def _detect_source(self, options: Dict[str, str], filename: str) -> str:
        """Detect import source from filename"""
        source_patterns = {
            'website': ['web', 'online', 'digital'],
            'event': ['event', 'conference', 'trade_show'],
            'referral': ['referral', 'reference', 'word_of_mouth'],
            'manual': ['manual', 'direct', 'custom']
        }
        
        # Check each available option
        for option_name, option_id in options.items():
            option_lower = option_name.lower()
            
            for category, keywords in source_patterns.items():
                if any(keyword in option_lower for keyword in keywords):
                    if any(keyword in filename for keyword in keywords):
                        logger.info(f"📥 Detected source: {option_name}")
                        return option_id
        
        # Default to first option
        return list(options.values())[0]
    
    def process_csv(self, csv_file_path: str, test_mode: bool = False) -> bool:
        """Process any CSV file and upload to ClickUp"""
        logger.info(f"🚀 Processing CSV: {csv_file_path}")
        
        try:
            # Read and analyze CSV
            df = pd.read_csv(csv_file_path)
            logger.info(f"📊 Loaded {len(df)} rows with {len(df.columns)} columns")
            
            # Build CSV mapping
            self.csv_mapping = self._intelligent_csv_mapping(df.columns.tolist())
            
            if not self.csv_mapping:
                logger.error("❌ No CSV columns could be mapped to ClickUp fields")
                return False
            
            # Test mode - only process first 3 rows
            if test_mode:
                df = df.head(3)
                logger.info(f"🧪 Test mode: Processing only {len(df)} rows")
            
            # Clean and process data
            processed_leads = self._clean_and_process_data(df, csv_file_path)
            
            # Upload to ClickUp
            success_count = self._upload_to_clickup(processed_leads)
            
            logger.info(f"🎉 Successfully processed {success_count}/{len(processed_leads)} leads")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error processing CSV: {str(e)}")
            return False
    
    def _clean_and_process_data(self, df: pd.DataFrame, csv_filename: str) -> List[Dict]:
        """Clean and standardize CSV data"""
        logger.info("🧹 Cleaning and processing data...")
        
        processed_leads = []
        
        for index, row in df.iterrows():
            lead_data = {}
            
            # Map CSV columns to ClickUp fields
            for csv_col, clickup_field_id in self.csv_mapping.items():
                value = row.get(csv_col)
                
                if pd.notna(value) and str(value).strip():
                    # Find field info
                    field_info = None
                    for field_name, field in self.discovered_fields.items():
                        if field.id == clickup_field_id:
                            field_info = field
                            break
                    
                    if field_info:
                        # Clean value based on field type
                        cleaned_value = self._clean_field_value(str(value), field_info.type, field_info.id)
                        if cleaned_value:
                            lead_data[clickup_field_id] = cleaned_value
            
            # Add dropdown values
            context = {
                'csv_filename': os.path.basename(csv_filename),
                'company': lead_data.get(self._get_field_id_by_pattern(['company']), '')
            }
            
           # for field_name, field in self.discovered_fields.items():
               # if field.type == 'drop_down' and field.id not in lead_data:
                   # dropdown_value = self._detect_dropdown_value(field_name, context)
                   # if dropdown_value:
                       # lead_data[field.id] = dropdown_value
            
            if lead_data:  # Only add if we have some data
                processed_leads.append(lead_data)
        
        logger.info(f"✅ Processed {len(processed_leads)} valid leads")
        return processed_leads
    
    def _get_field_id_by_pattern(self, patterns: List[str]) -> Optional[str]:
        """Get field ID by matching name patterns"""
        for field_name, field in self.discovered_fields.items():
            if any(pattern in field_name.lower() for pattern in patterns):
                return field.id
        return None
    
    def _clean_field_value(self, value: str, field_type: str, field_id: str = None) -> Optional[str]:
        """Clean value based on ClickUp field type"""
        value = str(value).strip()
        
        if not value or value.lower() in ['nan', 'null', 'none', '']:
            return None
        
        if field_type == 'email':
            # Basic email validation
            if '@' in value and '.' in value:
                return value.lower()
            return None
        
        elif field_type == 'phone':
            # Use EXACT v2 format that works: +1 XXX XXX XXXX
            if pd.isna(value) or not value:
                return None
            # Remove all non-digit characters
            cleaned = re.sub(r'[^\d]', '', str(value))
            # Format exactly like working leads: +1 XXX XXX XXXX
            if len(cleaned) == 10:
                return f"+1 {cleaned[:3]} {cleaned[3:6]} {cleaned[6:]}"
            elif len(cleaned) == 11 and cleaned[0] == '1':
                clean_10 = cleaned[1:]
                return f"+1 {clean_10[:3]} {clean_10[3:6]} {clean_10[6:]}"
            return None
        
        elif field_type == 'url':
            # Ensure URL has protocol
            if value and not value.startswith(('http://', 'https://')):
                return f"https://{value}"
            return value
        
        elif field_type == 'drop_down':
            # For dropdown fields, we need to convert text to UUID
            # Find the specific field info using field_id
            field_info = None
            for field_name, field in self.discovered_fields.items():
                if field.id == field_id and field.type == 'drop_down':
                    field_info = field
                    break
            
            if field_info and field_info.options:
                # Check if value matches any option name (case insensitive)
                for option_name, option_uuid in field_info.options.items():
                    if value.lower() == option_name.lower():
                        logger.info(f"🎯 Converted '{value}' to '{option_name}' UUID: {option_uuid}")
                        return option_uuid
                
                # If no exact match, try partial match
                for option_name, option_uuid in field_info.options.items():
                    if value.lower() in option_name.lower() or option_name.lower() in value.lower():
                        logger.info(f"🎯 Partial match '{value}' → '{option_name}' UUID: {option_uuid}")
                        return option_uuid
            
            # If no match found, return None to skip this field
            logger.warning(f"⚠️ No dropdown option found for '{value}'. Available options: {list(field_info.options.keys()) if field_info and field_info.options else 'None'}")
            return None
        
        elif field_type == 'currency':
            # Extract numeric value
            numeric = re.sub(r'[^\d.]', '', value)
            try:
                return str(float(numeric))
            except:
                return "0"
        
        return value
    
    def _upload_to_clickup(self, leads: List[Dict]) -> int:
        """Upload processed leads to ClickUp using two-step approach for phone numbers"""
        logger.info(f"📤 Uploading {len(leads)} leads to ClickUp...")
        
        success_count = 0
        
        for i, lead_data in enumerate(leads, 1):
            try:
                # STEP 1: Create task WITHOUT phone field
                phone_value = None
                phone_field_id = None
                lead_data_copy = lead_data.copy()  # Don't modify original
                
                # Extract phone field if present
                for field_id, value in list(lead_data_copy.items()):
                    # Find phone field by checking discovered fields
                    for field_name, field in self.discovered_fields.items():
                        if field.id == field_id and field.type == 'phone':
                            phone_value = value
                            phone_field_id = field_id
                            # Remove phone from initial payload
                            del lead_data_copy[field_id]
                            logger.info(f"📞 Extracted phone for later: {phone_value}")
                            break
                    if phone_value:
                        break
                
                # Create task payload without phone
                task_payload = {
                    "name": f"Lead {i}",
                    "description": f"Imported lead {i}",
                    "custom_fields": []
                }
                
                # Add all non-phone custom fields
                for field_id, value in lead_data_copy.items():
                    task_payload["custom_fields"].append({
                        "id": field_id,
                        "value": value
                    })
                
                logger.info(f"🚀 Step 1 - Creating task without phone field")
                
                # Create task without phone
                url = f"{self.base_url}/list/{self.list_id}/task"
                response = requests.post(url, headers=self.headers, json=task_payload)
                
                if response.status_code == 200:
                    task_data = response.json()
                    task_id = task_data.get('id')
                    logger.info(f"✅ Created task: {task_id}")
                    
                    # STEP 2: Update task with phone number if we have one
                    if phone_value and phone_field_id:
                        phone_payload = {
                            "custom_fields": [
                                {
                                    "id": phone_field_id,
                                    "value": phone_value
                                }
                            ]
                        }
                        
                        logger.info(f"📞 Step 2 - Adding phone to task {task_id}: {phone_value}")
                        
                        update_url = f"{self.base_url}/task/{task_id}"
                        update_response = requests.put(update_url, headers=self.headers, json=phone_payload)
                        
                        if update_response.status_code == 200:
                            logger.info(f"✅ Successfully added phone number to task {task_id}")
                        else:
                            logger.warning(f"⚠️ Failed to add phone to task {task_id}: {update_response.status_code} - {update_response.text}")
                            # Still count as success since task was created
                    
                    success_count += 1
                else:
                    logger.error(f"❌ Failed to create task {i}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"❌ Error uploading lead {i}: {str(e)}")
        
        return success_count

def main():
    parser = argparse.ArgumentParser(description='Universal CSV-to-ClickUp Processor')
    parser.add_argument('--token', help='ClickUp API token')
    parser.add_argument('--list-id', required=True, help='ClickUp list ID')
    parser.add_argument('--csv-file', required=True, help='Path to CSV file')
    parser.add_argument('--test-mode', action='store_true', help='Process only first 3 rows')
    
    args = parser.parse_args()
    
    # Get token from args or environment
    token = args.token or os.getenv('CLICKUP_TOKEN')
    if not token:
        print("❌ No ClickUp token provided")
        print("💡 Use --token YOUR_TOKEN or set CLICKUP_TOKEN in .env")
        return
    
    # Initialize universal processor
    logger.info("🚀 Starting Universal CSV-to-ClickUp Processor v3 - FIXED")
    processor = UniversalClickUpProcessor(token, args.list_id)
    
    # Process CSV
    success = processor.process_csv(args.csv_file, args.test_mode)
    
    if success:
        logger.info("🎉 Processing completed successfully!")
    else:
        logger.error("❌ Processing failed!")

if __name__ == "__main__":
    main()
