# -*- coding: utf-8 -*-
from odoo import http

# class C10iEmployeeAdvanceV2(http.Controller):
#     @http.route('/c10i_employee_advance_v2/c10i_employee_advance_v2/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/c10i_employee_advance_v2/c10i_employee_advance_v2/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('c10i_employee_advance_v2.listing', {
#             'root': '/c10i_employee_advance_v2/c10i_employee_advance_v2',
#             'objects': http.request.env['c10i_employee_advance_v2.c10i_employee_advance_v2'].search([]),
#         })

#     @http.route('/c10i_employee_advance_v2/c10i_employee_advance_v2/objects/<model("c10i_employee_advance_v2.c10i_employee_advance_v2"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('c10i_employee_advance_v2.object', {
#             'object': obj
#         })