from odoo import models, api, fields, _
from odoo.exceptions import Warning, ValidationError


class TaskMaster(models.Model):
	_inherit = 'project.task'
	
	sub_task_type_ids = fields.Many2many('project.sub_task.type', 'project_sub_task_type_project_task_rel', 'project_task_id', 'project_sub_task_type_id', string="Sub Task Stages")

	@api.model
	def create(self, vals):
		if True:
			default_subtask = self.env['project.sub_task.type'].search([])
			if default_subtask:
				vals.update({'sub_task_type_ids': [(6,0, default_subtask.ids)]})
		res = super(TaskMaster, self).create(vals)
		return res

class ProjectSubTaskType(models.Model):
	_inherit = 'project.sub_task.type'

	task_ids = fields.Many2many('project.task', 'project_sub_task_type_project_task_rel', 'project_sub_task_type_id', 'project_task_id', string="Task Ids")

