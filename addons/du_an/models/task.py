from odoo import models, fields

class ProjectTask(models.Model):
    _name = 'project.task'
    _description = 'Nhiệm vụ trong dự án'

    name = fields.Char(string="Tên nhiệm vụ", required=True)
    project_id = fields.Many2one('project.management', string="Dự án liên quan")
    assigned_to = fields.Many2one('res.users', string="Người phụ trách")
    employee_id = fields.Many2one("project.employee", string="Nhân viên thực hiện")
    deadline = fields.Date(string="Hạn chót")
    status = fields.Selection([
        ('todo', 'Cần làm'),
        ('in_progress', 'Đang làm'),
        ('done', 'Hoàn thành')
    ], string="Trạng thái", default='todo')
