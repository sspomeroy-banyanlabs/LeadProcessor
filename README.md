# LeadProcessor

Complete CSV to ClickUp lead processing automation tool.

## Features
- Processes 17+ CSV formats (Arizona, George CTO, Hubspot, etc)
- Phone formatting: +1 XXX XXX XXXX (ClickUp validated)
- Email cleaning with AI confidence parsing
- Company name standardization
- Revenue-based deal estimation
- Deduplication and validation

## Usage
1. Add CSV files to `data/csv_raw/`
2. Configure `.env` with ClickUp token
3. Run: `python scripts/leadgen_processor.py`

## Tested
Successfully imported 5,527+ leads to ClickUp sandbox.
