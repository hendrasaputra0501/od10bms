odoo.define('report_print_preview', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var ActionManager = require('web.ActionManager');
var ControlPanelMixin = require('web.ControlPanelMixin');
var ReportManager = require('report.report');
var ReportAction = require('report.client_action');
var QWeb = core.qweb;

var ReportClientAction = core.action_registry.get('report.client_action');
ReportClientAction.include({
    init: function (parent, action, options) {
        var self = this;
        self._super.apply(self, arguments);
        self.action = options.action || {};
    },
    start: function() {
        var self = this;
        self.auto_print = self.action.auto_print;
        return $.when(self._super.apply(self, arguments)).then(function () {
            self.$buttons.on('click', '.o_report_direct', self.on_click_direct);
        });
    },
    on_click_direct: function () {
        var self = this;
        self.iframe.contentWindow.print();
    },
    _on_iframe_loaded: function () {
        var self = this;
        self._super.apply(self, arguments);
        if(self.auto_print){
            self.auto_print = false;
            self.on_click_direct();
        }
    }
});

var ReportClientPreview = Widget.extend(ControlPanelMixin, {
    template: 'report.client_action',
    init: function (parent, action, options) {
        var self = this;
        self._super.apply(self, arguments);
        options = options || {};
        self.action_manager = parent;
        self.action = options.action || {};
        self.title = self.action.display_name || self.action.name;
        var report_url = '/report/pdf/' + self.action.report_name;
        report_url += '/' + self.action.context.active_ids.join(',');
        report_url += '?'+self.action.display_name+'.pdf';
        report_url = "/report_print_preview/static/lib/pdfjs/web/viewer.html?file=" + encodeURIComponent(report_url);
        report_url += "#page=1&zoom=page-width&pagemode=none";
        self.report_url = report_url;
    },
    start: function () {
        var self = this;
        self.set('title', self.title);
        self.auto_print = self.action.auto_print;
        self.iframe = self.$('iframe')[0];
        return self._super.apply(self, arguments).then(function () {
            self.$buttons = $(QWeb.render('report.client_action.ControlButtons', {}));
            self.$buttons.on('click', '.o_report_print', self.on_click_print);
            self.$buttons.on('click', '.o_report_direct', self.on_click_direct);
            self.$buttons.filter('.o_edit_mode_available, .o_report_edit_mode').hide();
            self._update_control_panel();
            self.iframe.src = self.report_url;
            self.iframe.onload = self.proxy(self._on_iframe_loaded);
        });
    },
    do_show: function () {
        var self = this;
        self._update_control_panel();
        return self._super.apply(self, arguments);
    },
    on_click_print: function () {
        var self = this;
        var action = _.clone(self.action);
        action.preview_print = null;
        return self.do_action(action);
    },
    on_click_direct: function () {
        var self = this;
        var win = self.iframe.contentWindow;
        var pdfViewer = win.PDFViewerApplication.pdfViewer;
        if(pdfViewer && pdfViewer.pageViewsReady){
            win.print();
        }else{
            setTimeout(function() { self.on_click_direct(); }, 50);
        }
    },
    _on_iframe_loaded: function () {
        var self = this;
        if(self.auto_print){
            self.auto_print = false;
            self.on_click_direct();
        }
        var $contents = $(self.iframe).contents();
        $contents.find('#openFile, #viewBookmark').hide();
    },
    _update_control_panel: function () {
        var self = this;
        self.update_control_panel({
            breadcrumbs: self.action_manager.get_breadcrumbs(),
            cp_content: {
                $buttons: this.$buttons
            }
        });
    }
});
core.action_registry.add('report.client_preview', ReportClientPreview);

ActionManager.include({
    ir_actions_report_xml: function (action, options) {
        var self = this;
        if(options){
            options.action = action;
        }
        if (action.report_type === 'qweb-pdf' && action.preview_print) {
            return self.do_action('report.client_preview', options);
        }else{
            return self._super.apply(self, arguments);
        }
    }
});

});