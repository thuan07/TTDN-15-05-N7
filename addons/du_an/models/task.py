from odoo import models, fields, api

class ProjectTask(models.Model):
    _name = 'project_task'
    _description = 'Nhiệm vụ trong dự án'

    name = fields.Char("Tên nhiệm vụ", required=True)
    project_id = fields.Many2one('project_management', string="Dự án")
    employee_id = fields.Many2many('nhan_vien', string="Nhân viên phụ trách")
    deadline = fields.Date("Hạn chót")
    status = fields.Selection([
        ('pending', 'Đang chờ'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành')
    ], string="Trạng thái", default='pending')

    log_ids = fields.One2many('project_log', 'task_id', string="Nhật ký hoạt động")

    def write(self, vals):
        """ Ghi log khi trạng thái nhiệm vụ thay đổi """
        if 'status' in vals:
            for project in self:
                status_mapping = {
                'draft': 'Nháp',
                'in_progress': 'Đang thực hiện',
                'completed': 'Hoàn thành'
            }
            for task in self:
                new_status = status_mapping.get(vals['status'], 'Không xác định')
                self.env['project_log'].create({
                    'task_id': task.id,
                    'project_id': task.project_id.id,  # Ghi cả project_id vào log
                    'action': f"Trạng thái nhiệm vụ thay đổi thành {vals['new_status']}",
                })
        return super(ProjectTask, self).write(vals)