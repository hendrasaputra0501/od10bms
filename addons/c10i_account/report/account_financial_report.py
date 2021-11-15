from odoo import api, fields, models

class account_financial_report(models.Model):
    _inherit = "account.financial.report"
    
    show_view_label = fields.Boolean('Show Parent Label', default=False)