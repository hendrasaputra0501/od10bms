# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#   --- Deby Wahyu Kurdian ---                                               #
#                                                                            #
##############################################################################

from odoo.addons.jasper_reports import JasperDataParser
from odoo.addons.jasper_reports import jasper_report
import odoo.tools


class jasper_report_wp_cost(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(jasper_report_wp_cost, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'parameters'
    def generate_parameters(self, cr, uid, ids, data, context):
        return {
                'id': data['id']
        }

    def generate_properties(self, cr, uid, ids, data, context):
        return {}

    def generate_output(self,cr, uid, ids, data, context):
        return data['report_type']
    
    def generate_records(self, cr, uid, ids, data, context):
        return {}

jasper_report.ReportJasper('report.report_wp_cost',  'report.wp.cost', parser=jasper_report_wp_cost,)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
