odoo.define('report_designer_73lines.web_settings_dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var Dashboard = require('web_settings_dashboard');
    var Widget = require('web.Widget');
    var Model = require('web.Model');

    var QWeb = core.qweb;

    QWeb.add_template('/report_designer_73lines/static/src/xml/website_templates.xml');

    Dashboard.Dashboard.include({
        init: function () {
            var res = this._super.apply(this, arguments);
            this.all_dashboards.push('report_designer');
            return res;
        },
        load_report_designer: function (data) {
            return new DashboardReportDesigner(this, data.apps).replace(this.$('.o_web_settings_dashboard_report_designer'));
        }
    });


    var DashboardReportDesigner = Widget.extend({
        template: 'DashboardReportDesigner',
        events: {
            'click .o_start_report_designing': 'on_start_design',
            'click .o_report_list': 'created_report_list',
        },
        init: function () {
            return this._super.apply(this, arguments);
        },

        start: function () {
            var self = this;
            var domain = [["is_report_designer", "=", true]];
            var model_fields = ['name'];
            new Model("ir.actions.report.xml").call('search_read', [domain, model_fields]).then(function (res) {
                self.$el.find('.o_web_settings_dashboard_header').html(res.length + " Reports");
            });

            new Model('ir.config_parameter').call('get_param', ['database.uuid', false]).then(function (dbuuid) {
                var apps = self.$el.find('.org_logo_with_uuid_name').attr('data-app-name');
                var src = 'https://srv.73lines.com/get-org-logo';
                self.$el.find('.org_logo_with_uuid_name').attr('src', src + '?dbuuid=' + dbuuid + '&apps=' + apps);
            });

            this._super.apply(this, arguments);
        },
        on_start_design: function (e) {
            this.do_action('report_designer_73lines.action_report_designer');
        },
        created_report_list: function (e) {
            var self = this;
            this.rpc("/web/action/load", {
                action_id: "base.ir_action_report_xml",
            }).then(function (action) {
                action.display_name = 'Report Created Using Report Designer';
                action.domain = [['is_report_designer', '=', true]];
                self.do_action(action);
            });
        }

    });
});