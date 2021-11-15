# -*- coding: utf-8 -*-
from odoo import http

# class BmsHrAttendance(http.Controller):
#     @http.route('/bms_hr_attendance/bms_hr_attendance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bms_hr_attendance/bms_hr_attendance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bms_hr_attendance.listing', {
#             'root': '/bms_hr_attendance/bms_hr_attendance',
#             'objects': http.request.env['bms_hr_attendance.bms_hr_attendance'].search([]),
#         })

#     @http.route('/bms_hr_attendance/bms_hr_attendance/objects/<model("bms_hr_attendance.bms_hr_attendance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bms_hr_attendance.object', {
#             'object': obj
#         })