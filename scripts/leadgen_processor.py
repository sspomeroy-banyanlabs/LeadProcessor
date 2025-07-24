#!/usr/bin/env python3
"""
LeadGen CSV to ClickUp Processor
Cleans and standardizes lead data from multiple CSV sources for ClickUp import
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
        
        # ClickUp field mapping - CONFIGURED FOR YOUR SANDBOX
        self.clickup_field_mapping = {
            'company': '0945b0ab-20e6-4f19-9667-a0d11ab32f0e',
            'email': 'b07a69f3-1ba6-4520-bb5a-f513b573fb2e',
            'phone': '6eff29cc-d7b8-4517-8d4e-ff0ba486973a',
            'estimated_value': '25945e8b-0126-405d-95eb-d0d8ca09bbb3',
            'last_contact': 'a5be2a78-bd38-4393-a193-41648af324b8',
            'opportunity_stage': 'f803fb30-8709-4294-9421-22546ccd219f',
            'opportunity_type': '46389a05-2371-434a-9dba-82e152e2e53b'
        }
        
        # Default values for new leads
        self.default_values = {
            'opportunity_stage': 'New',
            'last_contact': datetime.now().strftime('%Y-%m-%d'),
            'estimated_value': 0
        }

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
            'source': 'Arizona Commercial Real Estate'
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
            'source': 'George CTO Lead List'
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
        
        processed = pd.DataFrame({
            'first_name': df['First Name'],
            'last_name': df['Last Name'],
            'title': df['Job Title'] if 'Job Title' in df.columns else None,
            'company': df['Associated Company (Primary)'].apply(self.standardize_company_name) if 'Associated Company (Primary)' in df.columns else None,
            'email': df['Email'].apply(self.clean_email),
            'phone': df['Phone Number'].apply(self.clean_phone_number) if 'Phone Number' in df.columns else None,
            'industry': df['Industry'] if 'Industry' in df.columns else None,
            'source': 'Hubspot Export'
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
        
        df = pd.read_csv(file_path)
        columns_lower = [col.lower() for col in df.columns]
        
        # Try to find common patterns
        name_col = None
        first_name_col = None
        last_name_col = None
        email_col = None
        phone_col = None
        company_col = None
        title_col = None
        
        for i, col in enumerate(df.columns):
            col_lower = col.lower()
            
            if 'full name' in col_lower or col_lower == 'name':
                name_col = col
            elif 'first name' in col_lower:
                first_name_col = col
            elif 'last name' in col_lower:
                last_name_col = col
            elif 'email' in col_lower:
                email_col = col
            elif 'phone' in col_lower:
                phone_col = col
            elif 'company' in col_lower:
                company_col = col
            elif 'title' in col_lower:
                title_col = col
        
        processed = pd.DataFrame({
            'name': df[name_col] if name_col else None,
            'first_name': df[first_name_col] if first_name_col else None,
            'last_name': df[last_name_col] if last_name_col else None,
            'title': df[title_col] if title_col else None,
            'company': df[company_col].apply(self.standardize_company_name) if company_col else None,
            'email': df[email_col].apply(self.clean_email) if email_col else None,
            'phone': df[phone_col].apply(self.clean_phone_number) if phone_col else None,
            'source': f'Generic CSV: {Path(file_path).name}',
            'estimated_value': 5000
        })
        
        # Create name if missing
        if name_col is None and first_name_col and last_name_col:
            processed['name'] = (
                processed['first_name'].astype(str) + ' ' + 
                processed['last_name'].astype(str)
            ).str.strip()
        
        return processed

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
        
        # Create description with available info
        description_parts = [f"Lead from {lead.get('source', 'Unknown')}"]
        if lead.get('title'):
            description_parts.append(f"Title: {lead['title']}")
        if lead.get('industry'):
            description_parts.append(f"Industry: {lead['industry']}")
        
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
                if 'arizona' in file_name:
                    df = self.process_arizona_csv(str(csv_file))
                elif 'george' in file_name or 'cto' in file_name:
                    df = self.process_george_cto_csv(str(csv_file))
                elif 'hubspot' in file_name:
                    df = self.process_hubspot_csv(str(csv_file))
                else:
                    logger.info(f"🔍 Processing as generic CSV: {csv_file}")
                    df = self.process_generic_csv(str(csv_file))
                
                all_leads.append(df)
                logger.info(f"✅ Processed {len(df)} leads from {csv_file.name}")
                
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
    
    print(f"\n💾 Processed data saved to: processed_leads.csv")
    
    # UPLOAD TO CLICKUP - CONFIGURED FOR YOUR SANDBOX
    list_id = "901316698136"
    print(f"\n🚀 Uploading to ClickUp list: {list_id}")
    task_ids = processor.upload_to_clickup(processed_leads, list_id)
    print(f"✅ Created {len(task_ids)} tasks in ClickUp!")

if __name__ == "__main__":
    main()
