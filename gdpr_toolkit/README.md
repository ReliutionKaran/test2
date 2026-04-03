# GDPR Compliance Toolkit — Odoo 17

A complete internal GDPR compliance module for EU businesses using Odoo.
Covers the obligations that regulators actually check — not just the
customer-facing data deletion form.

## Features

### 1. Consent management (`gdpr.consent`)
- Per-contact consent log with purpose, legal basis, channel, timestamp
- Consent withdrawal with audit trail
- Automatic expiry via daily cron
- Proof/notes field (form URL, email ID, document reference)

### 2. Data subject requests — DSR (`gdpr.request`)
- Pipeline for: access, portability, erasure, rectification, restriction, objection
- Auto-calculated 30-day SLA deadline (Art. 12)
- Kanban + list view with colour-coded urgency
- 60-day extension support
- DSR data export wizard (JSON or plain text) across contacts, CRM, sales, invoices
- Email notification to data subject on completion
- Activity alerts 5 days before deadline

### 3. Data breach notification (`gdpr.breach`)
- 72-hour countdown from discovery to DPA notification deadline (Art. 33)
- Severity levels, breach type, data categories, approx. individuals affected
- Checklist: DPA notified, individuals notified, case reference
- Cron alert every 2 hours when breach is open and approaching deadline
- Full audit trail on DPA notification action

### 4. Retention automation (`gdpr.retention.rule`)
- Rules per Odoo model + date field + retention period
- Actions: anonymise, archive, or delete
- Configurable domain filter to narrow scope
- Manually run or scheduled daily cron
- Field-level anonymisation (set to '[anonymised]')
- Legal justification field per rule

### 5. Audit trail (`gdpr.audit.log`)
- Immutable — write() and unlink() are blocked at model level
- IP address capture from HTTP request context
- Exportable as PDF (printable for regulators)
- Covers: consents, DSRs, breaches, retentions, data exports

### 6. Processing register — Art. 30 (`gdpr.processing.register`)
- Records all processing activities with: purpose, legal basis, data subjects,
  data categories, recipients, third country transfers, retention, security measures
- Special category data flag (Art. 9) with required legal basis
- Legitimate interest balancing test field
- PDF export formatted as a regulator-ready document
- Review frequency tracking and last reviewed date

### Partner integration
- GDPR smart buttons on contact form (consent count, open DSRs)
- GDPR tab with consent history inline
- `gdpr_do_not_contact` and `gdpr_erasure_requested` flags

## Access roles
| Role | Access |
|------|--------|
| Auditor | Read-only across all GDPR models |
| DPO / Manager | Full create/edit/read |
| Administrator | Manages retention rules and config |

## Installation
1. Copy `gdpr_toolkit` folder to your Odoo addons path
2. Restart Odoo
3. Apps → Update Apps List
4. Search "GDPR" → Install
5. Assign roles under Settings → Users → Groups

## Pricing
€149 on Odoo Apps Store (v17)
Port to v18 after first sales — versions sold separately.

## Roadmap
- Cookie consent banner integration (website module)
- DPA contact directory per EU country
- AI-assisted personal data field detection
- Supplier/processor DPA agreement tracking
