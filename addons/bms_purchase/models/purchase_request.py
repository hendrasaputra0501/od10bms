# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Chaidar Aji Nugroho <chaidaraji@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    department_id = fields.Many2one('hr.department', string="Department", required=True)
    realisasi = fields.Selection([('local','Local'), ('ho', 'Head Office')], string="Realisasi")

    @api.model
    def create(self, vals):
        if vals.get('operating_unit_id', False):
            seq = self.env['ir.sequence'].with_context({'force_operating_unit':vals['operating_unit_id']})
        elif self._context.get('operating_unit_id',False):
            seq = self.env['ir.sequence'].with_context({'force_operating_unit': self._context.get('operating_unit_id')})
            vals.update({'operating_unit_id' : self._context.get('operating_unit_id')})
        else:
            seq = self.env['ir.sequence']
        
        department = self.env['hr.department'].browse(vals['department_id'])
        parent_department = department['parent_id']
        name = vals['name']=='New Document' and seq.next_by_code('seq.purchase.request') or vals['name']
        name_edit = name.split('/')
        no_seq = name_edit[0]
        month = name_edit[1]
        year = name_edit[2]
        vals['name'] = "%s/%s/%s-%s/%s/%s" % (str(no_seq),"PBJ", str(department.code),str(parent_department.code), str(month), str(year))
        request = super(PurchaseRequest, self).create(vals)
        if vals.get('approved_by'):
            request.message_subscribe_users(user_ids=[request.approved_by.id])
        return request

    @api.onchange('department_id')
    def onchange_department(self):
        if self.department_id:
            try:
                self.operating_unit_id = self.department_id.operating_unit_id and self.department_id.operating_unit_id.id or False
            except:
                self.operating_unit_id = False
                self.department_id = False

    @api.multi
    def button_rejected(self):
        residual = self.env['purchase.order.line'].sudo().search([('request_line_id', 'in', self.line_ids.ids),('state', 'in', ['purchase','done'])])
        if residual:
            raise ValidationError(_("Perhatian, Reject tidak dapat dilakukan karena PO berstatus Purchase/Done."))

        return self.write({
                            'state'         : 'rejected',
                            'approved_by'   : False,
                           })

class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    note = fields.Selection([('local', 'Lokal'),('pusat', 'Pusat')], string="Note")
    specifications = fields.Text(string='Penggunaan')
    qty_onhand = fields.Integer(string="Qty. On Hand")

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (self.product_id.code, name)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty    = 0.0
            self.name           = name
            self.qty_onhand = self.product_id.qty_available