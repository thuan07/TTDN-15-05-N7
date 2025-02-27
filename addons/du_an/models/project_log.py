from odoo import models, fields, api

class ProjectLog(models.Model):
    _name = 'project_log'
    _description = 'Nhật ký hoạt động dự án'
    _order = 'date desc'

    project_id = fields.Many2one('project_management', string="Dự án", ondelete='cascade')
    task_id = fields.Many2one('project_task', string="Nhiệm vụ", ondelete='cascade')
    user_id = fields.Many2one('res.users', string="Người thực hiện", default=lambda self: self.env.user)
    date = fields.Datetime("Thời gian", default=fields.Datetime.now)
    action = fields.Char("Hành động")
