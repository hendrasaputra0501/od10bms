# -*- coding: utf-8 -*-
from odoo import http

# class BmsStock(http.Controller):
#     @http.route('/bms_stock/bms_stock/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bms_stock/bms_stock/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bms_stock.listing', {
#             'root': '/bms_stock/bms_stock',
#             'objects': http.request.env['bms_stock.bms_stock'].search([]),
#         })

#     @http.route('/bms_stock/bms_stock/objects/<model("bms_stock.bms_stock"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bms_stock.object', {
#             'object': obj
#         })