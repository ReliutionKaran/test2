from odoo import models, fields, api, _
import json
import base64
from datetime import date, datetime


class GdprDsrExportWizard(models.TransientModel):
    _name = 'gdpr.dsr.export.wizard'
    _description = 'GDPR DSR Data Export Wizard'

    request_id = fields.Many2one('gdpr.request', string='DSR request', required=True)
    partner_id = fields.Many2one(related='request_id.partner_id', readonly=True)
    include_contacts = fields.Boolean('Contact data', default=True)
    include_crm = fields.Boolean('CRM / leads', default=True)
    include_sales = fields.Boolean('Sales orders', default=True)
    include_invoices = fields.Boolean('Invoices', default=True)
    include_helpdesk = fields.Boolean('Helpdesk tickets', default=False)

    export_format = fields.Selection([
        ('json', 'JSON (machine-readable)'),
        ('txt', 'Plain text (human-readable)'),
    ], string='Export format', default='json', required=True)

    def action_export(self):
        self.ensure_one()
        partner = self.partner_id
        data = {'export_date': datetime.now().isoformat(), 'data_subject': {}}

        if self.include_contacts:
            data['data_subject'] = {
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'street': partner.street,
                'city': partner.city,
                'country': partner.country_id.name if partner.country_id else '',
                'company': partner.company_name,
                'vat': partner.vat,
            }

        if self.include_crm and 'crm.lead' in self.env:
            leads = self.env['crm.lead'].search([('partner_id', '=', partner.id)])
            data['crm_leads'] = [{
                'name': l.name,
                'stage': l.stage_id.name if l.stage_id else '',
                'date_deadline': l.date_deadline.isoformat() if l.date_deadline else None,
                'description': l.description or '',
            } for l in leads]

        if self.include_sales and 'sale.order' in self.env:
            orders = self.env['sale.order'].search([('partner_id', '=', partner.id)])
            data['sale_orders'] = [{
                'name': o.name,
                'date_order': o.date_order.isoformat() if o.date_order else None,
                'amount_total': o.amount_total,
                'state': o.state,
            } for o in orders]

        if self.include_invoices and 'account.move' in self.env:
            invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
            ])
            data['invoices'] = [{
                'name': inv.name,
                'date': inv.invoice_date.isoformat() if inv.invoice_date else None,
                'amount_total': inv.amount_total,
                'state': inv.payment_state,
            } for inv in invoices]

        if self.export_format == 'json':
            content = json.dumps(data, indent=2, default=str)
            filename = f'gdpr_export_{partner.name}_{date.today()}.json'
            mimetype = 'application/json'
        else:
            lines = [f'GDPR DATA EXPORT — {partner.name}', f'Generated: {date.today()}', '=' * 60, '']
            for section, value in data.items():
                if isinstance(value, dict):
                    lines.append(f'\n{section.upper()}')
                    for k, v in value.items():
                        lines.append(f'  {k}: {v}')
                elif isinstance(value, list):
                    lines.append(f'\n{section.upper()} ({len(value)} records)')
                    for item in value:
                        lines.append('  ---')
                        for k, v in item.items():
                            lines.append(f'  {k}: {v}')
            content = '\n'.join(lines)
            filename = f'gdpr_export_{partner.name}_{date.today()}.txt'
            mimetype = 'text/plain'

        file_data = base64.b64encode(content.encode('utf-8'))
        self.request_id.write({
            'export_file': file_data,
            'export_filename': filename,
        })

        self.env['gdpr.audit.log'].create({
            'action': 'data_exported',
            'model_name': 'res.partner',
            'record_id': partner.id,
            'description': f'Personal data exported for {partner.name} — DSR {self.request_id.name}',
            'user_id': self.env.user.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gdpr.request',
            'res_id': self.request_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
