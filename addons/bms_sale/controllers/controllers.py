# -*- coding: utf-8 -*-
from odoo import http

# class BmsSale(http.Controller):
#     @http.route('/bms_sale/bms_sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bms_sale/bms_sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bms_sale.listing', {
#             'root': '/bms_sale/bms_sale',
#             'objects': http.request.env['bms_sale.bms_sale'].search([]),
#         })

#     @http.route('/bms_sale/bms_sale/objects/<model("bms_sale.bms_sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bms_sale.object', {
#             'object': obj
#         })