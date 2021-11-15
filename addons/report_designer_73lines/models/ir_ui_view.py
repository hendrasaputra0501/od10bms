# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class View(models.Model):
    _inherit = 'ir.ui.view'

    use_as_layout = fields.Boolean(string='Use as Layout', default=False)

    @api.multi
    def render(self, values=None, engine='ir.qweb'):
        if values and values.get('field_edition', False):
            self.env.context = dict(self.env.context, field_edition=True)
        return super(View, self).render(values=values, engine=engine)

    @api.multi
    def get_view_data(self, view_id):
        if view_id:
            view = self._view_obj(view_id)
            return view.read(['name', 'id', 'key', 'xml_id', 'arch', 'active', 'inherit_id'])
        else:
            return None
