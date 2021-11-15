# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#   --- Deby Wahyu Kurdian ---                                               #
#                                                                            #
##############################################################################

from odoo.addons.jasper_reports import JasperDataParser
from odoo.addons.jasper_reports import jasper_report
import odoo.tools


class jasper_rekap_timbangan(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(jasper_rekap_timbangan, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'parameters'

    def generate_parameters(self, cr, uid, ids, data, context):
        return data['form']

    def generate_properties(self, cr, uid, ids, data, context):
        return {}

    def generate_output(self,cr, uid, ids, data, context):
        return data['report_type']

    def generate_records(self, cr, uid, ids, data, context):
        return {}

# jasper_report.ReportJasper('report.rekap_timbangan_internal_metro', 'wizard.weighbridge.recap.metro', parser=jasper_rekap_timbangan,)
# jasper_report.ReportJasper('report.rekap_timbangan_internal_sampit', 'wizard.weighbridge.recap.sampit', parser=jasper_rekap_timbangan,)
# jasper_report.ReportJasper('report.rekap_timbangan_beacukai_metro', 'wizard.weighbridge.recap.metro', parser=jasper_rekap_timbangan,)
# jasper_report.ReportJasper('report.rekap_timbangan_beacukai_sampit', 'wizard.weighbridge.recap.sampit', parser=jasper_rekap_timbangan,)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: