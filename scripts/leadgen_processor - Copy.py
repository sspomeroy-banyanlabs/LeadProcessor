#!/usr/bin/env python3
#v11
"""
LeadGen CSV to ClickUp Processor
Cleans and standardizes lead data from multiple CSV sources for ClickUp import
Enhanced with automatic industry detection based on source
"""

import pandas as pd
import requests
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LeadGenProcessor:
    def __init__(self, clickup_token: str = None):
        """Initialize the processor with ClickUp API token"""
        self.clickup_token = clickup_token or os.getenv('CLICKUP_TOKEN')
        self.clickup_headers = {
            'Authorization': self.clickup_token,
            'Content-Type': 'application/json'
        }
        
        # Industry dropdown option UUIDs - BANYAN CRM (Production)
        self.banyan_industry_uuids = {
            'Real Estate': '49948abe-7bfe-4c28-a3a6-e4cd44b31fbf',
            'Technology': '5cd90d82-5807-470a-88c9-78c0ebf76283', 
            'Food & Beverage': 'f6d00d4c-0e88-46b5-a39f-60ccc9412ba5',
            'Healthcare/Dental': '0a455ced-8153-4fcc-b5b6-a6df5281a73f',
            'Non-Profit': '39289333-cf75-4dbb-b1a1-25e8c8b5b6ef',
            'Home Services': 'af306f65-b217-440c-b89c-2efea60e3a09',
            'Entrepreneurship': '40a69ef1-bb05-4efe-a687-b99f8ab45fcc',
            'Marketing/Design': 'fd29c12b-a143-4c05-b1cf-dd13608311f6',
            'General Business': 'b49cc787-79bd-48ff-bbbb-5a6ae32eb388'
        }
        
        # Industry dropdown option UUIDs - LEADGEN SAMPLE CRM (Testing)
        self.sample_industry_uuids = {
            'Real Estate': '2a41e944-36ad-4ee2-90e5-5b4d5248958e',
            'Technology': '8ad8c8b7-17b1-41fc-987c-946fd8444373',
            'Food & Beverage': '40d93476-3c7d-4db8-abc3-7df5d25c1167',
            'Healthcare/Dental': '8063b684-4de9-4d1c-bed7-fed75d79245d',
            'Non-Profit': 'b5d9b630-5ce3-4558-847e-6a9d75fc0e8a',
            'Home Services': '98d3b992-aaab-4ed3-a114-5370d58720e8',
            'Entrepreneurship': '5338d0ff-28ba-4976-8d1b-c2ea1af89ddc',
            'Marketing/Design': '87cab2f7-13c8-4d49-9a1c-00117b4071d9',
            'General Business': '49c21b2f-458d-4ff8-a456-72602d5b4033'
        }
        
        # Field mappings for different environments
        self.banyan_field_mapping = {
            'company': '0945b0ab-20e6-4f19-9667-a0d11ab32f0e',
            'email': 'b07a69f3-1ba6-4520-bb5a-f513b573fb2e',
            'phone': '6eff29cc-d7b8-4517-8d4e-ff0ba486973a',
            'estimated_value': '25945e8b-0126-405d-95eb-d0d8ca09bbb3',
            'last_contact': 'a5be2a78-bd38-4393-a193-41648af324b8',
            'opportunity_stage': 'f803fb30-8709-4294-9421-22546ccd219f',
            'opportunity_type': '46389a05-2371-434a-9dba-82e152e2e53b',
            'industry': 'a76893ac-c9d4-4886-a9e2-d850bbd7d151'  # Banyan CRM Industry field
        }
        
        self.sample_field_mapping = {
            'company': '0945b0ab-20e6-4f19-9667-a0d11ab32f0e',
            'email': 'b07a69f3-1ba6-4520-bb5a-f513b573fb2e',
            'phone': '6eff29cc-d7b8-4517-8d4e-ff0ba486973a',
            'estimated_value': '25945e8b-0126-405d-95eb-d0d8ca09bbb3',
            'last_contact': 'a5be2a78-bd38-4393-a193-41648af324b8',
            'opportunity_stage': 'f803fb30-8709-4294-9421-22546ccd219f',
            'opportunity_type': '46389a05-2371-434a-9dba-82e152e2e53b',
            'industry': '79fa76e2-4c2f-433d-bc93-b070fbf9778e'  # Sample CRM Industry field
        }
        
        # Default to Banyan (will be overridden in upload method)
        self.clickup_field_mapping = self.banyan_field_mapping
        self.industry_uuids = self.banyan_industry_uuids
        
        # Default values for new leads
        self.default_values = {
            'opportunity_stage': 'New',
            'last_contact': datetime.now().strftime('%Y-%m-%d'),
            'estimated_value': 0
        }

    def detect_industry_from_source(self, source: str) -> str:
        """
        Determine industry based on source/filename - same logic as the cleanup script
        """
        if not source:
            return 'General Business'
        
        source_lower = source.lower()
        
        # Check for specific industries based on source names
        if any(word in source_lower for word in ['restaurant', 'food', 'beverage']):
            return 'Food & Beverage'
        elif any(word in source_lower for word in ['real_estate', 'commercial']):
            return 'Real Estate'
        elif any(word in source_lower for word in ['tech', 'software', 'cto']):
            return 'Technology'
        elif 'non_profit' in source_lower:
            return 'Non-Profit'
        elif any(word in source_lower for word in ['dental', 'dentist']):
            return 'Healthcare/Dental'
        elif any(word in source_lower for word in ['landscaping', 'pool']):
            return 'Home Services'
        elif any(word in source_lower for word in ['diversity', 'equity', 'inclusion']):
            return 'Consulting/HR'
        elif 'chief_people_officer' in source_lower:
            return 'Human Resources'
        elif any(word in source_lower for word in ['business_owner', 'founder']):
            return 'Entrepreneurship'
        elif 'web_design' in source_lower:
            return 'Marketing/Design'
        elif 'social_impact' in source_lower:
            return 'Social Impact'
        elif 'individual_family_services' in source_lower:
            return 'Social Services'
        else:
            return 'General Business'

    def clean_phone_number(self, phone: str) -> Optional[str]:
        """Clean and standardize phone numbers for ClickUp - format: +1 XXX XXX XXXX"""
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

    def clean_email(self, email: str) -> Optional[str]:
        """Validate and clean email addresses, including AI confidence format"""
        if pd.isna(email) or not email:
            return None
            
        email_str = str(email).strip().lower()
        
        # Handle AI confidence format like "97% email@domain.com"
        if '%' in email_str:
            # Extract email after the percentage
            parts = email_str.split('%', 1)
            if len(parts) > 1:
                email_str = parts[1].strip()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email_str):
            return email_str
        
        return None

    def standardize_company_name(self, company: str) -> Optional[str]:
        """Clean and standardize company names"""
        if pd.isna(company) or not company:
            return None
            
        company = str(company).strip()
        
        # Remove common suffixes for consistency
        suffixes = [', Inc.', ', LLC', ', Corp.', ', Corporation', ', Ltd.']
        for suffix in suffixes:
            if company.endswith(suffix):
                company = company[:-len(suffix)]
        
        return company.title()

    def estimate_value_from_revenue(self, revenue: float) -> int:
        """Estimate deal value based on company revenue"""
        if pd.isna(revenue) or revenue <= 0:
            return 5000  # Default value
            
        # Simple estimation: assume deal is 0.1% of company revenue
        estimated = int(revenue * 0.001)
        
        # Cap between $1K and $500K
        return max(1000, min(500000, estimated))

    def process_arizona_csv(self, file_path: str) -> pd.DataFrame:
        """Process Arizona Commercial Real Estate CSV"""
        logger.info(f"Processing Arizona CSV: {file_path}")
        
        df = pd.read_csv(file_path)
        
        # Determine source name for industry detection
        source_name = f'Arizona Commercial Real Estate'
        
        # Map columns to standard format
        processed = pd.DataFrame({
            'name': df['Contact Full Name'],
            'first_name': df['First Name'], 
            'last_name': df['Last Name'],
            'title': df['Title'],
            'company': df['Company Name - Cleaned'].apply(self.standardize_company_name),
            'email': df['Email 1'].apply(self.clean_email),
            'email_backup': df['Email 2'].apply(self.clean_email) if 'Email 2' in df.columns else None,
            'phone': df['Contact Phone 1'].apply(self.clean_phone_number),
            'phone_backup': df['Company Phone 1'].apply(self.clean_phone_number) if 'Company Phone 1' in df.columns else None,
            'company_revenue': df['Company Annual Revenue'] if 'Company Annual Revenue' in df.columns else None,
            'source': source_name,
            'industry': self.detect_industry_from_source(source_name)  # Auto-detect industry
        })
        
        # Fill missing names
        processed['name'] = processed['name'].fillna(
            processed['first_name'].astype(str) + ' ' + processed['last_name'].astype(str)
        )
        
        # Estimate deal values
        if 'company_revenue' in processed.columns and processed['company_revenue'].notna().any():
            processed['estimated_value'] = processed['company_revenue'].apply(self.estimate_value_from_revenue)
        else:
            processed['estimated_value'] = 5000  # Default value
        
        return processed

    def process_george_cto_csv(self, file_path: str) -> pd.DataFrame:
        """Process George CTO Lead List CSV"""
        logger.info(f"Processing George CTO CSV: {file_path}")
        
        df = pd.read_csv(file_path)
        
        # Determine source name for industry detection
        source_name = f'George CTO Lead List'
        
        processed = pd.DataFrame({
            'name': df['Contact Full Name'],
            'first_name': df['First Name'],
            'last_name': df['Last Name'], 
            'title': df['Title'],
            'company': df['Company Name - Cleaned'].apply(self.standardize_company_name),
            'email': df['Email 1'].apply(self.clean_email),
            'email_backup': df['Email 2'].apply(self.clean_email) if 'Email 2' in df.columns else None,
            'phone': df['Contact Phone 1'].apply(self.clean_phone_number),
            'phone_backup': df['Company Phone 1'].apply(self.clean_phone_number) if 'Company Phone 1' in df.columns else None,
            'company_revenue': df['Company Annual Revenue'] if 'Company Annual Revenue' in df.columns else None,
            'source': source_name,
            'industry': self.detect_industry_from_source(source_name)  # Auto-detect industry
        })
        
        # Fill missing names
        processed['name'] = processed['name'].fillna(
            processed['first_name'].astype(str) + ' ' + processed['last_name'].astype(str)
        )
        
        # Estimate deal values  
        if 'company_revenue' in processed.columns and processed['company_revenue'].notna().any():
            processed['estimated_value'] = processed['company_revenue'].apply(self.estimate_value_from_revenue)
        else:
            processed['estimated_value'] = 7500  # Default for CTO leads (higher value)
        
        return processed

    def process_hubspot_csv(self, file_path: str) -> pd.DataFrame:
        """Process Hubspot Exports CSV"""
        logger.info(f"Processing Hubspot CSV: {file_path}")
        
        df = pd.read_csv(file_path)
        
        # Determine source name for industry detection
        source_name = f'Hubspot Export'
        
        processed = pd.DataFrame({
            'first_name': df['First Name'],
            'last_name': df['Last Name'],
            'title': df['Job Title'] if 'Job Title' in df.columns else None,
            'company': df['Associated Company (Primary)'].apply(self.standardize_company_name) if 'Associated Company (Primary)' in df.columns else None,
            'email': df['Email'].apply(self.clean_email),
            'phone': df['Phone Number'].apply(self.clean_phone_number) if 'Phone Number' in df.columns else None,
            'industry': df['Industry'] if 'Industry' in df.columns else self.detect_industry_from_source(source_name),  # Use HubSpot industry if available, otherwise auto-detect
            'source': source_name
        })
        
        # Create full name
        processed['name'] = (
            processed['first_name'].astype(str) + ' ' + 
            processed['last_name'].astype(str)
        ).str.strip()
        
        # Set default estimated value for Hubspot leads
        processed['estimated_value'] = 10000
        
        return processed

    def process_generic_csv(self, file_path: str) -> pd.DataFrame:
        """Process any other CSV file by trying to map common column names"""
        logger.info(f"Processing generic CSV: {file_path}")
        
        try:
            # First, try reading normally
            df = pd.read_csv(file_path)
            
            # Determine source name for industry detection
            source_name = f'Generic CSV: {Path(file_path).name}'
            
            # Check if this looks like a headerless file (first column contains names)
            first_col_sample = str(df.columns[1]) if len(df.columns) > 1 else str(df.columns[0])
            
            # Detect if the "headers" are actually data (names like Tara, Ron, Julian)
            headerless_indicators = [
                'tara hanley', 'ron williams', 'julian drew',  # Specific names we saw
                any(len(col.split()) == 2 and col.replace(' ', '').isalpha() for col in df.columns[:5])  # Two-word alpha strings
            ]
            
            if any(headerless_indicators) or any(name in first_col_sample.lower() for name in ['tara', 'ron', 'julian']):
                logger.info(f"Detected headerless CSV, re-reading with proper structure")
                # Re-read without headers and assign positional column names based on typical structure
                df = pd.read_csv(file_path, header=None)
                
                # Based on the patterns we saw, map columns positionally
                if len(df.columns) >= 10:
                    # Standard structure: timestamp, name, first, last, title, company, website, list, linkedin, email
                    df.columns = ['timestamp', 'full_name', 'first_name', 'last_name', 'title', 'company', 'website', 'list', 'linkedin', 'email'] + \
                                [f'col_{i}' for i in range(10, len(df.columns))]
                else:
                    df.columns = [f'col_{i}' for i in range(len(df.columns))]
                    
                # Override column detection for headerless files
                name_col = 'full_name' if 'full_name' in df.columns else df.columns[1] if len(df.columns) > 1 else None
                first_name_col = 'first_name' if 'first_name' in df.columns else df.columns[2] if len(df.columns) > 2 else None
                last_name_col = 'last_name' if 'last_name' in df.columns else df.columns[3] if len(df.columns) > 3 else None
                title_col = 'title' if 'title' in df.columns else df.columns[4] if len(df.columns) > 4 else None
                company_col = 'company' if 'company' in df.columns else df.columns[5] if len(df.columns) > 5 else None
                email_col = 'email' if 'email' in df.columns else df.columns[9] if len(df.columns) > 9 else None
                phone_col = None  # Usually not in a predictable position in these files
                
            else:
                # Normal CSV with headers - use original logic
                if df.empty:
                    logger.warning(f"CSV file {file_path} is empty")
                    return pd.DataFrame()
                
                # Debug: Print column names to help troubleshoot
                logger.info(f"Columns found: {list(df.columns)}")
                
                # Try to find common patterns - more flexible matching
                name_col = None
                first_name_col = None
                last_name_col = None
                email_col = None
                phone_col = None
                company_col = None
                title_col = None
                
                for col in df.columns:
                    col_lower = col.lower().strip()
                    
                    # Name field variations
                    if any(x in col_lower for x in ['contact full name', 'full name', 'name']):
                        if not name_col:  # Take first match
                            name_col = col
                    elif any(x in col_lower for x in ['first name', 'firstname', 'fname']):
                        if not first_name_col:
                            first_name_col = col
                    elif any(x in col_lower for x in ['last name', 'lastname', 'lname', 'surname']):
                        if not last_name_col:
                            last_name_col = col
                    
                    # Email field variations
                    elif any(x in col_lower for x in ['email', 'e-mail', 'mail']):
                        if not email_col:
                            email_col = col
                    
                    # Phone field variations
                    elif any(x in col_lower for x in ['phone', 'telephone', 'tel', 'mobile', 'cell']):
                        if not phone_col:
                            phone_col = col
                    
                    # Company field variations
                    elif any(x in col_lower for x in ['company', 'organization', 'org', 'business', 'firm']):
                        if not company_col:
                            company_col = col
                    
                    # Title field variations
                    elif any(x in col_lower for x in ['title', 'position', 'role', 'job']):
                        if not title_col:
                            title_col = col
                
            # Log what we found
            logger.info(f"Mapped fields - Name: {name_col}, First: {first_name_col}, Last: {last_name_col}, Email: {email_col}, Phone: {phone_col}, Company: {company_col}, Title: {title_col}")
            
            # Build the processed DataFrame with safer column access
            processed_data = {}
            
            # Handle name fields
            if name_col and name_col in df.columns:
                processed_data['name'] = df[name_col]
            else:
                processed_data['name'] = None
                
            if first_name_col and first_name_col in df.columns:
                processed_data['first_name'] = df[first_name_col]
            else:
                processed_data['first_name'] = None
                
            if last_name_col and last_name_col in df.columns:
                processed_data['last_name'] = df[last_name_col]
            else:
                processed_data['last_name'] = None
                
            if title_col and title_col in df.columns:
                processed_data['title'] = df[title_col]
            else:
                processed_data['title'] = None
                
            if company_col and company_col in df.columns:
                processed_data['company'] = df[company_col].apply(self.standardize_company_name)
            else:
                processed_data['company'] = None
                
            if email_col and email_col in df.columns:
                processed_data['email'] = df[email_col].apply(self.clean_email)
            else:
                processed_data['email'] = None
                
            if phone_col and phone_col in df.columns:
                processed_data['phone'] = df[phone_col].apply(self.clean_phone_number)
            else:
                processed_data['phone'] = None
            
            # Add source, industry, and estimated value
            processed_data['source'] = source_name
            processed_data['industry'] = self.detect_industry_from_source(source_name)  # Auto-detect industry
            processed_data['estimated_value'] = 5000
            
            # Create DataFrame with explicit index
            processed = pd.DataFrame(processed_data, index=range(len(df)))
            
            # Create name if missing but we have first/last
            if (not processed['name'].notna().any()) and first_name_col and last_name_col:
                processed['name'] = (
                    processed['first_name'].astype(str) + ' ' + 
                    processed['last_name'].astype(str)
                ).str.strip()
                # Clean up "nan nan" entries
                processed['name'] = processed['name'].replace('nan nan', None)
            
            logger.info(f"Successfully processed {len(processed)} leads from generic CSV")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            # Return empty DataFrame with correct structure
            return pd.DataFrame({
                'name': [],
                'first_name': [],
                'last_name': [],
                'title': [],
                'company': [],
                'email': [],
                'phone': [],
                'source': [],
                'industry': [],  # Include industry in empty DataFrame
                'estimated_value': []
            })

    def deduplicate_leads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate leads based on email and company"""
        logger.info("Deduplicating leads...")
        
        original_count = len(df)
        
        # Create boolean masks for duplicates
        email_mask = df['email'].notna()
        email_dupes = df[email_mask].duplicated(subset=['email'], keep='first')
        
        # Expand the mask back to the full DataFrame
        email_dupes_full = pd.Series(False, index=df.index)
        email_dupes_full[df[email_mask].index[email_dupes]] = True
        
        # Company + name duplicates
        company_name_mask = df['company'].notna() & df['name'].notna()
        company_name_dupes = df[company_name_mask].duplicated(subset=['company', 'name'], keep='first')
        
        # Expand the mask back to the full DataFrame
        company_name_dupes_full = pd.Series(False, index=df.index)
        company_name_dupes_full[df[company_name_mask].index[company_name_dupes]] = True
        
        # Combine the duplicate masks
        all_dupes = email_dupes_full | company_name_dupes_full
        
        deduped = df[~all_dupes].copy()
        
        logger.info(f"Removed {original_count - len(deduped)} duplicates, {len(deduped)} leads remaining")
        return deduped

    def validate_leads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and filter leads based on quality criteria"""
        logger.info("Validating leads...")
        
        original_count = len(df)
        
        # Must have name and either email or phone
        valid_leads = df[
            (df['name'].notna()) & 
            (df['name'].str.strip() != '') &
            (df['name'].str.strip() != 'nan nan') &
            ((df['email'].notna()) | (df['phone'].notna()))
        ].copy()
        
        logger.info(f"Filtered from {original_count} to {len(valid_leads)} valid leads")
        return valid_leads

    def create_clickup_task_payload(self, lead: pd.Series, list_id: str) -> Dict[str, Any]:
        """Create ClickUp task payload from lead data"""
        
        # Determine opportunity type from title - use simple values that ClickUp accepts
        title = str(lead.get('title', '')).lower()
        if any(word in title for word in ['cto', 'cio', 'tech', 'it', 'developer', 'engineer']):
            opp_type = 'Tech'
        elif any(word in title for word in ['ceo', 'president', 'owner', 'founder']):
            opp_type = 'Executive'
        elif any(word in title for word in ['sales', 'marketing', 'business', 'bd']):
            opp_type = 'Sales'
        else:
            opp_type = 'General'
        
        # Create description with available info INCLUDING INDUSTRY
        description_parts = [f"Lead from {lead.get('source', 'Unknown')}"]
        if lead.get('title'):
            description_parts.append(f"Title: {lead['title']}")
        if lead.get('industry'):
            description_parts.append(f"Industry: {lead['industry']}")  # This will now be populated!
        
        # Build custom fields - only include fields with valid data
        custom_fields = []
        
        # Company field
        if lead.get('company'):
            custom_fields.append({
                "id": self.clickup_field_mapping['company'],
                "value": str(lead['company'])
            })
        
        # Email field
        if lead.get('email'):
            custom_fields.append({
                "id": self.clickup_field_mapping['email'], 
                "value": str(lead['email'])
            })
        
        # Phone field - with correct +1 XXX XXX XXXX format
        if lead.get('phone'):
            custom_fields.append({
                "id": self.clickup_field_mapping['phone'],
                "value": str(lead['phone'])
            })
        
        # Estimated Value - always include this
        custom_fields.append({
            "id": self.clickup_field_mapping['estimated_value'],
            "value": int(lead.get('estimated_value', 5000))
        })
        
        # Industry field - NEW! Use UUID for dropdown
        if lead.get('industry'):
            industry_uuid = self.industry_uuids.get(lead['industry'])
            if industry_uuid:
                custom_fields.append({
                    "id": self.clickup_field_mapping['industry'],
                    "value": industry_uuid
                })
        
        payload = {
            "name": lead['name'],
            "description": "\n".join(description_parts),
            "assignees": [],
            "tags": [lead.get('source', 'Import').replace(' ', '_')],
            "status": "new",
            "priority": 3,
            "due_date": None,
            "start_date": None,
            "notify_all": False,
            "parent": None,
            "links_to": None,
            "custom_fields": custom_fields
        }
        
        return payload

    def upload_to_clickup(self, df: pd.DataFrame, list_id: str, batch_size: int = 5) -> List[str]:
        """Upload leads to ClickUp in batches"""
        
        # Configure field mappings based on target list
        if list_id == "901316698136":  # LeadGen Sample CRM
            self.clickup_field_mapping = self.sample_field_mapping
            self.industry_uuids = self.sample_industry_uuids
            logger.info("🧪 Using LeadGen Sample CRM field mappings")
        else:  # Banyan CRM (Production)
            self.clickup_field_mapping = self.banyan_field_mapping
            self.industry_uuids = self.banyan_industry_uuids
            logger.info("🚀 Using Banyan CRM field mappings")
        
        # TEST MODE: Only upload first 3 leads
        df = df.head(3)
        
        logger.info(f"Uploading {len(df)} leads to ClickUp list {list_id}")
        
        task_ids = []
        url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            for _, lead in batch.iterrows():
                try:
                    payload = self.create_clickup_task_payload(lead, list_id)
                    
                    response = requests.post(
                        url, 
                        headers=self.clickup_headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        task_id = response.json()['id']
                        task_ids.append(task_id)
                        logger.info(f"✅ Created task for {lead['name']}: {task_id}")
                    else:
                        logger.error(f"❌ Failed to create task for {lead['name']}: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.error(f"❌ Error creating task for {lead['name']}: {str(e)}")
            
            # Small delay between batches to be nice to the API
            import time
            time.sleep(2)
        
        logger.info(f"🎉 Successfully created {len(task_ids)} tasks")
        return task_ids

    def process_all_csvs(self, csv_dir: str = "data/csv_raw", output_file: str = 'processed_leads.csv') -> pd.DataFrame:
        """Process all CSV files in directory and combine them"""
        logger.info(f"Processing all CSVs in directory: {csv_dir}")
        
        all_leads = []
        csv_dir = Path(csv_dir)
        
        # Find all CSV files
        csv_files = list(csv_dir.glob('*.csv'))
        
        if not csv_files:
            logger.error("❌ No CSV files found in directory")
            return pd.DataFrame()
        
        logger.info(f"📁 Found {len(csv_files)} CSV files to process")
        
        # Process each CSV file
        for csv_file in csv_files:
            file_name = csv_file.name.lower()
            
            try:
                if 'arizona' in file_name and ('commercial' in file_name or 'restaurant' in file_name):
                    df = self.process_arizona_csv(str(csv_file))
                elif 'george' in file_name or 'cto' in file_name:
                    df = self.process_george_cto_csv(str(csv_file))
                elif 'hubspot' in file_name:
                    df = self.process_hubspot_csv(str(csv_file))
                else:
                    logger.info(f"🔍 Processing as generic CSV: {csv_file}")
                    df = self.process_generic_csv(str(csv_file))
                
                if not df.empty:
                    all_leads.append(df)
                    logger.info(f"✅ Processed {len(df)} leads from {csv_file.name}")
                else:
                    logger.warning(f"⚠️ No valid leads found in {csv_file.name}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {csv_file}: {str(e)}")
        
        if not all_leads:
            logger.error("❌ No CSV files were successfully processed")
            return pd.DataFrame()
        
        # Combine all leads
        combined_df = pd.concat(all_leads, ignore_index=True)
        logger.info(f"📊 Combined {len(combined_df)} total leads")
        
        # Deduplicate and validate
        deduped_df = self.deduplicate_leads(combined_df)
        validated_df = self.validate_leads(deduped_df)
        
        # Show industry breakdown
        if 'industry' in validated_df.columns:
            logger.info("🏭 Industry Distribution:")
            industry_counts = validated_df['industry'].value_counts()
            for industry, count in industry_counts.items():
                percentage = (count / len(validated_df)) * 100
                logger.info(f"   {industry}: {count} leads ({percentage:.1f}%)")
        
        # Save processed leads
        output_path = csv_dir.parent / output_file
        validated_df.to_csv(output_path, index=False)
        logger.info(f"💾 Saved {len(validated_df)} processed leads to {output_path}")
        
        return validated_df

def main():
    """Main function to run the processor"""
    
    print("🚀 LeadGen CSV Processor Starting...")
    print("=" * 50)
    
    # Initialize processor
    processor = LeadGenProcessor()
    
    # Check if token is loaded
    if not processor.clickup_token:
        print("❌ No CLICKUP_TOKEN found in environment")
        print("💡 Make sure your .env file has: CLICKUP_TOKEN=your_token_here")
        return
    
    print(f"✅ ClickUp token loaded: {processor.clickup_token[:10]}...")
    
    # Process all CSVs in data/csv_raw directory
    processed_leads = processor.process_all_csvs("data/csv_raw")
    
    if len(processed_leads) == 0:
        print("❌ No leads were processed. Check your CSV files and logs.")
        return
    
    print(f"\n🎉 Successfully processed {len(processed_leads)} leads!")
    print(f"📊 Sources breakdown:")
    source_counts = processed_leads['source'].value_counts()
    for source, count in source_counts.items():
        print(f"   📁 {source}: {count:,} leads")
    
    print(f"📧 Leads with emails: {processed_leads['email'].notna().sum():,}")
    print(f"📱 Leads with phones: {processed_leads['phone'].notna().sum():,}")
    print(f"🏢 Leads with companies: {processed_leads['company'].notna().sum():,}")
    
    # Show industry breakdown
    if 'industry' in processed_leads.columns:
        print(f"\n🏭 Industry Distribution:")
        industry_counts = processed_leads['industry'].value_counts()
        for industry, count in industry_counts.items():
            percentage = (count / len(processed_leads)) * 100
            print(f"   {industry}: {count:,} leads ({percentage:.1f}%)")
    
    print(f"\n💾 Processed data saved to: processed_leads.csv")
    
    # UPLOAD TO CLICKUP - TEST MODE: LeadGen Sample CRM
    list_id = "901315917676" # "901316698136"  # LeadGen Sample CRM for testing
    print(f"\n🧪 TEST MODE: Uploading to LeadGen Sample CRM: {list_id}")
    task_ids = processor.upload_to_clickup(processed_leads, list_id)
    print(f"✅ Created {len(task_ids)} test tasks in ClickUp!")

if __name__ == "__main__":
    main()
