# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.addons.jasper_reports import JasperDataParser
from odoo.addons.jasper_reports import jasper_report

class jasper_report_sales(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(jasper_report_sales, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'parameters'

    def generate_parameters(self, cr, uid, ids, data, context):
        
        return {
                'from_date' : data['form']['from_date'],
                'to_date'   : data['form']['to_date'],
                'company_name' : data['form']['company_id'][1]
                }

    def generate_properties(self, cr, uid, ids, data, context):
        return {}

    def generate_output(self,cr, uid, ids, data, context):
        return data['form']['report_type']
    
    def generate_records(self, cr, uid, ids, data, context):
        return {}

jasper_report.ReportJasper('report.report_sales', 'wizard.sales', parser=jasper_report_sales,)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
