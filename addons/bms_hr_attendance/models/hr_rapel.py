from odoo import models, fields, api, SUPERUSER_ID
import os, base64, xlrd
from xlrd import open_workbook, XLRDError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import Warning
import time
import logging
import pytz
from pytz import timezone
from datetime import datetime, timedelta
import xlrd
_logger = logging.getLogger(__name__)

class HrAttendanceRapel(models.Model):
    _name = 'hr.attendance.rapel'

    name = fields.Char(string="Name")
    date = fields.Date(string="Date")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="State", default="draft")
    book = fields.Binary(string='File Excel')
    book_filename = fields.Char(string='File Name')
    line_ids = fields.One2many('hr.attendance.rapel.line', 'rapel_id', string="Details")
    import_error_note = fields.Text("Error Note")

    @api.multi
    def import_rapel(self):
        if not self.book:
            raise Warning('File belum diupload!')
        return self.upload_import_rapel_function(False,False)

    @api.multi
    def upload_import_rapel_function(self, workbook, sheet_number):
        data_matrix = {}

        if not workbook and not sheet_number:
            file = os.path.splitext(self.sudo().book_filename)
            if file[1] not in ('.xls', '.xlsx'):
                raise UserError("Invalid File! Please import the correct file")

            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.sudo().book))
            sheet = wb.sheet_by_index(0)
        else:
            wb = workbook
            sheet = wb.sheet_by_index(sheet_number)

        col = 1
        row = 1

        warning = ''

        # end of header section
        data_matrix = []
        # start validating detail section
        while row != sheet.nrows:
            _logger.warning("row %s/%s" % (row,sheet.nrows))
            employee_id = False
            nik = False
            total = False
            padding="{0:02d}"
            col = 0


            if sheet.cell(row, col).value:
                nik = str(int(sheet.cell(row, col).value))
                employee_id = self.env['hr.employee'].search([('no_induk', '=', nik)])
                if not employee_id:
                    warning+="Data no induk pada baris ke %s tidak ada pada sistem\n" % (row)
            else:
                warning+="Data No Induk pada baris ke %s tidak diisi\n" % (row)
           
            col+=2

            if sheet.cell(row, col).value:
                if sheet.cell_type(row, col) != 2:
                    warning+="Data total pada baris ke %s bukan format angka\n" % (row)
                else:
                    total = sheet.cell(row, col).value
            else:
                warning+="Data total pada baris ke %s tidak diisi\n" % (row)


            if not warning:
                data_matrix.append([0,False,{
                    'employee_id': employee_id.id,
                    'nik' : nik,
                    'total' : total,
                    'pinjaman_import_id' : self.id,
                    }])

            row+=1
        if not warning:
            self.line_ids=False
            self.write({'line_ids': data_matrix, 'import_error_note': False})
        else:
            self.write({'import_error_note': warning})

    @api.multi
    def confirm(self):
        self.state = 'confirm'

    @api.multi
    def set_draft(self):
        self.state = 'draft'

class HrAttendanceRapelLine(models.Model):
    _name = 'hr.attendance.rapel.line'

    rapel_id = fields.Many2one('hr.attendance.rapel')
    nik = fields.Char(string="NIK")
    employee_id = fields.Many2one("hr.employee",string="Nama")
    total = fields.Float(string="Total")