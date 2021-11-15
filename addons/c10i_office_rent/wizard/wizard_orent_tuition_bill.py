from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT

import logging
_logger = logging.getLogger(__name__)

class TuitionBilling(models.TransientModel):
    _name = 'wizard.orent.tuition.bill'
    _description = 'Generate Tuition Bill'

    date_invoice = fields.Date("Invoice Date", required=True)
    filter_tuition_date = fields.Date("Filter Date", required=False)
    filter_unit_id = fields.Many2one('office.rent.unit', string='Filter Unit')
    # share_with_owner = fields.Boolean("Share with Owner (Prorata)")
    service_charge = fields.Boolean('for Service Charge')
    sinking_fund = fields.Boolean('for Sinking Fund')
    company_id = fields.Many2one('res.company', string='Company', index=True,
                    default=lambda self: self.env.user.company_id)
    state = fields.Selection([('draft','Draft'),('ready', 'Ready to Bill'),('invoiced','Invoiced')], string='Status', default='draft')
    line_ids = fields.One2many('orent.tuition.bill.line', 'wizard_id', string="Bills")

    # ----------------------------------------
    # Helpers
    # ----------------------------------------
    def prepare_invoice(self, partner):
        Invoice = self.env['account.invoice']
        journal_id = Invoice.with_context({'type': 'in_invoice'}).default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise ValidationError(_('Please define an accounting purchase journal for this company.'))
        account = partner.property_account_payable_id
        res = {
            'name': 'Tuition Bill',
            'type': 'in_invoice',
            'partner_id': partner.id,
            'account_id': account.id,
            'journal_id': 1,
            'date_invoice': self.date_invoice,
            'currency_id': self.company_id.currency_id.id,
            'company_id': self.company_id.id,
        }
        return res

    def prepare_invoice_line(self, line, invoice):
        product_account = line.product_id.product_tmpl_id.get_product_accounts()
        account = product_account.get('income')
        if not account:
            raise ValidationError(_('Please define Income Account for product %s.')%product.name)
        res = {
            'invoice_id': invoice.id,
            'product_id': line.product_id.id,
            'name': line.product_id.name + " for unit " + line.unit_id.name,
            'account_id': account.id,
            'quantity': 1.0,
            'uom_id': line.product_id.uom_id.id,
            'price_unit': line.amount,
            # 'invoice_line_tax_ids': [(6,0,[x.id for x in self.taxes_id])],
        }
        return res

    # ----------------------------------------
    # Actions
    # ----------------------------------------
    @api.multi
    def action_generate_lines(self):
        self.ensure_one()
        for x in self.line_ids:
            x.unlink()
        unit_domain = []
        if self.filter_unit_id:
            unit_domain.append(('id','=',self.filter_unit_id.id))
        for unit in self.env['office.rent.unit'].search(unit_domain):
            current_tenant = unit.get_current_tenant()
            if not current_tenant:
                raise ValidationError(_("Unit %s doesnt have current Tenant")%unit.name)

            new_service_charge_tuition, new_sinking_fund_tuition = self.env['bm.tuition'], self.env['bm.tuition']
            next_date = unit.get_next_tuition_date()
            if next_date > self.date_invoice:
                _logger.info('Unit %s already billed'%unit.name)
            else:
                new_service_charge_tuition, new_sinking_fund_tuition = unit.with_context(force_date=self.filter_tuition_date or self.date_invoice).create_tuition()
            
            if self.service_charge:    
                tuition_domain = [('unit_id','=',unit.id),('product_id','=',unit.service_charge_product_id.id),('invoice_state','=','open')]
                if self.filter_tuition_date:
                    tuition_domain.append(('date','<=',self.filter_tuition_date))
                tuitions_open1 = self.env['bm.tuition'].search(tuition_domain)
                for line1 in tuitions_open1:
                    print "-------------", line1
                    self.env['orent.tuition.bill.line'].create({
                        'wizard_id': self.id,
                        'unit_id': unit.id,
                        'tenant_id': current_tenant.id,
                        'tuition_id': line1.id,
                        'product_id': line1.product_id.id,
                        'partner_id': current_tenant.invoice_service_charge_partner_id.id,
                        'amount': line1.amount
                        })

            if self.sinking_fund:    
                tuition_domain2 = [('unit_id','=',unit.id),('product_id','=',unit.sinking_fund_product_id.id),('invoice_state','=','open')]
                if self.filter_tuition_date:
                    tuition_domain2.append(('date','<=',self.filter_tuition_date))
                tuitions_open2 = self.env['bm.tuition'].search(tuition_domain2)
                for line2 in tuitions_open2:
                    self.env['orent.tuition.bill.line'].create({
                        'wizard_id': self.id,
                        'unit_id': unit.id,
                        'tenant_id': current_tenant.id,
                        'tuition_id': line2.id,
                        'product_id': line2.product_id.id,
                        'partner_id': current_tenant.invoice_sinking_fund_partner_id.id,
                        'amount': line2.amount
                        })

        if not self.line_ids:
            raise UserError(_('There is nothing to pay.'))

        return self.write({'state': 'ready'})

    @api.multi
    def action_create_bill(self):
        self.ensure_one()
        if self.state=='draft':
            self.action_generate_lines()

        invoice_ids = []
        for partner in self.line_ids.mapped('partner_id'):
            invoice_vals = self.prepare_invoice(partner)
            invoice = self.env['account.invoice'].create(invoice_vals)
            tuition_to_update = self.env['bm.tuition']
            for line in self.line_ids.filtered(lambda x: x.partner_id.id==partner.id):
                invoice_line_vals = self.prepare_invoice_line(line, invoice)
                invoice_line = self.env['account.invoice.line'].create(invoice_line_vals)
                tuition_to_update |= line.tuition_id

            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post('This invoice has been created from Tuition Bill')
            invoice_ids.append(invoice.id)
            # Update all usage Invoice State
            if len(tuition_to_update.ids)>0:
                tuition_to_update.write({'invoice_id': invoice.id})

        self.write({'state': 'invoiced'})

        # Redirect to show Invoice
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        result['context'] = {'type': 'in_invoice'}
        # choose the view_mode accordingly
        if len(invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(invoice_ids) + ")]"
        elif len(invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = invoice_ids[0]
        else:
            return False
        return result

class TuitionBillingLines(models.TransientModel):
    _name = 'orent.tuition.bill.line'
    _description = 'Bill Lines'

    wizard_id = fields.Many2one('wizard.orent.tuition.bill', string="Wizard")
    unit_id = fields.Many2one('office.rent.unit', string="Unit")
    tenant_id = fields.Many2one('office.rent.unit.tenancy', string="Tenant")
    tuition_id = fields.Many2one('bm.tuition', string="Tuition")
    product_id = fields.Many2one('product.product', string="Product")
    partner_id = fields.Many2one('res.partner', string="Invoice to")
    amount = fields.Float(string="Amount")