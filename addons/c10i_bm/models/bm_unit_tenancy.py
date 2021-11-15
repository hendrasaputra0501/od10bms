from odoo import models, fields, api

class BMUnitTenancy(models.Model):
    _name = 'bm.unit.tenancy'
    _inherit = 'mail.thread'
    _description = 'Master data unit tenancy'

    company_id = fields.Many2one('res.company', string="Company", required=True,
        default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one('res.partner',string="Partner", required=True,)
    tenant_code = fields.Char(string="Tenant code", required=True,)
    unit_id = fields.Many2one('bm.unit', string='Unit', required=True,)
    tenancy_type = fields.Selection([('owner', 'Owner'), ('rent', 'Rent')], default='owner', required=True,)
    start_date = fields.Date(string='Start date', required=True,)
    end_date = fields.Date(string='End date')
    
    invoice_service_charge_partner_id = fields.Many2one('res.partner', string="Invoice service charge", required=True,)
    invoice_sinking_fund_partner_id = fields.Many2one('res.partner', string="Invoice sinking fund", required=True,)
    invoice_utility_partner_id = fields.Many2one('res.partner', string="Invoice utility partner", required=True,)
    tuition_method_period = fields.Selection([(1,"1 Month"),
            (2,"2 months"),
            (3,"3 months"),
            (4,"4 months"),
            (6,"6 months"),
            (12,"1 year")], string="Period of Tuition Payment", default=1, required=True,
            help="Please input Billing Period for this Units Bills to be generated")
    tuition_schedule_date = fields.Integer(string="Schedule Date of Tuition Payment", 
        default=lambda self: self.env.user.company_id.tuition_schedule_date, required=True,
        help="Please put Schedule Date for this Units Bills to be generated")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:        
            self.invoice_service_charge_partner_id = self.partner_id
            self.invoice_sinking_fund_partner_id = self.partner_id
            self.invoice_utility_partner_id = self.partner_id
        else:
            self.invoice_service_charge_partner_id = False
            self.invoice_sinking_fund_partner_id = False
            self.invoice_utility_partner_id = False