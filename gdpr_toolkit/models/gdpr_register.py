from odoo import models, fields


class GdprProcessingRegister(models.Model):
    _name = 'gdpr.processing.register'
    _description = 'GDPR Article 30 Processing Register'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char('Processing activity', required=True, tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('discontinued', 'Discontinued'),
    ], default='draft', string='Status', tracking=True)

    purpose = fields.Text('Purpose of processing', required=True, tracking=True)
    legal_basis = fields.Selection([
        ('consent', 'Consent (Art. 6.1.a)'),
        ('contract', 'Contract (Art. 6.1.b)'),
        ('legal_obligation', 'Legal obligation (Art. 6.1.c)'),
        ('vital_interests', 'Vital interests (Art. 6.1.d)'),
        ('public_task', 'Public task (Art. 6.1.e)'),
        ('legitimate_interest', 'Legitimate interests (Art. 6.1.f)'),
    ], string='Legal basis', required=True, tracking=True)
    legitimate_interest_detail = fields.Text(
        'Legitimate interest detail',
        help='Required if legal basis is legitimate interest',
    )

    data_categories = fields.Many2many(
        'gdpr.data.category', string='Categories of personal data',
    )
    data_subjects = fields.Char(
        'Categories of data subjects',
        help='e.g. customers, employees, website visitors, job applicants',
    )
    special_category = fields.Boolean('Includes special category data (Art. 9)')
    special_category_basis = fields.Text(
        'Special category legal basis',
        help='Required if special category data is processed',
    )

    recipients = fields.Text(
        'Recipients / categories of recipients',
        help='Who the data is shared with, including processors',
    )
    third_country_transfers = fields.Boolean('Transfers to third countries')
    third_country_detail = fields.Text(
        'Third country transfer safeguards',
        help='e.g. Standard Contractual Clauses, Adequacy Decision',
    )

    retention_period = fields.Char('Retention period', tracking=True)
    retention_justification = fields.Text('Retention justification')

    security_measures = fields.Text(
        'Technical & organisational security measures',
        help='e.g. encryption, access controls, pseudonymisation',
    )

    controller_name = fields.Char('Data controller')
    processor_names = fields.Text('Data processors (if any)')
    dpo_name = fields.Char('DPO name')
    dpo_contact = fields.Char('DPO contact details')

    system_location = fields.Char(
        'System / location',
        help='Which Odoo module or external system holds this data',
    )
    date_created = fields.Date('Record created', default=fields.Date.today)
    date_last_reviewed = fields.Date('Last reviewed', tracking=True)
    review_frequency = fields.Selection([
        ('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
        ('biannual', 'Every 6 months'), ('annual', 'Annual'),
    ], string='Review frequency', default='annual')

    notes = fields.Text('Additional notes')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    def action_activate(self):
        self.write({'state': 'active'})
        self.env['gdpr.audit.log'].create({
            'action': 'register_updated',
            'model_name': self._name,
            'record_id': self.id,
            'description': f'Processing activity "{self.name}" activated',
            'user_id': self.env.user.id,
        })

    def action_discontinue(self):
        self.write({'state': 'discontinued', 'active': False})
