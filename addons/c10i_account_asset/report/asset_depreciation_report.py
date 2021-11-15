from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from xlsxwriter import workbook
from datetime import datetime

class AssetDepreciationXlsx(ReportXlsx):

	def generate_xlsx_report(self, workbook, data, report):
		jan_dep=feb_dep=mar_dep=apr_dep=may_dep=jun_dep=jul_dep=aug_dep=sep_dep=okt_dep=nov_dep=des_dep=0
		for obj in report:
			report_date = obj.as_of_date
			date = datetime.strptime(report_date, "%Y-%m-%d")
			sheet = workbook.add_worksheet(report_date[:31])
			bold = workbook.add_format({
				'bold': True,
				'font_size': 14,
				})
			bold_border = workbook.add_format({
				'bold':True,
				'border':1,
				'align':'center',
				'bg_color': 'yellow',
				})
			sheet.write(0, 0, obj.company_id.name, bold)
			sheet.write(1, 0, "Asset Depreciation", bold)
			sheet.write(2, 0, report_date, bold)
			merge_format = workbook.add_format({
				'align': 'center',
				'valign': 'vcenter',
				'border': 1,
				'bold': True,
				'bg_color': 'yellow',
				})
			sheet.set_column('A:A', 4)
			sheet.set_column('B:B', 5)
			sheet.set_column('C:D', 15)
			sheet.set_column('F:I', 16)
			sheet.set_column('V:X', 15)
			sheet.merge_range('A5:A6','No.', merge_format)
			sheet.merge_range('B5:C6', "Asset", merge_format)
			sheet.merge_range('D5:D6', "Vendor", merge_format)
			sheet.merge_range('E5:E6', "PO Date", merge_format)
			sheet.merge_range('F5:F6', "Acq. Value", merge_format)
			sheet.merge_range('G5:G6', "Depr. Number", merge_format)
			sheet.merge_range('H5:H6', "Accum. Depr. "+str(date.year-1), merge_format)
			sheet.merge_range('I5:I6', "Book Value", merge_format)
			sheet.merge_range('J5:U5', "Depreciation", merge_format)
			sheet.write('J6', 'Janaury', bold_border)
			sheet.write('K6', 'February', bold_border)
			sheet.write('L6', 'March', bold_border)
			sheet.write('M6', 'April', bold_border)
			sheet.write('N6', 'May', bold_border)
			sheet.write('O6', 'June', bold_border)
			sheet.write('P6', 'July', bold_border)
			sheet.write('Q6', 'August', bold_border)
			sheet.write('R6', 'September', bold_border)
			sheet.write('S6', 'Oktober', bold_border)
			sheet.write('T6', 'November', bold_border)
			sheet.write('U6', 'December', bold_border)
			sheet.merge_range('V5:V6', "Total Depr.", merge_format)
			sheet.merge_range('W5:W6', "Accum. Depr.", merge_format)
			sheet.merge_range('X5:X6', "Current Book Value", merge_format)
			asset = self.env['account.asset.asset'].search([])
			first_line = 6
			no = 0
			start_year = "01-01-"+str(date.year)
			data_format = workbook.add_format({
				'font_size': 7,
				'border':1,
				})
			data_format_currency = workbook.add_format({
				'font_size': 7,
				'num_format': '#,##0.00',
				'border':1,
				})
			for val in asset:
				first_line+=1
				no+=1
				for asset_line in val.depreciation_line_ids:
					if start_year < asset_line.depreciation_date < report_date:
						if asset_line.id == val.depreciation_line_ids[0].id:
							prev_asset_line = asset_line
							prev_dep = 0
							book_value = val.value
						else:
							prev_asset_line =asset_line.id-1
							prev_asset = self.env['account.asset.depreciation.line'].search([('id','=', prev_asset_line)])
							prev_dep = prev_asset.depreciated_value 
							book_value = prev_asset.remaining_value
						sheet.write('A'+str(first_line),no, data_format)
						sheet.write('B'+str(first_line),val.code if val.code != False else "", data_format)
						sheet.write('C'+str(first_line),val.name, data_format)
						sheet.write('D'+str(first_line),val.partner_id.name if val.partner_id.name != False else "", data_format)
						sheet.write('E'+str(first_line),val.date, data_format)
						sheet.write('F'+str(first_line),val.value, data_format_currency)
						sheet.write('G'+str(first_line),val.method_period, data_format)
						sheet.write('H'+str(first_line),prev_dep, data_format_currency)
						sheet.write('I'+str(first_line),book_value, data_format_currency)
						month_dep = datetime.strptime(asset_line.depreciation_date, "%Y-%m-%d").month
						if month_dep == 1:
							jan_dep = asset_line.amount
						elif month_dep == 2:
							feb_dep = asset_line.amount
						elif month_dep == 3:
							mar_dep = asset_line.amount
						elif month_dep == 4:
							apr_dep = asset_line.amount
						elif month_dep == 5:
							may_dep = asset_line.amount
						elif month_dep == 6:
							jun_dep = asset_line.amount
						elif month_dep == 7:
							jul_dep = asset_line.amount
						elif month_dep == 8:
							aug_dep = asset_line.amount
						elif month_dep == 9:
							sep_dep = asset_line.amount
						elif month_dep == 10:
							okt_dep = asset_line.amount
						elif month_dep == 11:
							nov_dep = asset_line.amount
						elif month_dep == 12:
							des_dep = asset_line.amount
						book_value_now = asset_line.remaining_value
				sheet.write('J'+str(first_line), jan_dep, data_format_currency)
				sheet.write('K'+str(first_line), feb_dep, data_format_currency)
				sheet.write('L'+str(first_line), mar_dep, data_format_currency)
				sheet.write('M'+str(first_line), apr_dep, data_format_currency)
				sheet.write('N'+str(first_line), may_dep, data_format_currency)
				sheet.write('O'+str(first_line), jun_dep, data_format_currency)
				sheet.write('P'+str(first_line), jul_dep, data_format_currency)
				sheet.write('Q'+str(first_line), aug_dep, data_format_currency)
				sheet.write('R'+str(first_line), sep_dep, data_format_currency)
				sheet.write('S'+str(first_line), okt_dep, data_format_currency)
				sheet.write('T'+str(first_line), nov_dep, data_format_currency)
				sheet.write('U'+str(first_line), des_dep, data_format_currency)
				sheet.write_formula('V'+str(first_line), '=SUM(J'+str(first_line)+',U'+str(first_line)+')', data_format_currency)
				sheet.write_formula('W'+str(first_line), '=SUM(H'+str(first_line)+',V'+str(first_line)+')', data_format_currency)
				sheet.write('X'+str(first_line), book_value_now, data_format_currency)


AssetDepreciationXlsx('report.asset_depreciation_report',
			'wizard.asset.depreciation.report')