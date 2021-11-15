import time
from datetime import date
from odoo import http
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class WizardAssetDepreciation(models.TransientModel):
    _name = "wizard.asset.depreciation.report"
    _description = "Asset Depreciation Report"

    as_of_date = fields.Date(string='As of Date', required=True, default=lambda self:time.strftime('%Y-%m-%d'))
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id, required=True)

    @api.multi
    def print_report(self):
        res = self.env['report'].get_action(self, 'asset_depreciation_report')
        print "---------------", res
        return res 