from odoo import models, fields, api

class ProjectTask(models.Model):
    _name = 'project_task'
    _description = 'Nhiệm vụ trong dự án'

    name = fields.Char("Tên nhiệm vụ", required=True)
    project_id = fields.Many2one('project_management', string="Dự án")
    employee_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    deadline = fields.Date("Hạn chót")
    status = fields.Selection([
        ('pending', 'Đang chờ'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành')
    ], string="Trạng thái", default='pending')

    log_ids = fields.One2many('project_log', 'task_id', string="Nhật ký hoạt động")

    @api.onchange('status')
    def _onchange_status(self):
        if self.status:
            self.env['project_log'].create({
                'task_id': self.id,
                'action': f"Trạng thái nhiệm vụ thay đổi thành {self.status}",
            })