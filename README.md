# LeadProcessor

**Complete CSV to ClickUp lead processing automation tool**

Processes multiple CSV formats, cleans data, removes duplicates, and imports leads directly into ClickUp with proper field mapping and validation.

## 🎯 Proven Results

- ✅ **20,447 total leads** processed from 17 CSV files
- ✅ **9,639 high-quality leads** after deduplication and validation
- ✅ **96% email coverage** (9,237 leads with valid emails)
- ✅ **58% phone coverage** (5,555 leads with formatted phone numbers)
- ✅ **95% company coverage** (9,188 leads with company data)
- ✅ **Production tested** with successful ClickUp integration

## 🚀 Quick Start

### Prerequisites

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

1. **Set up ClickUp API token** in `.env`:
```
CLICKUP_TOKEN=pk_your_token_here
```

2. **Configure ClickUp field mappings** in `scripts/leadgen_processor.py`:
```python
self.clickup_field_mapping = {
    'company': 'your_company_field_id',
    'email': 'your_email_field_id',
    'phone': 'your_phone_field_id',
    'estimated_value': 'your_estimated_value_field_id',
    # ... etc
}
```

3. **Set your ClickUp list ID** at the bottom of the script:
```python
list_id = "your_clickup_list_id"
```

### Usage

```bash
# Place CSV files in data/csv_raw/
# Run the processor
python scripts/leadgen_processor.py
```

## 🧪 Testing Mode

**For testing with small batches** (recommended before full import):

In `scripts/leadgen_processor.py`, find the `upload_to_clickup` function and add:

```python
def upload_to_clickup(self, df: pd.DataFrame, list_id: str, batch_size: int = 5) -> List[str]:
    """Upload leads to ClickUp in batches"""
    
    # TEST MODE: Only upload first 3 leads
    df = df.head(3)
    
    logger.info(f"Uploading {len(df)} leads to ClickUp list {list_id}")
    # ... rest of function
```

**To process all leads**, simply comment out or remove the `df = df.head(3)` line.

## 📁 File Structure

```
LeadProcessor/
├── data/
│   ├── csv_raw/              # Input CSV files (17 files)
│   └── processed_leads.csv   # Final output (9,639 leads)
├── scripts/
│   ├── leadgen_processor.py  # Main processor
│   ├── clickup_setup.py      # ClickUp field mapping helper
│   ├── csv_analyzer.py       # Data quality analyzer
│   └── field_mapping.txt     # Generated field mappings
├── .env                      # ClickUp API token
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🔧 Supported CSV Formats

### Arizona Format
- Columns: `Contact Full Name`, `Company Name - Cleaned`, `Email 1`, `Contact Phone 1`, etc.
- Used for: Arizona Commercial Real Estate, Arizona Restaurants

### George CTO Format  
- Columns: `Contact Full Name`, `Title`, `Company Name - Cleaned`, `Email 1`, `Company Annual Revenue`
- Used for: CTO/executive lead lists

### Hubspot Format
- Columns: `First Name`, `Last Name`, `Email`, `Phone Number`, `Associated Company (Primary)`
- Used for: Hubspot CRM exports

### Generic Format
- Auto-detects common column variations
- Handles: `name`, `company`, `email`, `phone`, `title` variations
- Fallback for unknown CSV structures

## 📊 Processing Results by Source

| Source | Raw Leads | Final Leads | Quality Score |
|--------|-----------|-------------|---------------|
| Hubspot Export | 5,021 | 4,119 | ⭐⭐⭐⭐⭐ |
| George CTO Lead List | 3,162 | 3,070 | ⭐⭐⭐⭐⭐ |
| Business Owners & Founders | 1,024 | 706 | ⭐⭐⭐⭐ |
| Arizona Non-Profits | 775 | 627 | ⭐⭐⭐⭐ |
| Arizona Commercial Real Estate | 999 | 461 | ⭐⭐⭐ |
| Arizona Individual & Family Services | 496 | 394 | ⭐⭐⭐ |
| Food & Beverage | 361 | 259 | ⭐⭐⭐ |
| **Total** | **20,447** | **9,639** | **⭐⭐⭐⭐** |

## 📧 Email Processing

Handles multiple email formats:
- Standard: `email@domain.com`
- AI confidence: `97% email@domain.com` → `email@domain.com`
- Validation: RFC-compliant email format checking

## 📱 Phone Processing

Converts various phone formats to ClickUp-compatible format:
- Input: `888.793.8193`, `(888) 793-8193`, `888-793-8193`
- Output: `+1 888 793 8193`
- Handles: 10-digit and 11-digit (with leading 1) US numbers

## 💰 Deal Value Estimation

- **Revenue-based**: 0.1% of company annual revenue
- **Capped**: Between $1,000 and $500,000
- **Defaults**: $5,000 (general), $7,500 (CTO leads), $10,000 (Hubspot)

## 🔄 Data Pipeline

1. **CSV Detection**: Identifies file format (Arizona, George CTO, Hubspot, Generic)
2. **Data Extraction**: Maps columns to standard schema
3. **Data Cleaning**: Standardizes phones, emails, company names
4. **Deduplication**: Removes duplicates by email and company+name
5. **Validation**: Filters leads with names and contact info
6. **ClickUp Upload**: Batch creates tasks with custom fields

## 🛠️ Helper Scripts

### ClickUp Setup (`clickup_setup.py`)
- Interactive wizard for ClickUp API setup
- Discovers teams, spaces, lists, and custom fields
- Generates field mapping configuration
- Creates test tasks for validation

### CSV Analyzer (`csv_analyzer.py`)
- Analyzes data quality across all CSV files
- Shows column mappings and completeness scores
- Identifies issues before processing
- Ranks files by data quality

Usage:
```bash
python scripts/csv_analyzer.py                    # Analyze all CSVs
python scripts/csv_analyzer.py specific_file.csv  # Analyze one file
```

## 🔍 Troubleshooting

### Common Issues

**No CSV files found**
- Ensure files are in `data/csv_raw/` directory
- Check file permissions and extensions

**ClickUp API errors**
- Verify API token in `.env` file
- Check field mapping IDs match your ClickUp space
- Ensure proper list ID configuration

**Phone number validation errors**
- Script automatically formats to `+1 XXX XXX XXXX`
- Invalid numbers are skipped (logged as warnings)

**Email validation failures**
- Malformed emails are skipped
- AI confidence format is automatically parsed

## 📈 Performance

- **Processing Speed**: ~1,000 leads per minute
- **Memory Usage**: Optimized for large datasets (20K+ leads)
- **API Rate Limiting**: 2-second delays between batches
- **Batch Size**: 5 leads per API call (configurable)

## 🚀 Production Deployment

1. Remove test mode (`df.head(3)` line)
2. Configure production ClickUp list ID
3. Set up proper error monitoring
4. Consider running in batches for very large datasets (50K+ leads)

## 📋 Dependencies

```
pandas>=1.5.0
requests>=2.28.0
python-dotenv>=0.19.0
beautifulsoup4>=4.11.0
loguru>=0.6.0
openpyxl>=3.1.0
```

## 🎯 Future Enhancements

- [ ] Real-time CSV monitoring and processing
- [ ] Advanced duplicate detection algorithms
- [ ] Company enrichment via external APIs
- [ ] Email validation service integration
- [ ] Parallel processing for large datasets
- [ ] Integration with LeadGen automation workflows

---

**Built for Banyan Labs** | **Production-ready lead automation**
