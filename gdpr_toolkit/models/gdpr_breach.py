from odoo import models, fields, api, _
from datetime import timedelta


class GdprBreach(models.Model):
    _name = 'gdpr.breach'
    _description = 'GDPR Data Breach Notification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_discovered desc'

    name = fields.Char(
        'Reference', required=True, copy=False,
        readonly=True, default=lambda self: _('New'),
    )
    date_discovered = fields.Datetime(
        'Discovered on', required=True,
        default=fields.Datetime.now, tracking=True,
    )
    date_72h_deadline = fields.Datetime(
        '72-hour DPA deadline', compute='_compute_deadline', store=True,
    )
    hours_remaining = fields.Float(
        'Hours remaining', compute='_compute_hours_remaining',
    )
    deadline_breached = fields.Boolean(
        'Deadline passed', compute='_compute_hours_remaining', store=True,
    )

    state = fields.Selection([
        ('assessing', 'Assessing'),
        ('notifiable', 'Notifiable — DPA report required'),
        ('not_notifiable', 'Not notifiable'),
        ('dpa_notified', 'DPA notified'),
        ('closed', 'Closed'),
    ], default='assessing', string='Status', tracking=True, index=True)

    severity = fields.Selection([
        ('low', 'Low — minimal risk to individuals'),
        ('medium', 'Medium — possible harm to individuals'),
        ('high', 'High — significant harm likely'),
        ('critical', 'Critical — high risk, notify individuals too'),
    ], string='Severity', required=True, tracking=True)

    breach_type = fields.Selection([
        ('confidentiality', 'Confidentiality breach (unauthorised access/disclosure)'),
        ('integrity', 'Integrity breach (unauthorised alteration)'),
        ('availability', 'Availability breach (accidental loss/destruction)'),
        ('combined', 'Combined breach'),
    ], string='Breach type', required=True, tracking=True)

    data_categories = fields.Many2many(
        'gdpr.data.category', string='Categories of data affected',
    )
    approx_individuals = fields.Integer(
        'Approx. individuals affected', tracking=True,
    )
    approx_records = fields.Integer('Approx. records affected')

    description = fields.Text(
        'Description of the breach', required=True,
        help='Nature of the breach, what happened, how it was discovered',
    )
    likely_consequences = fields.Text('Likely consequences')
    measures_taken = fields.Text('Measures taken / proposed')

    controller_name = fields.Char('Data controller name')
    dpo_name = fields.Char('DPO / contact person')
    dpo_email = fields.Char('DPO email')

    dpa_reference = fields.Char('DPA case reference number')
    date_dpa_notified = fields.Datetime('DPA notified on', tracking=True)
    individuals_notified = fields.Boolean('Individuals notified', tracking=True)
    date_individuals_notified = fields.Datetime('Individuals notified on')

    internal_report = fields.Text('Internal investigation notes')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('gdpr.breach') or _('New')
        return super().create(vals_list)

    @api.depends('date_discovered')
    def _compute_deadline(self):
        for rec in self:
            if rec.date_discovered:
                rec.date_72h_deadline = rec.date_discovered + timedelta(hours=72)
            else:
                rec.date_72h_deadline = False

    @api.depends('date_72h_deadline', 'state')
    def _compute_hours_remaining(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.date_72h_deadline and rec.state not in ('dpa_notified', 'closed', 'not_notifiable'):
                delta = rec.date_72h_deadline - now
                total_hours = delta.total_seconds() / 3600
                rec.hours_remaining = round(total_hours, 1)
                rec.deadline_breached = total_hours < 0
            else:
                rec.hours_remaining = 0.0
                rec.deadline_breached = False

    def action_mark_notifiable(self):
        self.write({'state': 'notifiable'})
        self._schedule_dpa_alert()

    def action_mark_not_notifiable(self):
        self.write({'state': 'not_notifiable'})

    def action_dpa_notified(self):
        self.write({
            'state': 'dpa_notified',
            'date_dpa_notified': fields.Datetime.now(),
        })
        self.env['gdpr.audit.log'].create({
            'action': 'breach_dpa_notified',
            'model_name': self._name,
            'record_id': self.id,
            'description': f'DPA notification filed for breach {self.name}',
            'user_id': self.env.user.id,
        })

    def action_close(self):
        self.write({'state': 'closed'})

    def _schedule_dpa_alert(self):
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            date_deadline=self.date_72h_deadline.date() if self.date_72h_deadline else fields.Date.today(),
            summary=f'File DPA notification — {self.name} — 72h deadline',
            user_id=self.env.user.id,
        )

    @api.model
    def _cron_breach_deadline_alerts(self):
        now = fields.Datetime.now()
        warning_threshold = now + timedelta(hours=12)
        at_risk = self.search([
            ('state', 'in', ['assessing', 'notifiable']),
            ('date_72h_deadline', '<=', warning_threshold),
        ])
        for breach in at_risk:
            breach.message_post(
                body=f'WARNING: 72-hour DPA notification deadline approaching. Hours remaining: {breach.hours_remaining}',
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )


class GdprDataCategory(models.Model):
    _name = 'gdpr.data.category'
    _description = 'GDPR Data Category'
    _order = 'name'

    name = fields.Char('Category', required=True)
    is_special = fields.Boolean(
        'Special category (Art. 9)',
        help='Health, biometric, racial, political, religious, sexual orientation data',
    )
    description = fields.Text('Description')
