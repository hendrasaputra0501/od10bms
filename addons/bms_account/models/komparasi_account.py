from odoo import tools
from odoo import models, fields, api

class KomparasiAccount(models.Model):
    _name = 'komparasi.account'
    _description = "Invoices Statistics"
    _auto = False
    _rec_name = 'account_balance_sheet'

    # date = fields.Date(readonly=True)

    account_id = fields.Many2one('account.account', string='Account', readonly=True, domain=[('deprecated', '=', False)])   
    debit = fields.Float(string='debit', readonly=True)
    credit = fields.Float(string='credit', readonly=True)
    balance = fields.Float(string='balance', readonly=True)
    lead_create_date = fields.Datetime('Creation Date', readonly=True)   
    account_balance_sheet = fields.Boolean(string='account_balance_sheet')   

    def _select(self):
        return """
            SELECT
                aml.id,
                aml.account_id, 
                aml.debit, 
                aml.credit, 
                aml.debit - aml.credit AS balance,
                aml.create_date as lead_create_date,
                aat.include_initial_balance as account_balance_sheet, 
                aa.user_type_id
            """

    def _from(self):
        return """
            FROM account_move_line aml, account_account aa, account_account_type aat
        """

    # def _join(self):
    #     return """
    #         JOIN aa.id = aml.account_id 
    #         JOIN aa.id = aml.account_id
    #     """    

    def _where(self):
        return """
            WHERE
                EXTRACT(year FROM aml.create_date) = (SELECT periode FROM komparasi_wizard ORDER BY id DESC limit 1)
            AND
                aa.id = aml.account_id
            AND
                aat.id=aa.user_type_id
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._where())
        
        )
        # """ % (self._table, self._select(), self._from(), self._join(), self._where())