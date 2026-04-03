from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class GdprRetentionRule(models.Model):
    _name = 'gdpr.retention.rule'
    _description = 'GDPR Data Retention Rule'
    _inherit = ['mail.thread']
    _order = 'model_id, name'

    name = fields.Char('Rule name', required=True)
    active = fields.Boolean('Active', default=True, tracking=True)

    model_id = fields.Many2one(
        'ir.model', string='Odoo model', required=True,
        domain=[('transient', '=', False)],
        help='The model whose records this rule applies to',
    )
    model_name = fields.Char(related='model_id.model', store=True)

    domain = fields.Char(
        'Filter domain', default='[]',
        help='Additional domain to narrow which records are targeted',
    )
    date_field = fields.Many2one(
        'ir.model.fields', string='Date field',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]",
        help='The date field used to calculate record age',
    )
    retention_days = fields.Integer(
        'Retain for (days)', required=True,
        help='Records older than this many days will be processed',
    )

    action = fields.Selection([
        ('anonymise', 'Anonymise personal fields'),
        ('archive', 'Archive record'),
        ('delete', 'Delete record'),
    ], string='Action', required=True, default='anonymise', tracking=True)

    fields_to_anonymise = fields.Many2many(
        'ir.model.fields', string='Fields to anonymise',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['char', 'text', 'html', 'email', 'phone', 'date', 'datetime'])]",
        help='Leave blank to anonymise all personal fields automatically',
    )

    last_run = fields.Datetime('Last executed', readonly=True)
    records_processed = fields.Integer('Records processed (last run)', readonly=True)

    legal_basis = fields.Text(
        'Legal justification',
        help='Document why this retention period is appropriate',
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    def action_run_now(self):
        self.ensure_one()
        count = self._execute_rule()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Retention rule executed',
                'message': f'{count} records processed.',
                'type': 'success',
            },
        }

    def _execute_rule(self):
        self.ensure_one()
        if not self.model_id or not self.date_field or not self.retention_days:
            return 0

        from datetime import timedelta
        cutoff = fields.Datetime.now() - timedelta(days=self.retention_days)
        date_field_name = self.date_field.name

        try:
            domain = eval(self.domain or '[]')
        except Exception:
            domain = []

        domain += [(date_field_name, '<', cutoff)]

        Model = self.env[self.model_name]
        records = Model.search(domain)
        count = len(records)

        if self.action == 'anonymise':
            self._anonymise_records(records)
        elif self.action == 'archive':
            records.write({'active': False})
        elif self.action == 'delete':
            records.unlink()

        self.write({
            'last_run': fields.Datetime.now(),
            'records_processed': count,
        })

        self.env['gdpr.audit.log'].create({
            'action': f'retention_{self.action}',
            'model_name': self.model_name,
            'record_id': self.id,
            'description': f'Retention rule "{self.name}": {count} records {self.action}d',
            'user_id': self.env.user.id,
        })

        _logger.info('GDPR retention rule "%s": %d records %sd', self.name, count, self.action)
        return count

    def _anonymise_records(self, records):
        if not records:
            return
        anonymise_fields = self.fields_to_anonymise
        if not anonymise_fields:
            field_names = [
                f.name for f in self.env['ir.model.fields'].search([
                    ('model_id', '=', self.model_id.id),
                    ('ttype', 'in', ['char', 'text', 'email', 'phone']),
                ])
            ]
        else:
            field_names = anonymise_fields.mapped('name')

        vals = {f: '[anonymised]' for f in field_names if f in records._fields}
        if vals:
            records.write(vals)

    @api.model
    def _cron_run_all_retention_rules(self):
        rules = self.search([('active', '=', True)])
        for rule in rules:
            try:
                rule._execute_rule()
            except Exception as e:
                _logger.error('GDPR retention rule "%s" failed: %s', rule.name, str(e))
