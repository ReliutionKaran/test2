from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gdpr_consent_ids = fields.One2many(
        'gdpr.consent', 'partner_id', string='Consent records',
    )
    gdpr_request_ids = fields.One2many(
        'gdpr.request', 'partner_id', string='DSR requests',
    )
    gdpr_consent_count = fields.Integer(
        'Active consents', compute='_compute_gdpr_counts',
    )
    gdpr_request_count = fields.Integer(
        'Open DSRs', compute='_compute_gdpr_counts',
    )
    gdpr_do_not_contact = fields.Boolean(
        'Do not contact (GDPR)',
        help='Set automatically when all marketing consents are withdrawn',
        tracking=True,
    )
    gdpr_erasure_requested = fields.Boolean(
        'Erasure requested', tracking=True,
    )

    @api.depends('gdpr_consent_ids.state', 'gdpr_request_ids.state')
    def _compute_gdpr_counts(self):
        for partner in self:
            partner.gdpr_consent_count = len(
                partner.gdpr_consent_ids.filtered(lambda c: c.state == 'active')
            )
            partner.gdpr_request_count = len(
                partner.gdpr_request_ids.filtered(
                    lambda r: r.state not in ('completed', 'rejected')
                )
            )

    def action_view_gdpr_consents(self):
        return {
            'name': 'GDPR Consents',
            'type': 'ir.actions.act_window',
            'res_model': 'gdpr.consent',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_gdpr_requests(self):
        return {
            'name': 'DSR Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'gdpr.request',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
