from odoo import models, fields, api


class GdprAuditLog(models.Model):
    _name = 'gdpr.audit.log'
    _description = 'GDPR Audit Trail'
    _order = 'date desc'
    _log_access = False

    date = fields.Datetime(
        'Date / time', required=True,
        default=fields.Datetime.now, index=True,
    )
    user_id = fields.Many2one(
        'res.users', string='User', required=True,
        ondelete='restrict',
    )
    action = fields.Selection([
        ('consent_created', 'Consent created'),
        ('consent_withdrawn', 'Consent withdrawn'),
        ('dsr_created', 'DSR created'),
        ('dsr_started', 'DSR started'),
        ('dsr_completed', 'DSR completed'),
        ('dsr_rejected', 'DSR rejected'),
        ('dsr_extended', 'DSR extended'),
        ('data_exported', 'Personal data exported'),
        ('data_accessed', 'Personal data accessed'),
        ('data_deleted', 'Data deleted'),
        ('breach_created', 'Breach reported'),
        ('breach_dpa_notified', 'DPA notified of breach'),
        ('retention_anonymise', 'Records anonymised'),
        ('retention_archive', 'Records archived'),
        ('retention_delete', 'Records deleted'),
        ('register_updated', 'Processing register updated'),
        ('other', 'Other'),
    ], string='Action', required=True, index=True)

    model_name = fields.Char('Model', index=True)
    record_id = fields.Integer('Record ID')
    description = fields.Text('Description', required=True)
    ip_address = fields.Char('IP address')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )

    def unlink(self):
        raise models.UserError(
            'Audit log records cannot be deleted. They must be retained for GDPR compliance.'
        )

    def write(self, vals):
        raise models.UserError(
            'Audit log records are immutable. They cannot be modified.'
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'user_id' not in vals:
                vals['user_id'] = self.env.user.id
            try:
                request = self.env['ir.http']._get_request()
                if request and hasattr(request, 'httprequest'):
                    vals.setdefault('ip_address', request.httprequest.environ.get('REMOTE_ADDR'))
            except Exception:
                pass
        return super().create(vals_list)
