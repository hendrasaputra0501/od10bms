# -*- coding: utf-8 -*-
from odoo import http

# class BmsHr(http.Controller):
#     @http.route('/bms_hr/bms_hr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bms_hr/bms_hr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bms_hr.listing', {
#             'root': '/bms_hr/bms_hr',
#             'objects': http.request.env['bms_hr.bms_hr'].search([]),
#         })

#     @http.route('/bms_hr/bms_hr/objects/<model("bms_hr.bms_hr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bms_hr.object', {
#             'object': obj
#         })