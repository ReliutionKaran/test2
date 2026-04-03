{
    'name': 'GDPR Compliance Toolkit',
    'version': '17.0.1.0.0',
    'category': 'Legal',
    'summary': 'Full GDPR compliance: consent, DSR, retention, breach, audit, Article 30',
    'description': """
GDPR Compliance Toolkit for EU Businesses
==========================================
A complete internal GDPR management system for DPOs and compliance teams.

Features:
- Consent management with channel, legal basis and timestamp per contact
- Data Subject Request (DSR) pipeline with 30-day SLA countdown
- Automated data retention rules with anonymisation/deletion cron
- 72-hour data breach notification timer and regulator log
- Tamper-evident audit trail exportable as PDF
- Article 30 processing register with PDF export
- DPO, Manager and Auditor access roles

This module covers the internal compliance obligations that regulators
actually check — not just the customer-facing data request form.
    """,
    'author': 'Your Company Name',
    'website': 'https://yourwebsite.com',
    'license': 'OPL-1',
    'price': 149.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'mail',
        'contacts',
        'web',
    ],
    'data': [
        'security/gdpr_security.xml',
        'security/ir.model.access.csv',
        'data/gdpr_cron.xml',
        'data/gdpr_mail_template.xml',
        'views/gdpr_consent_views.xml',
        'views/gdpr_request_views.xml',
        'views/gdpr_breach_views.xml',
        'views/gdpr_retention_views.xml',
        'views/gdpr_audit_views.xml',
        'views/gdpr_register_views.xml',
        'views/res_partner_views.xml',
        'views/gdpr_menu.xml',
        'wizard/gdpr_dsr_export_wizard_views.xml',
        'report/gdpr_audit_report.xml',
        'report/gdpr_register_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/banner.png'],
}
