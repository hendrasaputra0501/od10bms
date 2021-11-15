from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class BMUnit(models.Model):
    _name = 'bm.unit'
    _inherit = 'mail.thread'
    _description = 'Master data unit'

    company_id = fields.Many2one('res.company', string="Company",
        default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Unit Code', required=True,)
    tower_id = fields.Many2one('bm.tower', string="Tower")
    floor_id = fields.Many2one('bm.floor', string="Floor", domain="[('tower_id','=', tower_id)]")
    area = fields.Float(string="Area (m2)")

    electricity_factor = fields.Float(string="Electricity Meter Factor")
    electricity_load_voltage = fields.Float(string="Electricity Load Voltage (kVA)")
    electricity_saving_limit = fields.Float(string="Saving Limit")
    
    owner_ids = fields.One2many('bm.owner', 'unit_id', string="Owner")
    tenant_ids = fields.One2many('bm.unit.tenancy', 'unit_id', string="Tenant")
    service_charge_product_id = fields.Many2one('product.product', string="Service Charge", required=True,
        default=lambda self: self.env.user.company_id.service_charge_product_id)
    sinking_fund_product_id = fields.Many2one('product.product', string="Sinking Fund", required=True,
        default=lambda self: self.env.user.company_id.sinking_fund_product_id)
    electricity_cost_product_id = fields.Many2one('product.product', string="Electricity Charge", required=True,
        default=lambda self: self.env.user.company_id.electricity_cost_product_id)
    water_cost_product_id = fields.Many2one('product.product', string="Water Charge", required=True,
        default=lambda self: self.env.user.company_id.water_cost_product_id)

    # electricity_usage_ids = fields.One2many('bm.electricity.usage', 'unit_id', string='Electricity Usage')
    # water_usage_ids = fields.One2many('bm.water.usage', 'unit_id', string='Water Usage')

    # ----------------------------------------
    # Helpers
    # ----------------------------------------
    @api.model
    def get_current_tenant(self):
        self.ensure_one()
        context = self._context
        current_date = context.get('date', time.strftime(DF))
        tenants = False
        if self.tenant_ids:
            tenants = self.tenant_ids.filtered(lambda x: x.start_date<=current_date and (x.end_date==False or x.end_date>=current_date))

        if tenants:
            return sorted(tenants, key=lambda x: x.id, reverse=True)[0]
        else:
            return False

    @api.model
    def get_next_tuition_date(self):
        self.ensure_one()
        context = self._context
        
        current_tenant = self.get_current_tenant()
        if not current_tenant:
            raise ValidationError(_("Unit %s doesnt have current Tenant")%self.name)

        # get last payment
        res = {'service_charge': False, 'sinking_fund': False}
        # for Service Charge
        last_tuition = self.env['bm.tuition'].search([('unit_id','=',self.id),('product_id','=',self.service_charge_product_id.id)], order='date desc', limit=1)
        if last_tuition:
            res['service_charge'] = (datetime.strptime(last_tuition.date, DF) + \
                    relativedelta(months=current_tenant.tuition_method_period)).strftime(DF)
        else:
            tenant_start = datetime.strptime(current_tenant.start_date, DF)
            if tenant_start.day<current_tenant.tuition_schedule_date:
                res['service_charge'] = tenant_start.strftime("%Y-%m-"+str(current_tenant.tuition_schedule_date))
            else:
                res['service_charge'] = (tenant_start + \
                    relativedelta(months=1)).strftime("%Y-%m-"+ \
                    ("0%s"%str(current_tenant.tuition_schedule_date) if current_tenant.tuition_schedule_date<10 else str(current_tenant.tuition_schedule_date)))
        # for Sinking Fund
        last_tuition = self.env['bm.tuition'].search([('unit_id','=',self.id),('product_id','=',self.sinking_fund_product_id.id)], order='date desc', limit=1)
        if last_tuition:
            res['sinking_fund'] = (datetime.strptime(last_tuition.date, DF) + \
                    relativedelta(months=current_tenant.tuition_method_period)).strftime(DF)
        else:
            tenant_start = datetime.strptime(current_tenant.start_date, DF)
            if tenant_start.day<current_tenant.tuition_schedule_date:
                res['sinking_fund'] = tenant_start.strftime("%Y-%m-"+str(current_tenant.tuition_schedule_date))
            else:
                res['sinking_fund'] = (tenant_start + \
                    relativedelta(months=1)).strftime("%Y-%m-"+\
                    ("0%s"%str(current_tenant.tuition_schedule_date) if current_tenant.tuition_schedule_date<10 else str(current_tenant.tuition_schedule_date)))
        return res

    @api.multi
    def create_tuition(self):
        self.ensure_one()
        context = self.env.context
        current_tenant = self.get_current_tenant()
        new_service_charge = self.env['bm.tuition']
        new_sinking_fund = self.env['bm.tuition']

        check_date = context.get('force_date', time.strftime(DF))
        next_date = self.get_next_tuition_date()
        
        # Servic Charge Tuition
        service_charge_date = next_date['service_charge']
        while check_date > service_charge_date:
            rate = self.env['bm.tuition.rate'].with_context(date=service_charge_date, product_id=self.service_charge_product_id.id).get_rate()
            if not rate:
                raise ValidationError(_("Please input your Service Charge Rate."))
            service_charge_tuition = self.env['bm.tuition'].create({
                'unit_id': self.id,
                'product_id': self.service_charge_product_id.id,
                'date': service_charge_date,
                'amount': rate.rate * self.area,
                })
            new_service_charge |= service_charge_tuition
            service_charge_date = (datetime.strptime(service_charge_date, DF) + \
                    relativedelta(months=current_tenant.tuition_method_period)).strftime(DF)
        
        # Sinking Fund Tuition
        sinking_fund_date = next_date['sinking_fund']
        while check_date > sinking_fund_date:
            rate2 = self.env['bm.tuition.rate'].with_context(date=sinking_fund_date, product_id=self.sinking_fund_product_id.id).get_rate()
            if not rate2:
                raise ValidationError(_("Please input your Service Charge Rate."))
            sinking_fund_tuition = self.env['bm.tuition'].create({
                'unit_id': self.id,
                'product_id': self.sinking_fund_product_id.id,
                'date': sinking_fund_date,
                'amount': rate2.rate*self.area,
                })
            new_sinking_fund |= sinking_fund_tuition
            sinking_fund_date = (datetime.strptime(sinking_fund_date, DF) + \
                    relativedelta(months=current_tenant.tuition_method_period)).strftime(DF)
        return (new_service_charge, new_sinking_fund)