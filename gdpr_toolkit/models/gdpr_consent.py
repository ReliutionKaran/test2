from odoo import models, fields, api
from odoo.exceptions import UserError


class GdprConsent(models.Model):
    _name = 'gdpr.consent'
    _description = 'GDPR Consent Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_consent desc'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner', string='Contact', required=True,
        ondelete='cascade', index=True, tracking=True,
    )
    purpose = fields.Selection([
        ('marketing_email', 'Marketing emails'),
        ('marketing_sms', 'Marketing SMS'),
        ('profiling', 'Profiling / personalisation'),
        ('data_sharing', 'Third-party data sharing'),
        ('newsletter', 'Newsletter'),
        ('legitimate_interest', 'Legitimate interest'),
        ('other', 'Other'),
    ], string='Purpose', required=True, tracking=True)
    purpose_other = fields.Char('Purpose details')

    legal_basis = fields.Selection([
        ('consent', 'Explicit consent (Art. 6.1.a)'),
        ('contract', 'Performance of contract (Art. 6.1.b)'),
        ('legal_obligation', 'Legal obligation (Art. 6.1.c)'),
        ('vital_interests', 'Vital interests (Art. 6.1.d)'),
        ('public_task', 'Public task (Art. 6.1.e)'),
        ('legitimate_interest', 'Legitimate interests (Art. 6.1.f)'),
    ], string='Legal basis', required=True, default='consent', tracking=True)

    channel = fields.Selection([
        ('web_form', 'Website form'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('paper', 'Paper / physical form'),
        ('in_app', 'In-app'),
        ('import', 'Data import'),
    ], string='Collection channel', required=True, tracking=True)

    state = fields.Selection([
        ('active', 'Active'),
        ('withdrawn', 'Withdrawn'),
        ('expired', 'Expired'),
    ], string='Status', default='active', tracking=True, index=True)

    date_consent = fields.Datetime(
        'Consent date', required=True,
        default=fields.Datetime.now, tracking=True,
    )
    date_withdrawn = fields.Datetime('Withdrawn on', tracking=True)
    date_expiry = fields.Date('Expires on', tracking=True)
    withdrawn_by = fields.Many2one('res.users', 'Withdrawn by', tracking=True)

    proof = fields.Text(
        'Proof / notes',
        help='URL of the form, email ID, or reference to physical document',
    )
    ip_address = fields.Char('IP address at consent')
    version = fields.Char(
        'Consent version',
        help='Version of the privacy policy shown at time of consent',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    def action_withdraw(self):
        for rec in self:
            if rec.state == 'withdrawn':
                raise UserError('This consent is already withdrawn.')
            rec.write({
                'state': 'withdrawn',
                'date_withdrawn': fields.Datetime.now(),
                'withdrawn_by': self.env.user.id,
            })
            rec._log_gdpr_audit('consent_withdrawn',
                                f'Consent withdrawn for {rec.purpose} by {self.env.user.name}')

    def _log_gdpr_audit(self, action, description):
        self.env['gdpr.audit.log'].create({
            'action': action,
            'model_name': self._name,
            'record_id': self.id,
            'description': description,
            'user_id': self.env.user.id,
        })

    @api.model
    def _cron_expire_consents(self):
        today = fields.Date.today()
        expired = self.search([
            ('state', '=', 'active'),
            ('date_expiry', '!=', False),
            ('date_expiry', '<', today),
        ])
        expired.write({'state': 'expired'})
