# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.
import json
import re
import zipfile
from contextlib import closing
import io
import os
from lxml import etree
from lxml.builder import E
import werkzeug
from collections import OrderedDict

from odoo import http, tools
from odoo.http import request

from odoo.addons.website.controllers.main import Website


class WebsiteReportDesigner(http.Controller):
    @http.route(['/report/editor'], type='http', auth='public', website=True)
    def select_template(self, **post):
        models = request.env['ir.model'].sudo().search([('transient', '=', False)])
        model_name_lst = []
        for each_model in models:
            model_name_lst.append(each_model.model)
        paperformats = request.env['report.paperformat'].sudo().search([])
        layouts = request.env['ir.ui.view'].sudo().search([('use_as_layout', '=', True)])
        all_reports = request.env['ir.actions.report.xml'].sudo().search([
            ('model', 'in', model_name_lst),
            ('report_type', 'in', ['qweb-pdf', 'qweb-html']),
            ('is_report_designer', '=', True)],
            order="name asc")

        reports = request.env['ir.actions.report.xml']
        view = request.env['ir.ui.view']
        for report in all_reports:
            domain = report.associated_view()['domain']
            if len(view.search(domain)) > 1:
                reports += report

        values = {
            'models': models,
            'paperformats': paperformats,
            'layouts': layouts,
            'reports': reports,
        }

        return request.render("report_designer_73lines.main_report_designer_form", values)

    @http.route(['/report_designer/dialog'], type='json', auth='public', website=True)
    def report_designer_dialog(self, **post):
        res = {
            'attribute_types': None,
            'field_names': None,
            'function_names': None,
            'relation_field_names': None,
            'relation_function_names': None,
            'report_widget': None
        }
        if post['foreach_field'] and post['foreach_field'].find('doc.', 0, len(post['foreach_field'])) != -1:
            doc, field_name = post['foreach_field'].split('doc.')
            if post['foreach_field'].startswith('doc.', 0, len(post['foreach_field'])):
                report = request.env['ir.actions.report.xml'].sudo().browse(int(post['report_id']))
                if report and report.model and field_name:
                    model_field = request.env['ir.model.fields'].search([
                        ('name', '=', field_name),
                        ('model', '=', report.model)], limit=1)
                    if model_field.relation:
                        relation_field_names = {}
                        rel_model = request.env[model_field.relation].search([], limit=1)
                        res['relation_function_names'] = sorted([func for func in dir(rel_model) if callable(getattr(rel_model, func)) and not func.startswith("_")])
                        all_fields = request.env['ir.model.fields'].search([('model', '=', model_field.relation)])
                        for field in sorted(all_fields):
                            relation_field_names[field.name] = field.field_description
                        sorted(relation_field_names)
                        res['relation_field_names'] = relation_field_names

        field_names = {}
        final_attributes_dict = {}

        for attribute in request.env['report.tag.attribute'].sudo().search([]):
            final_attributes_dict[attribute.name] = json.dumps({
                "name": attribute.name,
                "display": attribute.display,
                "second_attribute": attribute.second_attribute or False,
                "with_attrs": attribute.with_attrs
            })

        report_widget = {}
        for widget in request.env['report.widget'].sudo().search([]):
            report_widget[widget.name] = widget.widget_json

        if report_widget:
            res['report_widget'] = report_widget

        report_id = post.get('report_id', False)
        if report_id:
            ir_report_model = request.env['ir.actions.report.xml'].browse([int(report_id)])
            record = request.env['ir.model'].search([('model', '=', ir_report_model.model)])
            model = request.env[ir_report_model.model].search([], limit=1)
            res['function_names'] = sorted([func for func in dir(model) if callable(getattr(model, func)) and not func.startswith("_")])
            for field in sorted(record.field_id):
                field_names[field.name] = {
                    "label": field.field_description,
                    "type": field.ttype,
                    "relation": field.relation
                }
            sorted(field_names)

        res['attribute_types'] = OrderedDict(sorted(final_attributes_dict.items(), key=lambda item: item[1][0]))
        res['field_names'] = field_names

        return res

    @http.route(['/report-designer-snippets'], type='json', auth='public', website=True)
    def designer_templates(self, **post):
        return request.env.ref('report_designer_73lines.report_snippets').render(None)

    @http.route(['/create-report'], type='http', auth='user', website=True, method=['post'])
    def create_report(self, **post):
        ir_view = request.env['report'].sudo() \
            .new_report(post.get('name'), object_name=post.get('model'), layout=post.get('layout'))

        vals = {
            'name': post.get('name'),
            'model': post.get('model'),
            'type': 'ir.actions.report.xml',
            'report_type': post.get('report_type'),
            'report_name': ir_view,
            'is_report_designer': True
        }

        if post.get('paperformat', False):
            vals.update({'paperformat_id': post.get('paperformat')})

        report = request.env['ir.actions.report.xml'].sudo().create(vals)
        report.create_action()
        url = "/report/edit/" + re.sub(r"^report_designer_73lines\.", '', ir_view) + "?report_id=" + str(report.id)

        return werkzeug.utils.redirect(url)

    @http.route(['/edit-report'], type='http', auth='user', website=True)
    def edit_report(self, **post):
        selected_report = post.get('reports')
        report_obj = request.env['ir.actions.report.xml'].sudo().browse(int(selected_report))
        url = '/report/edit/' + report_obj.report_name + '?report_id=' + selected_report
        return werkzeug.utils.redirect(url)

    @http.route('/report/edit/<page:report>', type='http', auth="public", website=True, cache=300)
    def edit_report_display(self, report, **kwargs):
        values = {'edit_report': True, 'field_edition': True}
        return request.render('report_designer_73lines.report_designer_loader', values)

    def is_integer(self, string):
        try:
            int(string)
            return True
        except Exception:
            pass

    @http.route('/report/get_report_html/', type='json', website=True, auth="user")
    def get_report_html(self, report_id=False):
        if report_id and self.is_integer(report_id):
            ir_report = request.env['ir.actions.report.xml'].search([('id', '=', report_id)])
            if ir_report:
                views = request.env['ir.ui.view'].search([('name', 'ilike', ir_report.report_name.split('.')[1]), ('type', '=', 'qweb')])
                if views:
                    view_name = ir_report.report_name + '_document'
                    element, document = request.env['ir.qweb'].get_template(view_name, {})
                    return {
                        'template': etree.tostring(element, encoding='utf-8').decode(),
                        'id': request.env['ir.ui.view'].get_view_id(view_name) or ''
                    }
        return False

    @http.route('/report/preview/<page:report>', type='http', auth="user", website=True)
    def report(self, report, report_id=False, record_id=False):
        if report_id and self.is_integer(report_id):
            ir_report = request.env['ir.actions.report.xml'].search([('id', '=', report_id)])
            if ir_report:
                views = request.env['ir.ui.view'].search(
                    [('name', 'ilike', ir_report.report_name.split('.')[1]), ('type', '=', 'qweb')])
                if views:
                    view_name = ir_report.report_name
                    if record_id and self.is_integer(record_id):
                        values = request.env[ir_report.model].search([('id', '=', int(record_id))])
                    else:
                        values = request.env[ir_report.model].search([], limit=1)
                    return request.render(view_name, {"docs": values})
        return request.render('website.404')

    @http.route('/report/export/<int:report_id>', type='http', auth="public", website=True)
    def report_export(self, report_id=False, **post):
        if report_id:
            content, report_name = self.get_zip_content(report_id)
            if content and report_name:
                return request.make_response(content, headers=[
                    ('Content-Disposition', 'customizations.zip;filename=Report-' + report_name + '-Customizations.zip'),
                    ('Content-Type', 'application/zip'),
                    ('Content-Length', len(content))])
        return request.render('website.404')

    def get_zip_content(self, report_id):
        ir_report = request.env['ir.actions.report.xml'].browse(report_id)
        if ir_report:
            report_name = ir_report.report_name.split('.')[1]
            module_name = report_name.replace('-', '_')
            dir_path = {
                "report_template_path": os.path.join("report", report_name + ".xml"),
                "report_action_path": os.path.join("report", "report_action.xml")
            }
            view = request.env['ir.ui.view'].search(
                [('name', 'ilike', report_name), ('type', '=', 'qweb')])

            report_action = '''<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <report
            id="%s"
            string="%s"
            model="%s"
            report_type="%s"
            file="%s"
            name="%s"
        />

        <record id="%s" model="ir.actions.report.xml">
            <field name="is_report_designer">True</field>
            <field name="print_report_name">%s</field>
        </record>
    </data>
</odoo>
''' % (
                "action_report_" + report_name,
                ir_report.name,
                ir_report.model,
                ir_report.report_type,
                module_name + "." + ir_report.report_name.split('.')[1],
                module_name + "." + ir_report.report_name.split('.')[1],
                "action_report_" + report_name,
                "'%s-%s.pdf' % (object.name, object.id)",
            )

            manifest = """# -*- coding: utf-8 -*-
{
    'name': %r,
    'version': '1.0',
    'category': 'Report Designer',
    'description': %s,
    'depends': [%s
    ],
    'data': [%s
    ],
    'application': %s
}
""" % (
                module_name,
                'u"""\n%s\n"""' % "Export report using Report Designer",
                "\n        %r," % "report_designer_73lines",
                ''.join("\n        %r," % value for key, value in dir_path.items()),
                False
            )
            manifest = manifest.encode('utf-8')
            report_action = report_action.encode('utf-8')

            with closing(io.BytesIO()) as buf:
                tools.trans_export(False, [module_name], buf, 'po', request._cr)
                pot = buf.getvalue()

            with closing(io.BytesIO()) as f:
                with zipfile.ZipFile(f, 'w') as archive:
                    data = E.data()
                    for v in view:
                        data.append(etree.fromstring(v.arch_base))
                        ele = data.findall(".//t[@t-name]")
                        if len(ele):
                            t_name = ele[0].attrib['t-name'].split('.')[1]
                            ele[0].set('id', t_name)
                            ele[0].tag = "template"
                            del ele[0].attrib['t-name']
                        data.append(etree.fromstring('''
    <record id="%s" model="ir.ui.view">
        <field name="model">%s</field>
    </record>''' % (t_name, ir_report.model)
                                                     )
                                    )

                    template_xml = etree.tostring(E.odoo(data), pretty_print=True, encoding='UTF-8', xml_declaration=True)
                    archive.writestr(os.path.join(module_name, dir_path['report_template_path']), template_xml)
                    archive.writestr(os.path.join(module_name, dir_path['report_action_path']), report_action)
                    archive.writestr(os.path.join(module_name, 'i18n', module_name + '.pot'), pot)
                    archive.writestr(os.path.join(module_name, '__manifest__.py'), manifest)
                    archive.writestr(os.path.join(module_name, '__init__.py'), b'')

                return f.getvalue(), (ir_report.name + "-" + str(ir_report.id)).replace(' ', '-')
        return ()

class Website(Website):
    @http.route()
    def customize_template_get(self, key, full=False, bundles=False):
        views = super(Website, self).customize_template_get(key, full=full, bundles=bundles)
        url = request.httprequest.headers.get('Referer', '')
        if url.find('/report/edit/') != -1:
            extract_report_key = url.split("?")[0].split("/")
            report_key = extract_report_key[len(extract_report_key) - 1] + "_document"
            view = request.env["ir.ui.view"].get_view_data(report_key)
            views.append(view[0])
        return views
