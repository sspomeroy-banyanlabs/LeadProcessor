# LeadGen Tool – Developer Notes & Project Alignment

## 📌 Vision Alignment: pitch deck #86aa9rcer.2.pdf

This pitch deck outlines Banyan Labs' strategic direction and establishes the vision behind the LeadGen Tool MVP.

> **As a team member at Banyan Labs, I want to gather, manage, and enrich leads from multiple sources so I can launch personalized outreach and support the growth of client partnerships.**

### 🔑 Key Goals (Implied from Deck):
- Aggregate lead data from sources like HubSpot, Google Sheets, and CSVs.
- Prevent duplicates across imports and avoid lost data.
- Track changes to lead information over time.
- Surface leads inside ClickUp in a clear, structured, and filterable way.
- Enable future automation of outreach via tags, triggers, or external tools.

---

## ✅ Current Progress (Week 1)
| Feature/Step | Status |
|--------------|--------|
| .env setup and token authentication | ✅ Done |
| CSV ingestion and cleanup | ✅ Done |
| Google Sheets → CSV conversion | ✅ Done |
| Lead deduplication by email | ✅ Done |
| ClickUp list ID discovery | ✅ Done |
| Change logger (`log_lead_change`) | ✅ Done |
| Lead preview in terminal | ✅ Done |
| Proposal for ClickUp custom fields | ✅ Drafted |
| Repo modularity and planning | ✅ In progress |

---

## 📋 Proposed ClickUp Custom Fields
| Field Name        | Type       | Description |
|-------------------|------------|-------------|
| Lead Status        | Dropdown   | Hot, Warm, Cold, Do Not Contact |
| Source             | Text       | e.g., Matthew, Google Sheet |
| Last Updated       | Date       | When lead was last synced |
| First Contacted    | Date       | Outreach initiation |
| Has Email          | Checkbox   | True/False |
| Contact Methods    | Text       | e.g., Phone, LinkedIn |
| Notes              | Long Text  | Free-form lead notes |
| CRM Synced?        | Checkbox   | If auto-imported via script |
| Updated By         | Text       | Developer or automation name |

---

## 🛠️ Dev To-Do
- [ ] Push valid leads to ClickUp
- [ ] Use actual task IDs in `log_lead_change()`
- [ ] Integrate custom fields once approved
- [ ] Add README.md for future devs
- [ ] Tag and commit completed phases
- [ ] Confirm field mapping needs with Matthew
