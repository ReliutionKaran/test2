from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class GdprRequest(models.Model):
    _name = 'gdpr.request'
    _description = 'GDPR Data Subject Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_received desc'

    name = fields.Char(
        'Reference', required=True, copy=False,
        readonly=True, default=lambda self: _('New'),
    )
    partner_id = fields.Many2one(
        'res.partner', string='Data subject', required=True,
        tracking=True,
    )
    request_type = fields.Selection([
        ('access', 'Right of access (Art. 15)'),
        ('portability', 'Data portability (Art. 20)'),
        ('erasure', 'Right to erasure (Art. 17)'),
        ('rectification', 'Right to rectification (Art. 16)'),
        ('restriction', 'Restriction of processing (Art. 18)'),
        ('objection', 'Right to object (Art. 21)'),
    ], string='Request type', required=True, tracking=True)

    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In progress'),
        ('awaiting_id', 'Awaiting ID verification'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('extended', 'Extended (60 days)'),
    ], default='new', string='Status', tracking=True, index=True)

    date_received = fields.Date(
        'Received on', required=True, default=fields.Date.today, tracking=True,
    )
    date_deadline = fields.Date(
        'Deadline (30 days)', compute='_compute_deadline', store=True,
    )
    date_extended_deadline = fields.Date('Extended deadline (60 days)')
    date_completed = fields.Date('Completed on', tracking=True)

    days_remaining = fields.Integer(
        'Days remaining', compute='_compute_days_remaining',
    )
    is_overdue = fields.Boolean(
        'Overdue', compute='_compute_days_remaining', store=True,
    )

    assigned_to = fields.Many2one(
        'res.users', 'Assigned to',
        default=lambda self: self.env.user, tracking=True,
    )
    channel = fields.Selection([
        ('email', 'Email'), ('post', 'Post'),
        ('phone', 'Phone'), ('portal', 'Website portal'),
        ('in_person', 'In person'),
    ], string='Received via', tracking=True)

    identity_verified = fields.Boolean('Identity verified', tracking=True)
    identity_method = fields.Char('Verification method')

    description = fields.Text('Request details')
    response_notes = fields.Text('Response / action taken')
    rejection_reason = fields.Text('Rejection reason')

    export_file = fields.Binary('Data export file')
    export_filename = fields.Char('Export filename')

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('gdpr.request') or _('New')
        return super().create(vals_list)

    @api.depends('date_received')
    def _compute_deadline(self):
        for rec in self:
            if rec.date_received:
                rec.date_deadline = rec.date_received + timedelta(days=30)
            else:
                rec.date_deadline = False

    @api.depends('date_deadline', 'state')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_deadline and rec.state not in ('completed', 'rejected'):
                delta = (rec.date_deadline - today).days
                rec.days_remaining = delta
                rec.is_overdue = delta < 0
            else:
                rec.days_remaining = 0
                rec.is_overdue = False

    def action_start(self):
        self.write({'state': 'in_progress'})
        self._log_gdpr_audit('dsr_started', f'DSR {self.name} moved to in progress')

    def action_complete(self):
        self.write({'state': 'completed', 'date_completed': fields.Date.today()})
        self._log_gdpr_audit('dsr_completed', f'DSR {self.name} completed')
        template = self.env.ref('gdpr_toolkit.mail_template_dsr_completed', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=False)

    def action_reject(self):
        if not self.rejection_reason:
            raise UserError('Please provide a rejection reason before rejecting.')
        self.write({'state': 'rejected'})
        self._log_gdpr_audit('dsr_rejected', f'DSR {self.name} rejected: {self.rejection_reason}')

    def action_extend(self):
        self.write({
            'state': 'extended',
            'date_extended_deadline': fields.Date.today() + timedelta(days=60),
        })
        self._log_gdpr_audit('dsr_extended', f'DSR {self.name} extended by 60 days')

    def _log_gdpr_audit(self, action, description):
        self.env['gdpr.audit.log'].create({
            'action': action,
            'model_name': self._name,
            'record_id': self.id,
            'description': description,
            'user_id': self.env.user.id,
        })

    @api.model
    def _cron_dsr_sla_alerts(self):
        today = fields.Date.today()
        warning_date = today + timedelta(days=5)
        at_risk = self.search([
            ('state', 'in', ['new', 'in_progress', 'awaiting_id']),
            ('date_deadline', '<=', warning_date),
        ])
        for req in at_risk:
            req.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=req.date_deadline,
                summary=f'DSR deadline in {req.days_remaining} days — {req.name}',
                user_id=req.assigned_to.id or self.env.user.id,
            )
