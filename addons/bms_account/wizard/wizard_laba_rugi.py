# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import time
from odoo import api, fields, models, exceptions

class wizard_laba_rugi(models.TransientModel):
    _name           = "wizard.laba.rugi.report"
    _description    = "Laba Rugi Report"

    @api.model
    def get_default_penjualan(self):
        return self.env['account.account'].search([('code', 'in', [
            '41000001', 
            '41000003',
            '41000006',
        ])]).ids
    
    def get_default_beban_pokok_penjualan(self):
        return self.env['account.account'].search([('code', 'in', [
            '51000001',
            '51000002',
            '51000003',
            '51000004',
            '51700001',
            '51700002',
            '51700003',
            '51700004',
            '51900304',
            '51900305',
            '51900306',
            '51100002',
            '51100003',
            '51100005',
            '51110009',
            '51900001',
            '51900002',
            '51900003',
            '51900004',
            '51900005',
            '51900006',
            '51900007',
            '51900008',
            '51900009',
            '51900010',
            '51900101',
            '51900102',
            '51900201',
            '51900202',
            '51900203',
            '51900204',
            '51900205',
            '51900206',
            '51900301',
            '51900302',
            '51900303',
            '51900401',
            '51900501',
            '51900601',
            '51900602',
            '51900701',
            '51900801',
            '51900802',
        ])]).ids

    def get_default_beban_pemasaran(self):
        return self.env['account.account'].search([('code', 'in', [
            '53010001', 
            '53010002',
            '53010003',
            '53010005',
            '53010006',
            '53010007',
            '53010008',
            '53020001',
            '53020002',
            '53020003',
            '53021001',
            '53021003',
            '53021004',
            '53021005',
            '53021006',
        ])]).ids

    def get_default_beban_administrasi_umum(self):
        return self.env['account.account'].search([('code', 'in', [
            '53030001', 
            '53030002',
            '53040001',
            '53040002',
            '53040003',
            '53040004',
            '53040011',
            '53040101',
            '53050001',
            '53050002',
            '53050003',
            '53050004',
            '53050005',
            '53050006',
            '53050007',
            '53050101',
            '53060001',
            '53070001',
            '53070002',
            '53070003',
            '53070004',
            '53070101',
            '53080001',
            '53080101',
            '53090001',
            '53090002',
            '53090003',
            '53090004',
            '53090101',
            '53100001',
            '53100002',
            '53100007',
            '53100008',
            '53100009',
            '53100010',
            '53100011',
            '53100101',
            '53110001',
            '53110101',
            '53120001',
            '53120002',
            '53120003',
            '53120004',
            '53120005',
            '53120006',
            '53120007',
            '53120008',
            '53120009',
            '53130001',
            '53140001',
            '53160001',
            '53170001',
            '53170002',
            '53170003',
            '53170004',
            '53170005',
            '53170101',
            '53180001',
            '53180002',
            '53180003',
            '53180004',
            '53180005',
            '55010005',
        ])]).ids

    def get_default_pendapatan_lain_lain(self):
        return self.env['account.account'].search([('code', 'in', [
            '41000007', 
            '61100001',
            '61100002',
            '61100101',
            '61200001',
            '61200002',
            '61200101',
        ])]).ids

    def get_default_beban_lain_lain(self):
        return self.env['account.account'].search([('code', 'in', [
            '65100001', 
            '65100002',
            '65100003',
            '65100004',
            '65100005',
            '65100006',
            '65100007',
            '65100101',
            '65100102',
            '65100103',
            '65100104',
            '65100105',
            '65100109',
            '65100108',
            '65100106',
        ])]).ids

    date_start = fields.Date("Start Date", default=lambda *a: time.strftime('%Y-01-01'))
    date_end = fields.Date("End Date", default=lambda *a: time.strftime('%Y-%m-%d'))
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account')
    )

    report_type = fields.Selection([('xlsx', 'Xlsx'),('qweb-pdf','PDF')], string='Report Type', default='xlsx')
    
    account_id_penjualan = fields.Many2many(
        'account.account',
        string='Ref. Penjualan',
        required=True,
        default=get_default_penjualan
    )

    account_id_beban_pokok_penjualan = fields.Many2many(
        'account.account',
        string='Ref. Beban Pokok Penjualan',
        required=True,
        default=get_default_beban_pokok_penjualan
    )

    account_id_beban_pemasaran = fields.Many2many(
        'account.account',
        string='Ref. Beban Pemasaran',
        required=True,
        default=get_default_beban_pemasaran
    )

    account_id_beban_administrasi_umum = fields.Many2many(
        'account.account',
        string='Ref. Beban Administrasi dan Umum',
        required=True,
        default=get_default_beban_administrasi_umum
    )

    account_id_pendapatan_lain_lain = fields.Many2many(
        'account.account',
        string='Ref. Pendapatan Lain Lain',
        required=True,
        default=get_default_pendapatan_lain_lain
    )

    account_id_beban_lain_lain = fields.Many2many(
        'account.account',
        string='Ref. Beban Lain Lain',
        required=True,
        default=get_default_beban_lain_lain
    )

    @api.onchange('date_start','date_end')
    def onchange_date(self):
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise exceptions.ValidationError('Warning, End Date must greater than Start Date !!!')

    @api.multi
    def print_report(self):
        name = 'report_laba_rugi_xlsx' if str(self.report_type) == 'xlsx' else 'report_laba_rugi_pdf'
        res = self.env['report'].get_action(self, name)
        return res

wizard_laba_rugi()


