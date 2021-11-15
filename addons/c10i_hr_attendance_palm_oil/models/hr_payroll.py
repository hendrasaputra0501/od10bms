# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author1 Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   @author2 Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
from datetime import datetime
from odoo import models, fields, tools, exceptions, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT

class hr_attendance_payroll(models.Model):
    _inherit = 'hr.attendance.payroll'

    def _get_default_partner(self):
        partner = self.env['res.partner'].search([('name','ilike','Payroll')], limit=1)
        return partner and partner.id or False

    def _get_default_partner_bpjs_kes(self):
        partner = self.env['res.partner'].search([('name','ilike','BPJS Kesehatan')], limit=1)
        return partner and partner.id or False

    def _get_default_partner_bpjs_tk(self):
        partner = self.env['res.partner'].search([('name','ilike','BPJS Ketenagakerjaan')], limit=1)
        return partner and partner.id or False

    payroll_partner_id = fields.Many2one('res.partner', 'Partner Payroll', default=_get_default_partner, states={'done': [('readonly',True)]})
    bpjs_kes_partner_id = fields.Many2one('res.partner', 'Partner BPJS Kesehatan', default=_get_default_partner_bpjs_kes, states={'done': [('readonly',True)]})
    bpjs_tk_partner_id = fields.Many2one('res.partner', 'Partner BPJS Ketenagakerjaan', default=_get_default_partner_bpjs_tk, states={'done': [('readonly',True)]})
    invoice_ids = fields.Many2many('account.invoice', 'payroll_account_invoice_rel', 'payroll_id', 'invoice_id', string='Invoice AP')
    invoice_count = fields.Integer(compute="_compute_invoice", string='# of AP', copy=False, default=0)

    @api.depends('invoice_ids.state')
    def _compute_invoice(self):
        for payroll in self:
            payroll.invoice_count = len(payroll.invoice_ids.ids)

    @api.multi
    def action_draft(self):
        self.state = "draft"
        return True

    @api.multi
    def action_create_bill(self):
        self.ensure_one()
        # 1. Grouping Salary Expenses
        grouped_hke = {}
        grouped_hkne = {}
        grouped_overtime = {}
        grouped_natura = {}
        grouped_bpjs_kes = {}
        grouped_bpjs_kes_pot = {}
        grouped_bpjs_tk = {}
        grouped_bpjs_tk_pot = {}
        grouped_bpjs_pen = {}
        grouped_bpjs_pen_pot = {}
        default_type_none = self.env['account.location.type'].search(['|', ('name', '=', '-'), ('code', '=', '-')],limit=1)
        for line in self.line_ids:
            employee = line.employee_id
            if not (line.effective_work_days_value or line.natura_value or line.overtime_value or line.non_effective_work_days_value):
                continue
            # 0.0 Validasi data
            salary_ok = bpjs_kes_ok = bpjs_tk_ok = bpjs_pen_ok = True
            if employee.default_account_salary_id:
                salary_ok = True
            else:
                raise exceptions.ValidationError(_("Karyawan %s tidak memiliki Account Gaji.\n\
                        Silahkan diinput di Data Karyawan tersebut terlebih dahulu.")%employee.name)
            if line.potongan_bpjs_kes:
                if not employee.default_account_bpjs_allowance_id or not employee.inter_account_bpjs_allowance_id:
                    raise exceptions.ValidationError(_("Karyawan %s tidak memiliki Account Beban BPJS Kesehatan.\n\
                                            Silahkan diinput di Data Karyawan tersebut terlebih dahulu.") % employee.name)
                else:
                    bpjs_kes_ok = True

            if line.potongan_bpjs_tk:
                if not employee.default_account_ketenagakerjaan_allowance_id or not employee.inter_account_ketenagakerjaan_allowance_id:
                    raise exceptions.ValidationError(_("Karyawan %s tidak memiliki Account Beban BPJS Ketenagakerjaan.\n\
                                            Silahkan diinput di Data Karyawan tersebut terlebih dahulu.")%employee.name)
                else:
                    bpjs_tk_ok = True

            if line.potongan_bpjs_pensiun:
                if not employee.default_account_pensiun_allowance_id or not employee.inter_account_pensiun_allowance_id:
                    raise exceptions.ValidationError(_("Karyawan %s tidak memiliki Account Beban BPJS Pensiun.\n\
                                            Silahkan diinput di Data Karyawan tersebut terlebih dahulu.")%employee.name)
                else:
                    bpjs_pen_ok = True

            # 1.1 Grouped by Location are made for Basic Salary Expenses, Overtime Expenses, BPJS Kes and BPJS TK
            location_type = employee.default_location_type_id or (default_type_none or False)
            location = employee.default_location_id
            if location_type.id not in grouped_hke.keys() and salary_ok:
                grouped_hke.update({location_type.id: {}})
                grouped_hkne.update({location_type.id: {}})
                grouped_natura.update({location_type.id: {}})
                grouped_overtime.update({location_type.id: {}})
                if bpjs_kes_ok:
                    grouped_bpjs_tk.update({location_type.id: {}})
                if bpjs_tk_ok:
                    grouped_bpjs_kes.update({location_type.id: {}})
                if bpjs_pen_ok:
                    grouped_bpjs_pen.update({location_type.id: {}})
            if location.id not in grouped_hke[location_type.id].keys() and salary_ok:
                grouped_hke[location_type.id].update({location.id:{}})
                grouped_hkne[location_type.id].update({location.id: {}})
                grouped_natura[location_type.id].update({location.id: {}})
                grouped_overtime[location_type.id].update({location.id: {}})
                if bpjs_kes_ok:
                    grouped_bpjs_tk[location_type.id].update({location.id: {}})
                if bpjs_tk_ok:
                    grouped_bpjs_kes[location_type.id].update({location.id: {}})
                if bpjs_pen_ok:
                    grouped_bpjs_pen[location_type.id].update({location.id: {}})

            # 1.2 Grouped by Salary Account for Basic Salary Expenses
            salary_account = employee.default_account_salary_id
            if salary_account.id not in grouped_hke[location_type.id][location.id].keys() and salary_ok:
                grouped_hke[location_type.id][location.id].update({salary_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': salary_account.id,
                    'name': 'Beban Gaji Hari Kerja Efektif',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_hke[location_type.id][location.id][salary_account.id]['price_unit'] += (line.effective_work_days_value - line.penalty_value)
            if salary_account.id not in grouped_hkne[location_type.id][location.id].keys() and salary_ok:
                grouped_hkne[location_type.id][location.id].update({salary_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': salary_account.id,
                    'name': 'Beban Gaji Hari Kerja Non-efektif',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_hkne[location_type.id][location.id][salary_account.id]['price_unit'] += line.non_effective_work_days_value

            # 1.3 Grouped by Overtime Account for Overtime Expenses
            overtime_account = employee.default_account_overtime_id or salary_account
            if overtime_account.id not in grouped_overtime[location_type.id][location.id].keys() and salary_ok:
                grouped_overtime[location_type.id][location.id].update({overtime_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': overtime_account.id,
                    'name': 'Beban Overtime',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_overtime[location_type.id][location.id][overtime_account.id]['price_unit'] += line.overtime_value

            # 1.4 Grouped by Natura Account for Overtime Expenses
            natura_account = employee.default_account_welfare_allowance_id or salary_account
            if natura_account.id not in grouped_natura[location_type.id][location.id].keys() and salary_ok:
                grouped_natura[location_type.id][location.id].update({natura_account.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': natura_account.id,
                    'name': 'Beban Natura',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_natura[location_type.id][location.id][natura_account.id]['price_unit'] += line.natura_value

            # BEBAN BPJS KES
            account_bpjs_kes = employee.default_account_bpjs_allowance_id
            if account_bpjs_kes.id not in grouped_bpjs_kes[location_type.id][location.id].keys() and bpjs_kes_ok:
                grouped_bpjs_kes[location_type.id][location.id].update({account_bpjs_kes.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': account_bpjs_kes.id,
                    'name': 'Beban BPJS Kesehatan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_kes[location_type.id][location.id][account_bpjs_kes.id]['price_unit'] += line.tunjangan_bpjs_kes
            # POTONGAN GAJI KARYAWAN UNTUK BPJS KESEHATAN
            account_bpjs_kes_pot = employee.inter_account_bpjs_allowance_id
            if account_bpjs_kes_pot.id not in grouped_bpjs_kes_pot.keys() and bpjs_kes_ok:
                grouped_bpjs_kes_pot.update({account_bpjs_kes_pot.id: {
                    'account_location_type_id': default_type_none and default_type_none.id or False,
                    'account_location_id': False,
                    'account_id': account_bpjs_kes_pot.id,
                    'name': 'Potongan Gaji untuk BPJS Kesehatan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_kes_pot[account_bpjs_kes_pot.id]['price_unit'] += line.potongan_bpjs_kes

            # BEBAN BPJS KETENAGAKERJAAN
            account_bpjs_tk = employee.default_account_ketenagakerjaan_allowance_id
            if account_bpjs_tk.id not in grouped_bpjs_tk[location_type.id][location.id].keys() and bpjs_tk_ok:
                grouped_bpjs_tk[location_type.id][location.id].update({account_bpjs_tk.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': account_bpjs_tk.id,
                    'name': 'Beban BPJS Ketenagakerjaan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_tk[location_type.id][location.id][account_bpjs_tk.id]['price_unit'] += line.tunjangan_bpjs_tk
            # POTONGAN GAJI KARYAWAN UNTUK BPJS KETENAGAKERJAAN
            account_bpjs_tk_pot = employee.inter_account_ketenagakerjaan_allowance_id
            if account_bpjs_tk_pot.id not in grouped_bpjs_tk_pot.keys() and bpjs_tk_ok:
                grouped_bpjs_tk_pot.update({account_bpjs_tk_pot.id: {
                    'account_location_type_id': default_type_none and default_type_none.id or False,
                    'account_location_id': False,
                    'account_id': account_bpjs_tk_pot.id,
                    'name': 'Potongan Gaji untuk BPJS Ketenagakerjaan',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_tk_pot[account_bpjs_tk_pot.id]['price_unit'] += line.potongan_bpjs_tk

            # BEBAN BPJS PENSIUN
            account_bpjs_pen = employee.default_account_pensiun_allowance_id
            if account_bpjs_pen.id not in grouped_bpjs_pen[location_type.id][location.id].keys() and bpjs_pen_ok:
                grouped_bpjs_pen[location_type.id][location.id].update({account_bpjs_pen.id: {
                    'account_location_type_id': location_type.id,
                    'account_location_id': location.id,
                    'account_id': account_bpjs_pen.id,
                    'name': 'Beban BPJS Pensiun',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_pen[location_type.id][location.id][account_bpjs_pen.id]['price_unit'] += line.tunjangan_bpjs_pensiun
            # POTONGAN GAJI KARYAWAN UNTUK BPJS KETENAGAKERJAAN
            account_bpjs_pen_pot = employee.inter_account_pensiun_allowance_id
            if account_bpjs_pen_pot.id not in grouped_bpjs_pen_pot.keys() and bpjs_pen_ok:
                grouped_bpjs_pen_pot.update({account_bpjs_pen_pot.id: {
                    'account_location_type_id': default_type_none and default_type_none.id or False,
                    'account_location_id': False,
                    'account_id': account_bpjs_pen_pot.id,
                    'name': 'Potongan Gaji untuk BPJS Pensiun',
                    'price_unit': 0.0,
                    'quantity': 1.0,
                }})
            grouped_bpjs_pen_pot[account_bpjs_pen_pot.id]['price_unit'] += line.potongan_bpjs_pensiun

        # Create Invoice AP
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        invoice_ids = []
        default_journal = self.env['account.journal'].search([('type','=','general')], limit=1)
        # 1. Create Invoice AP for Salary
        invoice1 = AccountInvoice.create({
            'type': 'in_invoice',
            'date_invoice': self.date_stop,
            'partner_id': self.payroll_partner_id.id,
            'account_id': self.payroll_partner_id.property_account_payable_id.id,
            'journal_id': default_journal.id,
            'currency_id': self.company_id.currency_id.id,
            'company_id': self.company_id.id
        })
        # Salary and Overtime Expenses
        salary_lines = []
        for loctype in grouped_hke.values() + grouped_hkne.values():
            for loc in loctype.values():
                for x in loc.values():
                    salary_lines.append(x)
        for salary_expense in salary_lines:
            if not salary_expense['price_unit']:
                continue
            invoice_line_vals = salary_expense
            invoice_line_vals.update({'invoice_id': invoice1.id})
            AccountInvoiceLine.create(invoice_line_vals)
        overtime_lines = []
        for loctype in grouped_overtime.values():
            for loc in loctype.values():
                for x in loc.values():
                    overtime_lines.append(x)
        for overtime_expense in overtime_lines:
            if not overtime_expense['price_unit']:
                continue
            invoice_line_vals = overtime_expense
            invoice_line_vals.update({'invoice_id': invoice1.id})
            AccountInvoiceLine.create(invoice_line_vals)
        # Potongan Gaji
        for bpjs_kes_pot in grouped_bpjs_kes_pot.values():
            if not bpjs_kes_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_kes_pot
            invoice_line_vals.update({'invoice_id': invoice1.id, 'quantity': -1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        for bpjs_tk_pot in grouped_bpjs_tk_pot.values():
            if not bpjs_tk_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_tk_pot
            invoice_line_vals.update({'invoice_id': invoice1.id, 'quantity': -1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        for bpjs_tk_pen in grouped_bpjs_pen_pot.values():
            if not bpjs_tk_pen['price_unit']:
                continue
            invoice_line_vals = bpjs_tk_pen
            invoice_line_vals.update({'invoice_id': invoice1.id, 'quantity': -1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        invoice1.compute_taxes()
        invoice_ids.append(invoice1.id)

        # 2. Create Invoice AP for BPJS Kesehatan
        invoice2 = AccountInvoice.create({
            'type': 'in_invoice',
            'date_invoice': self.date_stop,
            'partner_id': self.bpjs_kes_partner_id.id,
            'account_id': self.bpjs_kes_partner_id.property_account_payable_id.id,
            'journal_id': default_journal.id,
            'currency_id': self.company_id.currency_id.id,
            'company_id': self.company_id.id
        })
        # BPJS Expenses
        bpjs_lines = []
        for loctype in grouped_bpjs_kes.values():
            for loc in loctype.values():
                for x in loc.values():
                    bpjs_lines.append(x)
        for bpjs_kes_expenses in bpjs_lines:
            if not bpjs_kes_expenses['price_unit']:
                continue
            invoice_line_vals = bpjs_kes_expenses
            invoice_line_vals.update({'invoice_id': invoice2.id})
            AccountInvoiceLine.create(invoice_line_vals)
        # Potongan Gaji
        for bpjs_kes_pot in grouped_bpjs_kes_pot.values():
            if not bpjs_kes_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_kes_pot
            invoice_line_vals.update({'invoice_id': invoice2.id, 'quantity': 1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        invoice2.compute_taxes()
        invoice_ids.append(invoice2.id)

        # 3. Create Invoice AP for BPJS Ketenagakerjaan
        invoice3 = AccountInvoice.create({
            'type': 'in_invoice',
            'date_invoice': self.date_stop,
            'partner_id': self.bpjs_tk_partner_id.id,
            'account_id': self.bpjs_tk_partner_id.property_account_payable_id.id,
            'journal_id': default_journal.id,
            'currency_id': self.company_id.currency_id.id,
            'company_id': self.company_id.id
        })
        # BPJS Expenses
        bpjs_lines2 = []
        for loctype in grouped_bpjs_tk.values():
            for loc in loctype.values():
                for x in loc.values():
                    bpjs_lines2.append(x)
        for bpjs_tk_expenses in bpjs_lines2:
            if not bpjs_tk_expenses['price_unit']:
                continue
            invoice_line_vals = bpjs_tk_expenses
            invoice_line_vals.update({'invoice_id': invoice3.id})
            AccountInvoiceLine.create(invoice_line_vals)
        bpjs_lines3 = []
        for loctype in grouped_bpjs_pen.values():
            for loc in loctype.values():
                for x in loc.values():
                    bpjs_lines3.append(x)
        for bpjs_pen_expenses in bpjs_lines3:
            if not bpjs_pen_expenses['price_unit']:
                continue
            invoice_line_vals = bpjs_pen_expenses
            invoice_line_vals.update({'invoice_id': invoice3.id})
            AccountInvoiceLine.create(invoice_line_vals)
        # Potongan Gaji
        for bpjs_tk_pot in grouped_bpjs_tk_pot.values():
            if not bpjs_tk_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_tk_pot
            invoice_line_vals.update({'invoice_id': invoice3.id, 'quantity': 1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        for bpjs_pen_pot in grouped_bpjs_pen_pot.values():
            if not bpjs_pen_pot['price_unit']:
                continue
            invoice_line_vals = bpjs_pen_pot
            invoice_line_vals.update({'invoice_id': invoice3.id, 'quantity': 1.0})
            AccountInvoiceLine.create(invoice_line_vals)
        invoice3.compute_taxes()
        invoice_ids.append(invoice3.id)

        self.invoice_ids = [(6,0,invoice_ids)]
        self.state='done'

        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        result['context'] = {'type': 'in_invoice', 'default_journal_id': default_journal.id}
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

    @api.multi
    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]

        # override the context to get rid of the default filtering
        result['context'] = {'type': 'in_invoice'}

        # choose the view_mode accordingly
        if len(self.invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        elif len(self.invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.invoice_ids.id
        return result

class hr_attendance_payroll_line(models.Model):
    _inherit = 'hr.attendance.payroll.line'

    amount_bpjs_kes = fields.Float("Nilai BPJS Kesehatan")
    potongan_bpjs_kes = fields.Float("Potongan BPJS Kesehatan")
    tunjangan_bpjs_kes = fields.Float("Tunjangan BPJS Kesehatan")
    amount_bpjs_tk = fields.Float("Nilai BPJS Ketenagakerjaan")
    potongan_bpjs_tk = fields.Float("Potongan BPJS Ketenagakerjaan")
    tunjangan_bpjs_tk = fields.Float("Tunjangan BPJS Ketenagakerjaan")
    amount_bpjs_pensiun = fields.Float("Nilai BPJS Pensiun")
    potongan_bpjs_pensiun = fields.Float("Potongan BPJS Pensiun")
    tunjangan_bpjs_pensiun = fields.Float("Tunjangan BPJS Pensiun")