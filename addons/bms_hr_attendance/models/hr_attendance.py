# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    _description = "Attendance"
    _order = "check_in desc"

    premi_value = fields.Float('Premi Value')

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            attendance_check_in = (datetime.strptime(attendance.check_in, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)) if attendance.check_in else 0
            check_out_last_attendance_before_check_in = (datetime.strptime(last_attendance_before_check_in.check_out, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)) if last_attendance_before_check_in.check_out else 0
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and (attendance_check_in.time().hour != 0) and check_out_last_attendance_before_check_in > attendance_check_in:
                print '======================1', check_out_last_attendance_before_check_in, attendance_check_in, attendance.id
                raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s. Check in tidak boleh lebih awal dari check out kemarin!!") % {
                    'empl_name': attendance.employee_id.name_related,
                    'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(attendance.check_in))),
                })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ])
                if no_check_out_attendances:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                        'empl_name': attendance.employee_id.name_related,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
                    })
            # else:
            #     # we verify that the latest attendance with check_in time before our check_out time
            #     # is the same as the one before our check_in time computed before, otherwise it overlaps
            #     last_attendance_before_check_out = self.env['hr.attendance'].search([
            #         ('employee_id', '=', attendance.employee_id.id),
            #         ('check_in', '<', attendance.check_out),
            #         ('id', '!=', attendance.id),
            #     ], order='check_in desc', limit=1)
            #     if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
            #         print '======================2', last_attendance_before_check_in,last_attendance_before_check_out
            #         raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
            #             'empl_name': attendance.employee_id.name_related,
            #             'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(last_attendance_before_check_out.check_in))),
            #         })

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    raise exceptions.ValidationError(_(str(attendance.employee_id.name)+' : "Check Out" time cannot be earlier than "Check In" time.'))