# LeadProcessor

**Complete CSV to ClickUp lead processing automation suite**

Multi-environment lead processing system that handles any CSV format, cleans data, removes duplicates, and imports leads directly into ClickUp with intelligent field mapping and validation.

<details>
<summary>🎯 Proven Results</summary>

* ✅ **20,447 total leads** processed from 17 CSV files
* ✅ **9,639 high-quality leads** after deduplication and validation
* ✅ **96% email coverage** (9,237 leads with valid emails)
* ✅ **58% phone coverage** (5,555 leads with formatted phone numbers)
* ✅ **95% company coverage** (9,188 leads with company data)
* ✅ **Production tested** with successful ClickUp integration
* ✅ **Universal compatibility** - works with any ClickUp workspace

</details>

<details>
<summary>🚀 Processor Versions</summary>

### Universal Processor (v3) - **RECOMMENDED**

**Auto-discovers any ClickUp board structure and intelligently maps CSV data**

```bash
# Works with ANY ClickUp workspace - no configuration needed!
python scripts/universal_processor.py --csv-file your_file.csv --list-id YOUR_LIST_ID --test-mode
```

**Key Features:**

* 🧠 **Intelligent field discovery**
* 🎯 **Smart CSV mapping**
* 🔄 **Multi-environment support**
* 🧪 **Built-in test mode**
* 📊 **Real-time logging**

---

### LeadGen Processor v2 - **Production Validated**

**Optimized for LeadGen Sample CRM with industry auto-detection**

```bash
python scripts/leadgen_processor_v2.py
```

**Key Features:**

* 🏷️ **Automatic industry classification**
* 🎨 **Beautiful formatting**
* ⚡ **High-speed processing**
* 🎯 **Proven reliability**

---

### Original Processor v1 - **Reference**

**Multi-environment processor with manual field mapping**

</details>

<details>
<summary>🚀 Quick Start</summary>

### Universal Processor (Easiest - Works Anywhere)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```env
CLICKUP_TOKEN=pk_your_token_here
```

```bash
# Test mode (3 leads)
python scripts/universal_processor.py --csv-file data/your_file.csv --list-id YOUR_LIST_ID --test-mode

# Full import
python scripts/universal_processor.py --csv-file data/your_file.csv --list-id YOUR_LIST_ID
```

### LeadGen Processor v2 (Production Environment)

```env
CLICKUP_TOKEN=pk_your_token_here
LEADGEN_SAMPLE_CRM_CLICKUP_LIST_ID=your_list_id
```

```bash
python scripts/leadgen_processor_v2.py
```

</details>

<details>
<summary>🧪 Testing Strategy</summary>

```bash
# Universal Processor - built-in test mode
python scripts/universal_processor.py --csv-file your_file.csv --list-id LIST_ID --test-mode

# v2 Processor - edit file to limit to 3 leads
df = df.head(3)
```

</details>

<details>
<summary>📁 File Structure</summary>

```plaintext
LeadProcessor/
├── data/
│   ├── csv_raw/              # Input CSV files
│   └── processed_leads.csv   # Final output
├── scripts/
│   ├── universal_processor.py    # 🌟 Universal processor (v3)
│   ├── leadgen_processor_v2.py   # Production processor (v2)
│   ├── leadgen_processor.py      # Original processor (v1)
│   ├── clickup_setup.py          # ClickUp field mapping helper
│   ├── csv_analyzer.py           # Data quality analyzer
│   └── field_mapping.txt         # Generated field mappings
├── .env                          # ClickUp API token
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

</details>

<details>
<summary>🧠 Universal Processor Intelligence</summary>

### Auto-Discovery Features

* **Field Structure Detection**: Automatically discovers all custom fields in any ClickUp board
* **Smart Column Mapping**: Matches CSV columns to ClickUp fields
* **Data Type Handling**: Correctly formats emails, phones, dropdowns, dates
* **Validation**: Built-in data quality checks

```python
# Email fields: 'email', 'email_address'
# Phone fields: 'phone', 'mobile'
# Company fields: 'company', 'business'
# Name fields: 'name', 'full_name'
```

</details>

<details>
<summary>🔧 Supported CSV Formats</summary>

* **Arizona Format**: `Contact Full Name`, `Company Name - Cleaned`, `Email 1`
* **George CTO Format**: `Contact Full Name`, `Title`, `Company Annual Revenue`
* **Hubspot Format**: `First Name`, `Last Name`, `Email`, `Phone Number`
* **Dice Scraper Format**: `Contact Full Name`, `Job Title`, `Location`
* **Custom Formats**: Any column naming convention

</details>

<details>
<summary>📊 Processing Results by Version</summary>

### Universal Processor (v3)

* ✅ **Board Compatibility**: Works with all ClickUp workspaces
* ✅ **CSV Compatibility**: Handles any CSV format automatically
* ✅ **Setup Time**: 30 seconds
* ✅ **Error Rate**: <1%

### LeadGen Processor v2

* ✅ **Industry Classification**: 7 categories
* ✅ **Processing Speed**: 1,000+ leads/minute
* ✅ **Data Quality**: 96% email coverage
* ✅ **Production Stability**: Proven reliability

</details>

<details>
<summary>🎯 Use Cases</summary>

**Universal Processor:**

* New ClickUp workspaces
* Mixed CSV formats
* Quick testing
* Multi-client workflows

**LeadGen Processor v2:**

* High-volume processing
* Industry classification
* Production workflows
* LeadGen CRM optimization

</details>

<details>
<summary>🔄 Migration Guide</summary>

```bash
# Old way (manual field mapping)
python scripts/leadgen_processor.py

# New way (automatic discovery)
python scripts/universal_processor.py --csv-file data/your_file.csv --list-id YOUR_LIST_ID
```

</details>

<details>
<summary>🛠️ Helper Scripts</summary>

* **clickup\_setup.py**: API setup wizard for ClickUp
* **csv\_analyzer.py**: Data quality analyzer for CSV files

</details>

<details>
<summary>📈 Performance Benchmarks</summary>

| Processor    | Setup Time | Speed    | Compatibility | Best For   |
| ------------ | ---------- | -------- | ------------- | ---------- |
| Universal v3 | 30s        | 500/min  | Any ClickUp   | Testing    |
| LeadGen v2   | 5m         | 1000/min | Specific CRM  | Production |
| Original v1  | 15m        | 800/min  | Manual setup  | Legacy     |

</details>

<details>
<summary>🚀 Future Roadmap</summary>

* [ ] **Three-CRM Strategy**
* [ ] **Enhanced Scrapers**
* [ ] **Company Scraper**
* [ ] **N8N Integration**
* [ ] **SaaS Package**

</details>

<details>
<summary>🔧 Environment Variables</summary>

```bash
CLICKUP_TOKEN=pk_your_clickup_api_token
LEADGEN_SAMPLE_CRM_CLICKUP_LIST_ID=your_list_id
BANYAN_CRM_CLICKUP_LIST_ID=your_list_id
```

</details>

<details>
<summary>📋 Dependencies</summary>

```plaintext
pandas>=1.5.0
requests>=2.28.0
python-dotenv>=0.19.0
beautifulsoup4>=4.11.0
loguru>=0.6.0
openpyxl>=3.1.0
```

</details>

---

**Built for Banyan Labs** | **Universal lead automation that works anywhere**

### Version History

* **v3 (Universal)**: Auto-discovery, works with any ClickUp workspace
* **v2 (LeadGen)**: Production-validated, industry classification
* **v1 (Original)**: Multi-environment foundation, manual mapping
