# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import time
from odoo import api, fields, models, exceptions

class wizard_neraca(models.TransientModel):
    _name           = "wizard.neraca.report"
    _description    = "Neraca Report"


    @api.model
    def _default_account_id_kas(self):
        return '11199999'
    
    def _default_account_id_bank(self):
        return '11289999'
    
    def _default_account_id_piutang(self):
        return '11310000'
        
    def _default_account_id_inventory(self):
        return '11508999'
        
    def _default_account_id_pbd(self):
        return '11507999'
        
    def _default_account_id_pdd(self):
        return '11520000'
        
    def _default_account_id_um(self):
        return '11600099'

    def _default_account_id_asset(self):
        return '15110000'
    
    def _default_account_id_akp(self):
        return '15599999'
        
    def _default_account_id_atll(self):
        return '17999999'
        
    def _default_account_id_hd(self):
        return '21100000'
        
    def _default_account_id_hp(self):
        return '21200100'
        
    def _default_account_id_hps(self):
        return '23100002'
        
    def _default_account_id_sgujp(self):
        return '23101001'
        
    def _default_account_id_hki(self):
        return '23200001'
        
    def _default_account_id_hkoj(self):
        return '23300001'
        
    def _default_account_id_hbj(self):
        return '23100001'
        
    def _default_account_id_hko(self):
        return '23300099'
        
    def _default_account_id_myd(self):
        return '31000001'
        
    def _default_account_id_sldt(self):
        return '32000001'
        
    def _default_account_id_pmd(self):
        return '32000002'
        
    def _default_account_id_slblj(self):
        return '33000001'
    
    def _default_account_id_sbbi(self):
        return '34000999'

    
    date_start      = fields.Date("Start Date", default=lambda *a: time.strftime('%Y-01-01'))
    date_end       = fields.Date("End Date", default=lambda *a: time.strftime('%Y-%m-%d'))
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account'))
    report_type = fields.Selection([('xlsx', 'Xlsx'),('qweb-pdf','PDF')], string='Report Type', default='xlsx')
    account_id_kas = fields.Char(string='Ref. Kas', default=_default_account_id_kas)
    account_id_bank = fields.Char(string='Ref. Bank', default=_default_account_id_bank)
    account_id_piutang = fields.Char(string='Ref. Piutang', default=_default_account_id_piutang)
    account_id_inventory = fields.Char(string='Ref. Inventory', default=_default_account_id_inventory)
    account_id_pbd = fields.Char(string='Ref. Persediaan Barang Dagang', default=_default_account_id_pbd)
    account_id_pdd = fields.Char(string='Ref. Pajak dibayar dimuka', default=_default_account_id_pdd)
    account_id_um = fields.Char(string='Ref. Uang Muka', default=_default_account_id_um)
    
    account_id_asset = fields.Char(string='Ref. Asset', default=_default_account_id_asset)
    account_id_akp = fields.Char(string='Ref. Akumulasi Penyusutan', default=_default_account_id_akp)
    
    account_id_atll = fields.Char(string='Ref. Aktiva Lancar Lainnya', default=_default_account_id_atll)
    account_id_hd = fields.Char(string='Ref. Hutang Dagang', default=_default_account_id_hd)
    account_id_hp = fields.Char(string='Ref. Hutang Pajak', default=_default_account_id_hp)
    
    account_id_hps = fields.Char(string='Ref. Hutang Pemegang Saham', default=_default_account_id_hps)
    account_id_sgujp = fields.Char(string='Ref. Sewa Guna Usaha Jangka Panjang', default=_default_account_id_sgujp)
    account_id_hki = fields.Char(string='Ref. Hutang Kredit Investasi', default=_default_account_id_hki)
    account_id_hkoj = fields.Char(string='Ref. Hutang Kredit Obligasi Jakarta', default=_default_account_id_hkoj)
    account_id_hbj = fields.Char(string='Ref. Hutang Bank Jakarta', default=_default_account_id_hbj)
    account_id_hko = fields.Char(string='Ref. HUtang Kredit Obligasi', default=_default_account_id_hko)
    
    account_id_myd = fields.Char(string='Ref. Modal Yang Disetor', default=_default_account_id_myd)
    account_id_sldt = fields.Char(string='Ref. Saldo Laba Ditahan', default=_default_account_id_sldt)
    account_id_pmd = fields.Char(string='Ref. Penambahan Modal Disetor', default=_default_account_id_pmd)
    account_id_slblj = fields.Char(string='Ref. Saldo Laba s/d bulan lalu Jakarta', default=_default_account_id_slblj)
    account_id_sbbi = fields.Char(string='Ref. Saldo Berjalan Bulan Ini', default=_default_account_id_sbbi)
    


    @api.onchange('date_start','date_end')
    def onchange_date(self):
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise exceptions.ValidationError('Warning, End Date must greater than Start Date !!!')

    @api.multi
    def print_report(self):
        name = 'report_neraca_xlsx' if str(self.report_type) == 'xlsx' else 'report_neraca_pdf'
        res = self.env['report'].get_action(self, name)
        return res
        
wizard_neraca()


