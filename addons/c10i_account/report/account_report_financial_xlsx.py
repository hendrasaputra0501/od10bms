from odoo import api, fields, models
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from xlsxwriter.utility import xl_rowcol_to_cell
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class ReportFinancial(ReportXlsx):
    def add_dict(self, src_dict, input_dict):
        res = src_dict.copy()
        res.update(input_dict)
        return res

    def _compute_account_balance(self, accounts, context=None):
        """ compute the balance, debit and credit for the provided accounts
        """
        context = {} if context is None else context
        mapping = {
            'init_balance': "COALESCE(SUM(init_balance), 0) as init_balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
            'balance': "COALESCE(SUM(init_balance),0) + COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
        }
        mapping1 = {
            'init_balance': "SUM(0) as init_balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        mapping2 = {
            'init_balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as init_balance",
            'debit': "SUM(0) as debit",
            'credit': "SUM(0) as credit",
        }

        if not (context.get('date_from') or context.get('date_from_cmp')):
            dont_show_initial_bal = " 1=0 AND "
        else:
            dont_show_initial_bal = " account_id is not NULL AND "
        
        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            # account_bl
            account_bl = accounts.filtered(lambda x: x.user_type_id.include_initial_balance)
            account_pl = accounts.filtered(lambda x: not x.user_type_id.include_initial_balance)
            if account_bl:
                ctx = context.copy()
                ctx.update({'initial_bal': True})
                tables1, where_clause1, where_params1 = self.env['account.move.line'].with_context(context)._query_get()
                tables2, where_clause2, where_params2 = self.env['account.move.line'].with_context(ctx)._query_get()
                tables1 = tables1.replace('"', '') if tables1 else "account_move_line"
                tables2 = tables2.replace('"', '') if tables2 else "account_move_line"
                wheres1 = [""]
                wheres2 = [""]
                if where_clause1.strip():
                    wheres1.append(where_clause1.strip())
                if where_clause2.strip():
                    wheres2.append(where_clause2.strip())
                filters1 = " AND ".join(wheres1)
                filters2 = " AND ".join(wheres2)
                request = "SELECT id, " + ', '.join(mapping.values()) + \
                    " FROM ( " \
                        "SELECT account_id as id, " + ', '.join(mapping1.values()) + \
                           " FROM " + tables1 + \
                           " WHERE account_id IN %s " \
                                + filters1 + \
                           " GROUP BY account_id" \
                        " UNION ALL " \
                        "SELECT account_id as id, " + ', '.join(mapping2.values()) + \
                           " FROM " + tables2 + \
                           " WHERE " +dont_show_initial_bal+ \
                                " account_id IN %s " \
                                + filters2 + \
                           " GROUP BY account_id" \
                        ") sub " \
                    "GROUP BY id"
                params = (tuple(accounts._ids),) + tuple(where_params1) + (tuple(accounts._ids),) + tuple(where_params2)
                self.env.cr.execute(request, params)
                for row in self.env.cr.dictfetchall():
                    res[row['id']] = row
            if account_pl:
                tables1, where_clause1, where_params1 = self.env['account.move.line'].with_context(context)._query_get()
                ctx2 = context.copy()
                if ctx2.get('pl_date_start'):
                    ctx2.update({'date_from': ctx2['pl_date_start'],
                        'date_to': (datetime.strptime(ctx2['date_from'],DF) + relativedelta(days=-1)).strftime(DF)})
                tables2, where_clause2, where_params2 = self.env['account.move.line'].with_context(ctx2)._query_get()
                tables1 = tables1.replace('"', '') if tables1 else "account_move_line"
                tables2 = tables2.replace('"', '') if tables2 else "account_move_line"
                wheres1 = [""]
                wheres2 = [""]
                if where_clause1.strip():
                    wheres1.append(where_clause1.strip())
                if where_clause2.strip():
                    wheres2.append(where_clause2.strip())
                filters1 = " AND ".join(wheres1)
                filters2 = " AND ".join(wheres2)
                request = "SELECT id, " + ', '.join(mapping.values()) + \
                    " FROM ( " \
                        "SELECT account_id as id, " + ', '.join(mapping1.values()) + \
                           " FROM " + tables1 + \
                           " WHERE account_id IN %s " \
                                + filters1 + \
                           " GROUP BY account_id" \
                        " UNION ALL " \
                        "SELECT account_id as id, " + ', '.join(mapping2.values()) + \
                           " FROM " + tables2 + \
                           " WHERE " +dont_show_initial_bal+ \
                                " account_id IN %s " \
                                + filters2 + \
                           " GROUP BY account_id" \
                        ") sub " \
                    "GROUP BY id"
                params = (tuple(accounts._ids),) + tuple(where_params1) + (tuple(accounts._ids),) + tuple(where_params2)
                self.env.cr.execute(request, params)
                for row in self.env.cr.dictfetchall():
                    res[row['id']] = row
        return res

    def _generate_report_balance(self, wb, sheet, row, style, data, objects, reports, skip_write=False):
        parent_sum_rows = []
        sum_rows = []
        temp = {'balance': 0.0, 'balance_comp': 0.0}
        
        # Column Header Row
        cell_format = self.add_dict(style['xlsx_cell'],self.add_dict(style['arial'],self.add_dict(style['bold'],self.add_dict(style['border_bottom'],style['border_top']))))
        c_hdr_cell_style = wb.add_format(cell_format)
        c_hdr_cell_style_decimal = wb.add_format(self.add_dict(self.add_dict(cell_format, style['right']),style['integer']))
        
        # cell styles for ledger lines
        ll_cell_format = self.add_dict(style['xlsx_cell'],self.add_dict(style['arial'],style['wrap']))
        ll_cell_style = wb.add_format(ll_cell_format)
        ll_cell_style_decimal = wb.add_format(self.add_dict(self.add_dict(ll_cell_format,style['right']),style['integer']))

        for report in sorted(reports, key=lambda x: (x.sequence, x.id)):
            if report.type in ('accounts','account_type'):
                if report.type == 'account_type':
                    accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                else:
                    accounts = report.account_ids
                result_account = self._compute_account_balance(accounts, context=data['form'].get('used_context',{}))
                if objects.enable_filter:
                    result_account_comp = self._compute_account_balance(accounts, context=data['form'].get('comparison_context',{}))
                if skip_write:
                    for account in accounts:
                        temp['balance'] += result_account.get(account.id,{}).get('balance',0.0)*report.sign
                        if objects.enable_filter:
                            temp['balance_comp'] += result_account_comp.get(account.id,{}).get('balance',0.0)*report.sign
                else:
                    row_start = row_end = row
                    for account in accounts:
                        sheet.write_string(row, 1, account.code, ll_cell_style)
                        sheet.write_string(row, 2, account.name, ll_cell_style)
                        sheet.write_number(row, 3, result_account.get(account.id,{}).get('balance',0.0)*report.sign, ll_cell_style_decimal)
                        if objects.enable_filter:
                            sheet.write_number(row, 4, result_account_comp.get(account.id,{}).get('balance',0.0)*report.sign, ll_cell_style_decimal)
                        row_end = row
                        row+=1
                    sheet.write_string(row, 1, "", c_hdr_cell_style)
                    sheet.write_string(row, 2, report.name, c_hdr_cell_style)
                    without_sum = False
                    if row_start == row_end:
                        without_sum = True
                    sheet.write_formula(row, 3, "=D%s"%str(row_start+1) if without_sum else "=SUM(D%s:D%s)"%(str(row_start+1), str(row_end+1)) , c_hdr_cell_style_decimal)
                    if objects.enable_filter:
                        sheet.write_formula(row, 4, "=E%s"%str(row_start+1) if without_sum else "=SUM(E%s:E%s)"%(str(row_start+1), str(row_end+1)) , c_hdr_cell_style_decimal)
                    sum_rows.append(row)
                    row+=1
            elif report.type == 'account_report':
                # to reset the temp subtotal into 0. this is only use type Account Report
                temp = {'balance': 0.0, 'balance_comp': 0.0}
                
                row, current_total, child_sum_rows = self._generate_report_balance(wb, sheet, row, style, data, objects, report.account_report_id, skip_write=True)
                temp['balance'] += current_total['balance']*report.sign
                if objects.enable_filter:
                    temp['balance_comp'] += current_total['balance_comp']*report.sign

                sheet.write_string(row, 1, "", ll_cell_style)
                sheet.write_string(row, 2, report.name, ll_cell_style)
                sheet.write_number(row, 3, current_total['balance']*report.sign, ll_cell_style_decimal)
                if objects.enable_filter:
                    sheet.write_number(row, 4, current_total['balance_comp']*report.sign, ll_cell_style_decimal)
                sum_rows.append(row)
                row+=1
            elif report.type == 'sum':
                if report.show_view_label:
                    sheet.write_string(row, 1, "", c_hdr_cell_style)
                    sheet.write_string(row, 2, report.name, c_hdr_cell_style)
                    sheet.write_string(row, 3, "", c_hdr_cell_style)
                    sheet.write_string(row, 4, "", c_hdr_cell_style)
                    row+=1
                row, current_total, child_sum_rows = self._generate_report_balance(wb, sheet, row, style, data, objects, report.children_ids, skip_write=skip_write)
                temp['balance'] += current_total['balance']*report.sign
                if objects.enable_filter:
                    temp['balance_comp'] += current_total['balance_comp']*report.sign
            
                if child_sum_rows:
                    sheet.write_string(row, 1, "", c_hdr_cell_style)
                    sheet.write_string(row, 2, report.name, c_hdr_cell_style)
                    without_sum = False
                    if len(child_sum_rows) == 1:
                        without_sum = True
                    sheet.write_formula(row, 3, "=D%s"%str(child_sum_rows[0]+1) if without_sum else "=SUM(%s)"%(",".join(map(lambda x: 'D%s'%str(x+1), child_sum_rows))) , c_hdr_cell_style_decimal)
                    if objects.enable_filter:
                        sheet.write_formula(row, 4, "=E%s"%str(child_sum_rows[0]+1) if without_sum else "=SUM(%s)"%(",".join(map(lambda x: 'E%s'%str(x+1), child_sum_rows))) , c_hdr_cell_style_decimal)
                    sum_rows.append(row)
                    row+=1

        return row, temp, sum_rows

    def _generate_report_complete(self, wb, sheet, row, style, data, objects, reports, skip_write=False):
        parent_sum_rows = []
        sum_rows = []
        temp = {'init_balance':0.0, 'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
        
        # Column Header Row
        cell_format = self.add_dict(style['xlsx_cell'],self.add_dict(style['arial'],self.add_dict(style['bold'],self.add_dict(style['border_bottom'],style['border_top']))))
        c_hdr_cell_style = wb.add_format(cell_format)
        c_hdr_cell_style_decimal = wb.add_format(self.add_dict(self.add_dict(cell_format, style['right']),style['integer']))
        
        # cell styles for ledger lines
        ll_cell_format = self.add_dict(style['xlsx_cell'],self.add_dict(style['arial'],style['wrap']))
        ll_cell_style = wb.add_format(ll_cell_format)
        ll_cell_style_decimal = wb.add_format(self.add_dict(self.add_dict(ll_cell_format,style['right']),style['integer']))
        
        for report in sorted(reports, key=lambda x: (x.sequence, x.id)):
            if report.type in ('accounts','account_type'):
                if report.type == 'account_type':
                    accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                else:
                    accounts = report.account_ids
                result_account = self._compute_account_balance(accounts, context=data['form'].get('used_context',{}))
                if skip_write:
                    for account in accounts:
                        temp['init_balance'] += result_account.get(account.id,{}).get('init_balance',0.0)*report.sign
                        if report.sign==1:
                            temp['debit'] += result_account.get(account.id,{}).get('debit',0.0)
                            temp['credit'] += result_account.get(account.id,{}).get('credit',0.0)
                        else:
                            temp['credit'] += result_account.get(account.id,{}).get('debit',0.0)
                            temp['debit'] += result_account.get(account.id,{}).get('credit',0.0)
                        temp['balance'] += result_account.get(account.id,{}).get('balance',0.0)*report.sign
                else:
                    row_start = row_end = row
                    for account in accounts:
                        sheet.write_string(row, 1, account.code, ll_cell_style)
                        sheet.write_string(row, 2, account.name, ll_cell_style)
                        sheet.write_number(row, 3, result_account.get(account.id,{}).get('init_balance',0.0)*report.sign, ll_cell_style_decimal)
                        if report.sign==1:
                            sheet.write_number(row, 4, result_account.get(account.id,{}).get('debit',0.0), ll_cell_style_decimal)
                            sheet.write_number(row, 5, result_account.get(account.id,{}).get('credit',0.0), ll_cell_style_decimal)
                        else:
                            sheet.write_number(row, 4, result_account.get(account.id,{}).get('credit',0.0), ll_cell_style_decimal)
                            sheet.write_number(row, 5, result_account.get(account.id,{}).get('debit',0.0), ll_cell_style_decimal)
                        sheet.write_number(row, 6, result_account.get(account.id,{}).get('balance',0.0)*report.sign, ll_cell_style_decimal)
                        row_end = row
                        row+=1
                    sheet.write_string(row, 1, "", c_hdr_cell_style)
                    sheet.write_string(row, 2, report.name, c_hdr_cell_style)
                    without_sum = False
                    if row_start == row_end:
                        without_sum = True
                    sheet.write_formula(row, 3, "=D%s"%str(row_start+1) if without_sum else "=SUM(D%s:D%s)"%(str(row_start+1), str(row_end+1)) , c_hdr_cell_style_decimal)
                    sheet.write_formula(row, 4, "=E%s"%str(row_start+1) if without_sum else "=SUM(E%s:E%s)"%(str(row_start+1), str(row_end+1)) , c_hdr_cell_style_decimal)
                    sheet.write_formula(row, 5, "=F%s"%str(row_start+1) if without_sum else "=SUM(F%s:F%s)"%(str(row_start+1), str(row_end+1)) , c_hdr_cell_style_decimal)
                    sheet.write_formula(row, 6, "=G%s"%str(row_start+1) if without_sum else "=SUM(G%s:G%s)"%(str(row_start+1), str(row_end+1)) , c_hdr_cell_style_decimal)
                    sum_rows.append(row)
                    row+=1
            elif report.type == 'account_report':
                # to reset the temp subtotal into 0. this is only use type Account Report
                temp = {'init_balance':0.0, 'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
                
                row, current_total, child_sum_rows = self._generate_report_complete(wb, sheet, row, style, data, objects, report.account_report_id, skip_write=True)
                temp['init_balance'] += current_total['init_balance']*report.sign
                if report.sign == 1:
                    temp['debit'] += current_total['debit']
                    temp['credit'] += current_total['credit']
                else:
                    temp['debit'] += current_total['credit']
                    temp['credit'] += current_total['debit']
                temp['balance'] += current_total['balance']*report.sign

                sheet.write_string(row, 1, "", ll_cell_style)
                sheet.write_string(row, 2, report.name, ll_cell_style)
                sheet.write_number(row, 3, current_total['init_balance']*report.sign, ll_cell_style_decimal)
                if report.sign == 1:
                    sheet.write_number(row, 4, current_total['debit'], ll_cell_style_decimal)
                    sheet.write_number(row, 5, current_total['credit'], ll_cell_style_decimal)
                else:
                    sheet.write_number(row, 4, current_total['credit'], ll_cell_style_decimal)
                    sheet.write_number(row, 5, current_total['debit'], ll_cell_style_decimal)
                sheet.write_number(row, 6, current_total['balance']*report.sign, ll_cell_style_decimal)
                sum_rows.append(row)
                row+=1
                # if child_sum_rows:
                    # sum_rows.extend(child_sum_rows)
            elif report.type == 'sum':
                if report.show_view_label:
                    sheet.write_string(row, 1, "", c_hdr_cell_style)
                    sheet.write_string(row, 2, report.name, c_hdr_cell_style)
                    sheet.write_string(row, 3, "", c_hdr_cell_style)
                    sheet.write_string(row, 4, "", c_hdr_cell_style)
                    sheet.write_string(row, 5, "", c_hdr_cell_style)
                    sheet.write_string(row, 6, "", c_hdr_cell_style)
                    row+=1
                row, current_total, child_sum_rows = self._generate_report_complete(wb, sheet, row, style, data, objects, report.children_ids, skip_write=skip_write)
                temp['init_balance'] += current_total['init_balance']*report.sign
                if report.sign == 1:
                    temp['debit'] += current_total['debit']
                    temp['credit'] += current_total['credit']
                else:
                    temp['debit'] += current_total['credit']
                    temp['credit'] += current_total['debit']
                temp['balance'] += current_total['balance']*report.sign
                # if child_sum_rows:
                #   sum_rows.extend(child_sum_rows)

                if child_sum_rows:
                    sheet.write_string(row, 1, "", c_hdr_cell_style)
                    sheet.write_string(row, 2, report.name, c_hdr_cell_style)
                    without_sum = False
                    if len(child_sum_rows) == 1:
                        without_sum = True
                    sheet.write_formula(row, 3, "=D%s"%str(child_sum_rows[0]+1) if without_sum else "=SUM(%s)"%(",".join(map(lambda x: 'D%s'%str(x+1), child_sum_rows))) , c_hdr_cell_style_decimal)
                    sheet.write_formula(row, 4, "=E%s"%str(child_sum_rows[0]+1) if without_sum else "=SUM(%s)"%(",".join(map(lambda x: 'E%s'%str(x+1), child_sum_rows))) , c_hdr_cell_style_decimal)
                    sheet.write_formula(row, 5, "=F%s"%str(child_sum_rows[0]+1) if without_sum else "=SUM(%s)"%(",".join(map(lambda x: 'F%s'%str(x+1), child_sum_rows))) , c_hdr_cell_style_decimal)
                    sheet.write_formula(row, 6, "=G%s"%str(child_sum_rows[0]+1) if without_sum else "=SUM(%s)"%(",".join(map(lambda x: 'G%s'%str(x+1), child_sum_rows))) , c_hdr_cell_style_decimal)
                    sum_rows.append(row)
                    row+=1

        return row, temp, sum_rows

    def generate_xlsx_report(self, workbook, data, objects):

        def date_to_string(xdate_from, xdate_to, periodic=False):
            date_from = datetime.strptime(xdate_from, DF)
            date_to = datetime.strptime(xdate_to, DF)
            same_year = same_month = one_month = last_day = False
            if date_from.year==date_to.year:
                same_year = True
            if date_from.month==date_to.month:
                same_month = True
                if date_from.day==1 and (date_from + relativedelta(day=31)).strftime(DF)==xdate_to:
                    one_month = True
            if (date_to + relativedelta(day=31)).strftime(DF)==xdate_to:
                last_day = True

            if periodic:
                if one_month:
                    res = date_from.strftime("%B %y")
                elif same_month:
                    res = "%s-%s %s %s"%(date_from.strftime("%d"), date_to.strftime("%d"), date_from.strftime("%B"), date_from.strftime("%y"))
                elif same_year:
                    res = "%s-%s"%(date_from.strftime("%d/%m"), date_to.strftime("%d/%m %y"))
                else:
                    res = "%s-%s"%(date_from.strftime(DF), date_to.strftime(DF))
            else: # AS OF DATE
                if last_day:
                    res = "As of %s"%date_to.strftime("%B %y")
                else:
                    res = "As of %s"%date_to.strftime("%d %B %y")
            return res

        # Filter Date
        current_date = datetime.now().strftime(DF)
        if not objects.date_from and not objects.date_to:
            date_from = datetime.now().strftime("%Y-01-01")
            date_from = current_date
            date_year = datetime.now().strftime("%Y-01-01")
        elif not objects.date_from:
            date_from = datetime.now().strftime("%Y-01-01")
            date_to = objects.date_to
            date_year = datetime.strptime(objects.date_to, DF).strftime("%Y-01-01")
        elif not objects.date_to:
            date_from = objects.date_from
            date_to = datetime.now().strftime("%Y-01-01")
            date_year = datetime.strptime(objects.date_from, DF).strftime("%Y-01-01")
        else:
            date_from = objects.date_from
            date_to = objects.date_to
            date_year = datetime.strptime(objects.date_from, DF).strftime("%Y-01-01")

        if objects.enable_filter:
            if objects.filter_cmp == 'filter_no':
                date_from_cmp = datetime.now().strftime("%Y-01-01")
                date_to_cmp = current_date
                date_year_cmp = datetime.now().strftime("%Y-01-01")
            else:
                date_from_cmp = objects.date_from_cmp
                date_to_cmp = objects.date_to_cmp
                date_year_cmp = datetime.strptime(objects.date_from_cmp, DF).strftime("%Y-01-01")

        account_report = objects.account_report_id
        data = {}
        data['form'] = objects.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = objects._build_contexts(data)
        used_context.update({'pl_date_start': date_year})
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')

        if objects.enable_filter:
            data2 = {}
            data2['form'] = objects.read(['account_report_id', 'date_from_cmp', 'date_to_cmp', 'journal_ids', 'filter_cmp', 'target_move'])[0]
            for field in ['account_report_id']:
                if isinstance(data2['form'][field], tuple):
                    data2['form'][field] = data2['form'][field][0]
            comparison_context = objects._build_comparison_context(data2)
            comparison_context.update({'pl_date_start': date_year_cmp})
            data['form']['comparison_context'] = comparison_context
            data['form'].update(objects.read(['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter', 'target_move'])[0])
        
        row = 0
        xlsx_style = {
            'arial': {'font_name': 'Arial', 'font_size': 10},
            'xlsx_title': {'bold': True, 'font_size':12, 'align': 'left'},
            'xlsx_cell': {'font_size':8},
            'borders_all': {'border':1},
            'border_top': {'top':1},
            'border_bottom': {'bottom':1},
            'bold': {'bold':True},
            'underline': {'underline': True},
            'italic': {'italic': True},

            'left': {'align': 'left'},
            'center': {'align': 'center'},
            'right': {'align': 'right'},
            'top': {'valign': 'top'},
            'vcenter': {'valign': 'center'},
            'bottom': {'valign': 'bottom'},
            'wrap': {'text_wrap':True},
            
            'fill_blue': {'pattern':1, 'fg_color':'#99fff0'},
            'fill_grey': {'pattern':1, 'fg_color':'#e0e0e0'},
            'fill': {'pattern': 1, 'fg_color': '#ffff99'},

            'decimal': {'num_format':'#,##0.00;-#,##0.00;-'},
            'decimal4': {'num_format':'#,##0.0000;-#,##0.0000;-'},
            'percentage': {'num_format': '0%'},
            'percentage2': {'num_format': '0.00%'},
            'integer': {'num_format':'#,##0;-#,##0;-'},
            'date': {'num_format': 'dd-mmm-yy'},
            'date2': {'num_format': 'dd/mm/yy'},
        }

        sheet_name = account_report.name
        sheet = workbook.add_worksheet(sheet_name[:31])
        sheet.set_portrait()
        sheet.set_footer('&R&6&"Courier New,Italic"Page &P of &N', {'margin': 0.25})
        
        date_string = date_to_string(date_from, date_to)
        cell_style = workbook.add_format(self.add_dict(xlsx_style['arial'],xlsx_style['xlsx_title']))
        sheet.write_string(0, 1, objects.company_id.name, cell_style)
        sheet.write_string(1, 1, account_report.name, cell_style)
        sheet.write_string(1, 6, "Printed on: "+datetime.now().strftime('%d/%m/%Y'), cell_style)
        sheet.write_string(2, 1, "Period: "+datetime.strptime(objects.date_from,'%Y-%m-%d').strftime('%d/%m/%Y')+' - '+datetime.strptime(objects.date_to,'%Y-%m-%d').strftime('%d/%m/%Y'), cell_style)
        sheet.write_string(3, 1, "", cell_style)
        row = 4
        if objects.debit_credit:
            sheet.write_string(row, 1, "Filter: %s"%date_string, cell_style)
        sheet.freeze_panes(row+1,0)

        cell_format = self.add_dict(xlsx_style['xlsx_cell'],self.add_dict(xlsx_style['arial'],xlsx_style['bold']))
        cell_style = workbook.add_format(cell_format)
        cell_style_center = workbook.add_format(self.add_dict(cell_format,xlsx_style['center']))

        if objects.enable_filter or not objects.debit_credit:
            column_width = [0, 12, 45, 17, 17]
            for col_pos in range(1,5):
                sheet.set_column(col_pos, col_pos, column_width[col_pos])

            sheet.write_string(row, 1, "Acount Code", cell_style)
            sheet.write_string(row, 2, "Account Name", cell_style)
            sheet.write_string(row, 3, date_string, cell_style_center)
            if objects.enable_filter:
                date_string2 = date_to_string(date_from_cmp, date_to_cmp)
                sheet.write_string(row, 4, date_string2, cell_style_center)
            next_cols = 5
            row+=1
            res = self._generate_report_balance(workbook, sheet, row, xlsx_style, data, objects, account_report)
        else:
            column_width = [0, 6, 45, 17, 15, 15, 17]
            for col_pos in range(1,7):
                sheet.set_column(col_pos, col_pos, column_width[col_pos])

            sheet.write_string(row, 1, "Acount Code", cell_style)
            sheet.write_string(row, 2, "Account Name", cell_style)
            sheet.write_string(row, 3, "Initial Bal", cell_style)
            sheet.write_string(row, 4, "Debit", cell_style)
            sheet.write_string(row, 5, "Credit", cell_style)
            sheet.write_string(row, 6, "Closing Bal", cell_style)
            next_cols = 7
            row+=1
            res = self._generate_report_complete(workbook, sheet, row, xlsx_style, data, objects, account_report)
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)
        sheet.print_area(0, 0, res[0], next_cols) #print area of selected cell
        sheet.set_paper(9)  # set A4 as page format
        sheet.center_horizontally()
        pages_horz = 1 # wide
        pages_vert = 0 # as long as necessary
        sheet.fit_to_pages(pages_horz, pages_vert)
        pass

ReportFinancial('report.report_financial_xlsx', 'accounting.report')