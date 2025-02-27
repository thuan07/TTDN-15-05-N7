from odoo import models, fields, api

class Project(models.Model):
    _name = 'project_management'
    _description = 'Quản lý dự án'

    name = fields.Char(string="Tên dự án", required=True)
    description = fields.Text(string="Mô tả")
    start_date = fields.Date(string="Ngày bắt đầu")
    end_date = fields.Date(string="Ngày kết thúc")
    status = fields.Selection([
        ('draft', 'Nháp'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành')
    ], string="Trạng thái", default='draft')

    employee_ids = fields.Many2many("nhan_vien", string="Nhân viên tham gia")
    task_ids = fields.One2many("project_task", "project_id", string="Danh sách nhiệm vụ")

    # Thống kê nhiệm vụ
    total_tasks = fields.Integer("Tổng số nhiệm vụ", compute="_compute_task_counts", store=True)
    done_tasks = fields.Integer("Số nhiệm vụ hoàn thành", compute="_compute_task_counts", store=True)
    progress = fields.Float("Tiến độ (%)", compute="_compute_progress", store=True)

    @api.depends('task_ids.status')
    def _compute_task_counts(self):
        for project in self:
            tasks = project.task_ids
            project.total_tasks = len(tasks)
            project.done_tasks = len(tasks.filtered(lambda t: t.status == 'done'))

    @api.depends('total_tasks', 'done_tasks')
    def _compute_progress(self):
        for project in self:
            if project.total_tasks > 0:
                project.progress = (project.done_tasks / project.total_tasks) * 100
            else:
                project.progress = 0

    log_ids = fields.One2many('project_log', 'project_id', string="Nhật ký hoạt động")

    @api.onchange('status')
    def _onchange_status(self):
        if self.status:
            self.env['project_log'].create({
                'project_id': self.id,
                'action': f"Trạng thái dự án thay đổi thành {self.status}",
            })