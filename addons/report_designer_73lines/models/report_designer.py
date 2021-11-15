# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.
import uuid
from odoo import models, fields, api
from odoo.addons.website.models.website import slugify


class Report(models.Model):
    _inherit = 'report'

    @api.model
    def new_report(self, name, object_name=False, layout=False):
        templates = self.env['ir.ui.view'].search([('key', 'ilike', 'report_designer_73lines.default_report')], order='id asc')
        report_xmlid = False
        uq_key = str(uuid.uuid4()).replace('-', '')[:8]
        report_name = slugify(name, max_length=50) + "-" + uq_key
        template_module = report_name.replace('-', '_')

        for template in templates:
            report_xmlid = self.env['report.designer'].copy_template_data(template, template_module, report_name, object_name, layout)

        self.env['ir.module.module'].create({
            "name": template_module,
            "shortdesc": name,
            "application": False,
            "icon": "/base/static/description/icon.png",
            "description": "Export report using Report Designer",
            "state": "installed",
            "author": self.env.user.company_id.name,
        })

        return report_xmlid


class ReportDesigner(models.Model):
    _name = 'report.designer'

    @api.model
    def get_record_data(self, report_id=False):
        rec_dict = {}
        if report_id:
            ir_report_model = self.env['ir.actions.report.xml'].browse([int(report_id)])
            records = self.env[ir_report_model.model].search([])
            for record in records:
                rec_dict[record.id] = record.display_name
        return rec_dict

    @api.model
    def get_field_data(self, report_id=False):
        rec_dict = {}
        if report_id:
            ir_report_model = self.env['ir.actions.report.xml'].browse([int(report_id)])
            record = self.env['ir.model'].search([('model', '=', ir_report_model.model)])
            for field in record.field_id:
                rec_dict[field.name] = field.display_name
            return rec_dict

    def copy_template_data(self, template, template_module, report_name, object_name, layout):
        template_name = template.key.split('.')[1]
        if '_document' in template_name:
            report_name = report_name + '_document'

        report_xmlid = "%s.%s" % (template_module, report_name)

        template_id = template
        key = template_module + '.' + report_name
        report = template_id.copy({'key': key})

        self.env['ir.model.data'].create({'module': template_module,
                                          'model': 'ir.ui.view',
                                          'name': report_name,
                                          'res_id': report})
        report_arch = report.arch.replace(template.key, report_xmlid)
        report.write({
            'arch': report_arch.replace('report.external_layout', layout),
            'name': report_name,
            'model': object_name,
        })
        return report_xmlid


class ReportTagAttribute(models.Model):
    _name = 'report.tag.attribute'

    name = fields.Char(string='Attribute Name', required=True)
    display = fields.Boolean(string='Enable Field Selection')
    second_attribute = fields.Char(string='Second Attribute')
    with_attrs = fields.Char(string='attrs can use with main attribute')


class ReportWidget(models.Model):
    _name = 'report.widget'

    name = fields.Char(string='Widget Name', required=True)
    widget_json = fields.Char(string='Widget JSON', required=True)
