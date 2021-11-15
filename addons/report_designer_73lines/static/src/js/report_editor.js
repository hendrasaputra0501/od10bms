odoo.define('report_designer_73lines.report_editor', function (require) {
    'use strict';

    var core = require('web.core');
    var ajax = require('web.ajax');
    var Model = require('web.Model');
    var Website = require('website.website');
    var Editor = require('web_editor.editor');
    var snippet_editor = require('web_editor.snippet.editor');
    var qs_obj = $.deparam($.param.querystring());
    var allClassList = [];

    var _t = core._t;
    var QWeb = core.qweb;

    QWeb.add_template('/report_designer_73lines/static/src/xml/website_templates.xml');

    var misc = {
        is_report_editor: function () {
            return (window.location.pathname).indexOf('/report/edit/') !== -1 ? true : false;
        },
        is_report_main_page: function () {
            return (window.location.pathname).indexOf('/report/editor') !== -1 ? true : false;
        }
    };

    var ReportEditor = core.Class.extend({
        init: function () {
            this.report_id = parseInt(qs_obj.report_id) !== NaN ? parseInt(qs_obj.report_id) : false;
            this.record_id = parseInt(qs_obj.record_id) !== NaN ? parseInt(qs_obj.record_id) : false;
            this.debug = ("" + qs_obj.debug).toString().trim() !== '' ? qs_obj.debug : '';

            this.links = [
                "/web/static/src/less/web.assets_frontend/import_bootstrap.less.css",
                "/web/static/lib/fontawesome/css/font-awesome.css"
            ];
            _.each(this.links, function (link) {
                $('head').append('<link rel="stylesheet" class="class-list" href="' + link + '" type="text/css"/>');
            });
            this.start();
        },
        start: function () {
            $(window).on("load ul.o_menu_systray", _.bind(this.on_show, this));
            this.load_report();
        },
        load_report: function () {
            var self = this;
            ajax.jsonRpc('/report/get_report_html/', 'call', {
                report_id: this.report_id,
            }).done(function (report_html) {
                if (report_html) {
                    var $inner_content = $(report_html.template).html();
                    var $content = $('<div/>')
                        .attr({
                            'class': 'main_page',
                            'data-oe-id': report_html.id,
                            'data-oe-xpath':".",
                            'data-oe-field':"arch" ,
                            'data-oe-model':"ir.ui.view"
                        })
                        .html($inner_content);
                    $('main').html($content);
                    _.each($('[t-field]'), function (span) {
                        span = $(span);
                        var span_text = span.attr('t-field');
                        span.html(span_text);
                    });
                    _.each($('[t-raw]'), function (span) {
                        span = $(span);
                        var span_text = span.attr('t-raw');
                        span.html(span_text);
                    });
                    _.each($('[t-esc]'), function (span) {
                        span = $(span);
                        var span_text = '<b> Esc: </b>' + span.attr('t-esc');
                        span.html(span_text);
                    });
                    _.each($('[t-set][t-value]'), function (span) {
                        span = $(span);
                        var span_text = '<b> Set: </b>' + span.attr('t-set') + ' <b> Value: </b>'+ span.attr('t-value');
                        span.html(span_text);
                    });
                    allClassList = self._getCSSClass();
                    $('.report_loader').hide();
                }else{
                    window.location = '/report/editor';
                }
            });
        },
        uniqueArray: function (arrArg) {
            return arrArg.filter(function (elem, pos, arr) {
                return arr.indexOf(elem) == pos;
            });
        },
        _getCSSClass: function () {
            var rawClassList = [];
            var finalClassList = [];
            var CSSStyleSheetObj = [];
            for (var i = 0; i < document.styleSheets.length; i++) {
                if (this.links.includes(document.styleSheets[i].href.replace(window.location.origin, ''))) {
                    CSSStyleSheetObj.push(document.styleSheets[i]);
                    if(this.links.length ===  CSSStyleSheetObj.length){
                        break;
                    }
                }
            }
            for (var j = 0; j < CSSStyleSheetObj.length; j++) {
                _.each(CSSStyleSheetObj[j].cssRules, function (style) {
                    if (style.selectorText) {
                        rawClassList.push(style.selectorText);
                    }
                });
            }

            CSSStyleSheetObj = [];

            _.each(rawClassList, function (raw_text) {
                var tmp = [];
                _.map(raw_text.replace(/\>\ |\+\ |\,/g, '').split(' '), function (sub_raw_text) {
                    if(sub_raw_text.startsWith('.')){
                        sub_raw_text = sub_raw_text.slice(1);
                        if(sub_raw_text.indexOf('.') !== -1){
                            sub_raw_text = sub_raw_text.split('.');
                            _.each(sub_raw_text, function (cls) {
                                tmp.push(cls.split(':')[0]);
                            });
                        }else{
                            tmp.push(sub_raw_text.split(':')[0]);
                        }
                    }
                });
                _.map(tmp, function (cls) {
                    finalClassList.push(cls)
                });
            });

            $('.class-list').remove();

            return this.uniqueArray(finalClassList);
        },
        on_show: function () {
            var self = this;
            $('header, footer').remove();
            $('div.navbar').remove();
            $('div#footer').remove();

            /* Remove Process in navbar */
            var checkExist = setInterval(function () {
                if ($('.o_planner_systray').length) {
                    $('.o_planner_systray').hide();
                    clearInterval(checkExist);
                }
            }, 100);

            /* remove unnecessary menu */
            _.each($('ul.o_menu_systray').children(), function (elem) {
                elem = $(elem);
                var data_action = ("" + elem.find('a[data-action]').attr('data-action')).toString().trim();
                var class_name = ("" + elem.attr('class')).toString().trim();
                if (data_action === 'edit' || class_name.indexOf('report_customize_menu') !== -1) {
                    return;
                } else {
                    elem.remove();
                }
            });
            $('ul.o_menu_sections').remove();

            /* Preview Button Click Event */
            $('a#report_preview').click(function (e) {
                var url = window.location.href.replace('/edit/', '/preview/');
                window.open(url, '_blank');
            });

            /* Export Button Click Event */
            $('a#report_export').click(function (e) {
                window.location = '/report/export/'+ self.report_id;
            });

            /* Fill Report Record in selection box */
            new Model("report.designer").call('get_record_data', [this.report_id]).then(function (data) {
                var option_text = '<option selected="true" disabled="disabled" class="option_header"><b> Select Report Record </b></option>';
                for (var r in data) {
                    if (self.record_id == parseInt(r)) {
                        option_text += '<option value="' + window.location.pathname + '?report_id=' + self.report_id + '&record_id=' + r + '" selected>' + data[r] + '</option>'
                    } else {
                        option_text += '<option value="' + window.location.pathname + '?report_id=' + self.report_id + '&record_id=' + r + '">' + data[r] + '</option>'
                    }
                }
                $('select#all_records').html(option_text);
            }).then(function () {
                $('select#all_records').change(function () {
                    var href = $(this).val();
                    if (core.debug) {
                        href += "&debug=" + self.debug;
                    }
                    href = href.replace('/edit/', '/preview/')
                    window.open(href, '_blank');
                });
            });

            /* Fill Field Generator Record in selection box and Change Event */
            new Model("report.designer").call('get_field_data', [this.report_id]).then(function (data) {
                var option_text = '<option selected="true" disabled="disabled" class="option_header"><b> Select Report Field </b></option>';
                for (var r in data) {
                    option_text += '<option value="' + r + '">' + data[r] + '</option>'
                }
                $('select#report_field_name').html(option_text);
            }).then(function () {
                $('select#report_field_name').on('change', function (e) {
                    $("input#report_field_generator").val('t-field="doc.' + $(this).val());
                });
            });
        }
    });

    if (misc.is_report_editor()) {
        new ReportEditor();
    }
    if (misc.is_report_main_page()) {
        $(document).ready(function (e) {
            $('select#model').select2();
        });
    }

    snippet_editor.Class.include({
        _get_snippet_url: function () {
            if (misc.is_report_editor()) {
                return '/report-designer-snippets';
            }
            return '/website/snippets';
        }
    });

    Editor.Class.include({
        save: function () {
            if (qs_obj.report_id && misc.is_report_editor()) {
                $('span[t-field], p[t-field], [t-esc], [t-set][t-value],[t-raw]').html('');
            }
            try {
                return this._super.apply(this, arguments);
            } catch (ex) {
                window.location = window.location.href;
            }
        }
    });

    snippet_editor.Editor.include({
        init: function (BuildingBlock, dom) {
            this._super.apply(this, arguments);
            if (qs_obj.report_id && misc.is_report_editor()) {
                this.$overlay.on('click', '.oe_snippet_attribute', _.bind(this.on_attribute, this));
                if(("" + this.$target.attr('class')).indexOf('main_page') === -1) {
                    $('a#oe_snippet_attribute').removeClass("hidden");
                    $('a#oe_snippet_remove_tr').removeClass("hidden");
                    $('a#oe_snippet_add_tr').removeClass("hidden");
                }
            }
        },
        load_style_options: function () {
            this._super.apply(this, arguments);
            if (qs_obj.report_id && misc.is_report_editor()) {
                if(("" + this.$target.attr('class')).indexOf('main_page') === -1 && ("" + this.$target.attr('class')).indexOf('oe_structure') === -1) {
                    this.$overlay.find('.oe_snippet_move, .oe_snippet_clone, .oe_snippet_remove').removeClass('hidden');
                }else{
                   this.$overlay.find('.oe_snippet_move, .oe_snippet_clone, .oe_snippet_remove').addClass('hidden');
                }
            }
        },
        on_attribute: function (event) {
            var self = this;
            var $target_el = this.$target;
            var attribute_obj = {};

            var $tr = $($target_el.closest('[t-foreach]'));

            for (var idx = 0, len = this.$target[0].attributes.length; idx < len; idx++) {
                attribute_obj[this.$target[0].attributes[idx].name] = this.$target[0].attributes[idx].nodeValue
            }
            var report_id = qs_obj.report_id;
            Website.prompt({
                id: "report_designer_attribute",
                window_title: _t("Set Attribute"),
                init: function () {
                    var self = this;
                    this.$dialog.find('.modal-dialog').addClass('modal-lg');
                    this.$dialog.find(".btn-continue").html('Save').addClass('btn-save').removeClass('btn-continue');
                    this.$dialog.find("#report_designer_attribute").html('');
                    var isForeach = !("t-foreach" in attribute_obj) && $tr.length && $tr.attr('t-foreach') ? $tr.attr('t-foreach') : null;
                    ajax.jsonRpc('/report_designer/dialog', 'call', {
                        'report_id': report_id,
                        'attribute_obj': attribute_obj,
                        'foreach_field': isForeach
                    }).then(function (result) {
                        // Load Modal content
                        self.$dialog.find("#report_designer_attribute").html(QWeb.render('report_designer_dialogbox', {
                            attribute_types: result.attribute_types,
                            field_names: result.field_names,
                            function_names: result.function_names,
                            attribute_obj: attribute_obj,
                            relation_field_names: result.relation_field_names,
                            as: isForeach ? $tr.attr('t-as') : null
                        })).after(QWeb.render('WidgetGeneratorSelection', {widgets: result.report_widget}));

                        self.get_available_attr_list(attribute_obj, result.attribute_types, self.$dialog.find("#attribute_type option"));

                        var $classAutocomplete = $("#class-list").tagEditor({
                            initialTags: attribute_obj['class'] ? attribute_obj['class'].split(' '): [],
                            autocomplete: {
                                source: allClassList,
                                minLength: 2
                            },
                            onChange: function (field, editor, tags) {
                                self.$dialog.find("#attribute_value").val(tags.join(" "));
                            }
                        });

                        self.$dialog.find("#m-fld-normal-m2o, #m-fld-m2m-o2m, #m-rel-fld, #m-fn, #chld-fld").select2();

                        self.update_option_color(self.$dialog);

                        self.$dialog.find("#attribute_type").on('change', function (e) {
                            self.selected_text = $("#attribute_type option:selected").text().trim();
                            self.json_val = $(this).val().trim().length ? JSON.parse($(this).val()) : null;
                            self.$dialog.find("#m-fld-normal-m2o, #m-fld-m2m-o2m, #m-rel-fld, #m-fn, #chld-fld, #widget_name").val('').trigger('change.select2');
                            $('#m-rel-fld').html('');

                            self.$dialog.find("#attribute_value, #class-list + ul").removeClass('input-attr-value-err');

                            if(['t-options', 't-field-options'].includes(self.selected_text)){
                                self.$dialog.find('#report_designer_attribute').addClass('col-sm-8');
                                self.$dialog.find('#widget-selection').addClass('col-sm-4').removeClass('hidden');
                            }else{
                                self.$dialog.find('#report_designer_attribute').removeClass('col-sm-8');
                                self.$dialog.find('#widget-selection').removeClass('col-sm-4').addClass('hidden');
                            }

                            if(['class'].includes(self.selected_text)){
                                self.$dialog.find('.c-class-list').removeClass('hidden');
                                self.$dialog.find('.c-attr-1-val').addClass('hidden');
                                if(attribute_obj['class']) {
                                    $classAutocomplete.tagEditor('addTag', attribute_obj['class'].split(' '));
                                }
                            }else{
                                self.$dialog.find('.c-class-list').addClass('hidden');
                                self.$dialog.find('.c-attr-1-val').removeClass('hidden');
                            }

                            self.$dialog.find(".attr-1, .attr-1 > .attr-inner , .attr-2, .c-m-sel").removeClass('hidden');
                            self.$dialog.find(".c-m-fld-normal-m2o, .c-m-rel-fld, .c-m-fld-m2m-o2m, .c-m-fn").removeClass('hidden');

                            if(['class','style', 'groups', 't-options', 't-field-options'].includes(self.selected_text)){
                                self.$dialog.find(".attr-1 > .attr-inner, .attr-2").addClass('hidden');
                                self.$dialog.find(".attr-1").removeClass('hidden');
                            }else if(['t-foreach'].includes(self.selected_text)){
                                self.$dialog.find(".child_object").addClass('hidden');
                                self.$dialog.find(".c-m-fld-normal-m2o, .c-m-rel-fld").addClass('hidden');
                            }else if(['t-field', 't-raw'].includes(self.selected_text)){
                                self.$dialog.find(".c-m-fld-m2m-o2m, .c-m-fn").addClass('hidden');
                                if(isForeach){
                                    self.$dialog.find(".c-m-sel").addClass('hidden');
                                }
                            }

                            if (self.selected_text in attribute_obj) {
                                self.$dialog.find("#attribute_value").val(attribute_obj[self.selected_text]);
                                if (attribute_obj[self.selected_text].indexOf('doc.') !== -1) {
                                    self.$dialog.find("#m-fld-normal-m2o, #m-fld-m2m-o2m, #m-fn").val(attribute_obj[self.selected_text]).trigger('change.select2');
                                } else if ($tr.length && attribute_obj[self.selected_text].indexOf($tr.attr('t-as') + '.') !== -1) {
                                    self.$dialog.find("#chld-fld").val(attribute_obj[self.selected_text]).trigger('change.select2');
                                } else {
                                    self.$dialog.find('#m-fld-normal-m2o').val('');
                                }
                                self.update_button(self.selected_text, 'Update', 1);
                            } else {
                                self.$dialog.find("#attribute_value").val('');
                                self.update_button(self.selected_text, 'Add');
                            }
                            if (self.json_val) {
                                var second_attr = self.$dialog.find("#second_attribute_type, #second_attribute_value");
                                second_attr.parent().parent().addClass('hidden');
                                second_attr.val('');
                                if (self.json_val.second_attribute) {
                                    second_attr.parent().parent().removeClass('hidden');
                                    self.$dialog.find("#second_attribute_type").val(self.json_val.second_attribute);
                                    var $s_value = self.$dialog.find("#second_attribute_value");
                                    $s_value.val(self.json_val.second_attribute in attribute_obj ? attribute_obj[self.json_val.second_attribute] : '');
                                    if(['t-foreach'].includes(self.selected_text) && !$s_value.val()){
                                        self.$dialog.find("#second_attribute_value").val('line');
                                    }
                                }
                            }
                            if(self.selected_text){
                                $('.c-add-remove').removeClass('hidden');
                            }else{
                                $('.attr-1, .attr-1 > .attr-inner, .attr-2, .c-add-remove').addClass('hidden');
                            }
                        });

                        self.$dialog.find("#m-fld-normal-m2o, #m-fld-m2m-o2m, #m-fn, #chld-fld, #widget_name").on('change', function (e) {
                            $('#m-rel-fld').html('');
                            if(['t-set'].includes(self.selected_text)){
                                self.$dialog.find("#second_attribute_value").val($(this).val());
                            }else{
                                self.$dialog.find("#attribute_value").val($(this).val());
                            }
                            if($(this).prop('id') == 'm-fld-normal-m2o'){
                                var field = $(this).val().split('.')[1];
                                var relation_model = result.field_names[field]['relation'];
                                if(relation_model){
                                    var domain = [['model', '=', relation_model]];
                                    var model_fields = ['name', 'field_description', 'ttype'];
                                    new Model("ir.model.fields").call('search_read', [domain, model_fields])
                                        .then(function (relation_fields) {
                                        var $rel_selection_html = $(QWeb.render('MainObjectRelationFields', {
                                            fields: relation_fields,
                                            obj: field
                                        }));
                                        $('#m-rel-fld').html($rel_selection_html);
                                    })
                                }
                            }
                        });

                        self.$dialog.find("#m-rel-fld").on('change', function (e) {
                            self.$dialog.find("#attribute_value").val($(this).val());
                        });

                        self.$dialog.find("#save_close").on('click', function (e) {
                            if(!self._checkAttrValue()){
                                return false;
                            }
                            self.$dialog.find("#add_update_attr").trigger('click');
                            self.$dialog.find('.btn-save').trigger('click');
                        });

                        self.$dialog.find("#add_update_attr").on('click', function (e) {
                            e.preventDefault();
                            if(!self._checkAttrValue()){
                                return false;
                            }
                            attribute_obj[self.selected_text] = self.$dialog.find("#attribute_value").val();
                            if (self.json_val) {
                                if (self.json_val.second_attribute) {
                                    attribute_obj[self.$dialog.find("#second_attribute_type").val()] = self.$dialog.find("#second_attribute_value").val();
                                }
                            }

                            self.get_available_attr_list(attribute_obj, result.attribute_types, self.$dialog.find("#attribute_type option"));
                            self.update_option_color(self.$dialog);
                            self.update_button(self.selected_text, 'Update', 1);
                        });

                        self.$dialog.find("#remove_attr").on('click', function (e) {
                            e.preventDefault();
                            delete attribute_obj[self.selected_text];
                            if (self.json_val) {
                                if (self.json_val.second_attribute) {
                                    delete attribute_obj[self.$dialog.find("#second_attribute_type").val()];
                                }
                            }
                            self.get_available_attr_list(attribute_obj, result.attribute_types, self.$dialog.find("#attribute_type option"));
                            self.$dialog.find("#attribute_type, #attribute_value, #second_attribute_value, #m-fld-normal-m2o, #chld-fld")
                                .val('')
                                .trigger('change.select2');
                            self.$dialog.find(".attr-1, .attr-1 > .attr-inner , .attr-2, .c-m-sel, .c-add-remove").addClass('hidden');
                            self.$dialog.find('#report_designer_attribute').removeClass('col-sm-8');
                            self.$dialog.find('#widget-selection').removeClass('col-sm-4').addClass('hidden');
                            self.clearCSSClass($classAutocomplete);
                            self.update_option_color(self.$dialog);
                            self.update_button(self.selected_text, 'Add');
                        });

                        if(!self._checkStartWithAttr(Object.keys(attribute_obj), 't-')){
                            var field_op = '"name": "t-field"';
                            self.$dialog.find("#attribute_type option[value*='" + field_op + "']").prop('selected', true).trigger('change');
                        }
                    });
                },
                _checkAttrValue:function(){
                    var $f_attr_value = this.$dialog.find("#attribute_value");
                    var $class_list = this.$dialog.find("#class-list").next('ul');
                    var f_value = $f_attr_value.val();
                    if(f_value){
                        $f_attr_value.removeClass('input-attr-value-err');
                        $class_list.removeClass('input-attr-value-err');
                        return true;
                    }else{
                        alert("Attribute value required");
                        $f_attr_value.focus().addClass('input-attr-value-err');
                        $class_list.focus().addClass('input-attr-value-err');
                        return false;
                    }
                },
                _checkStartWithAttr: function (attrs_list, str) {
                    for (var i in attrs_list) {
                        if (attrs_list[i].startsWith(str) && !['t-field', 't-raw'].includes(attrs_list[i])) return true;
                    }
                    return false;
                },
                clearCSSClass: function ($obj) {
                    var tags = $obj.tagEditor('getTags')[0].tags;
                    for (var i = 0; i < tags.length; i++) {
                        $obj.tagEditor('removeTag', tags[i]);
                    }
                },
                update_button: function (selected_text, btn_text, remove_btn) {
                    this.$dialog.find("#remove_attr").prop('disabled', !remove_btn);
                    this.$dialog.find("#add_update_attr").html(btn_text).prop('disabled', !selected_text.length);
                },
                update_option_color: function (dialog) {
                    _.each(dialog.find("#attribute_type option"), function (option) {
                        option = $(option);
                        option.removeAttr('style');
                        if (option.text().trim() in attribute_obj) {
                            option.css({
                                'color': 'green',
                                'font-weight': 'bold'
                            });
                        }
                    });
                },
                get_available_attr_list: function (attrs, attribute_types, option) {
                    var available = '';
                    var tag_attributes = $.extend({}, attrs);
                    var attr_length = Object.keys(tag_attributes).length;
                    if('class' in tag_attributes && 'style' in attribute_obj && 'groups' in tag_attributes){
                        if(attr_length > 3){
                            delete tag_attributes['class'];
                            delete tag_attributes['style'];
                            delete tag_attributes['groups'];
                        }
                    }else if('class' in tag_attributes && 'style' in attribute_obj){
                        if(attr_length > 2){
                            delete tag_attributes['class'];
                            delete tag_attributes['style'];
                        }
                    }else if('style' in attribute_obj && 'groups' in tag_attributes){
                        if(attr_length > 2){
                            delete tag_attributes['style'];
                            delete tag_attributes['groups'];
                        }
                    }else if('class' in tag_attributes && 'groups' in tag_attributes){
                        if(attr_length > 2){
                            delete tag_attributes['class'];
                            delete tag_attributes['groups'];
                        }
                    }else if('class' in tag_attributes){
                        if(attr_length > 1){
                            delete tag_attributes['class'];
                        }
                    }else if('style' in tag_attributes){
                        if(attr_length > 1){
                            delete tag_attributes['style'];
                        }
                    }else if('groups' in tag_attributes){
                        if(attr_length > 1){
                            delete tag_attributes['groups'];
                        }
                    }
                    var list = null;
                    if(attr_length) {
                        _.each(tag_attributes, function (value, key) {
                            available += key + ',';
                            if(attribute_types[key]) {
                                var attr = JSON.parse(attribute_types[key]).with_attrs;
                                if (attr.length > 0) {
                                    available += attr + ',';
                                }
                            }
                        });
                        available = available.slice(0, -1).split(',');
                        var uniqueArray = function (arrArg) {
                            return arrArg.filter(function (elem, pos, arr) {
                                return arr.indexOf(elem) == pos;
                            });
                        };
                        list = uniqueArray(available);
                    }else{
                        list = attribute_types['class'];
                    }

                    $(option).removeClass('hide');
                    $(option).filter(function () {
                        if(list.indexOf($(this).html()) < 0){
                            $(this).addClass('hide');
                        }
                        if($(this).html() == ''){
                            $(this).removeClass('hide');
                        }
                    });

                    return list;
                }
            }).then(function (val, field, $dialog) {
                if($target_el.attr('t-foreach')){
                    var oldAttr = $target_el.attr('t-as');
                    var newAttr = attribute_obj['t-as'];
                    $target_el.html($target_el.html().split(oldAttr + '.').join(newAttr + '.'));
                }
                $target_el.each(function () {
                    var attributes = $.map(this.attributes, function (item) {
                        return item.name;
                    });
                    var tag = $(this);
                    $.each(attributes, function (i, item) {
                        tag.removeAttr(item);
                    });
                });

                for (var key in attribute_obj) {
                    $target_el.attr(key, attribute_obj[key]);
                }

                self.buildingBlock.getParent().rte.historyRecordUndo($target_el);
                if ($target_el.attr('t-field')) {
                    $target_el.html($target_el.attr('t-field'));
                }
                if ($target_el.attr('t-raw')) {
                    $target_el.html($target_el.attr('t-raw'));
                }
                if ($target_el.attr('t-esc')) {
                    $target_el.html('<b>Esc: </b>' + $target_el.attr('t-esc'));
                }
                if ($target_el.attr('t-set') && $target_el.attr('t-value')) {
                    var span_text = '<b> Set: </b>' + $target_el.attr('t-set') + ' <b> Value: </b>'+ $target_el.attr('t-value');
                    $target_el.html(span_text);
                }
            });
        }
    });
});
