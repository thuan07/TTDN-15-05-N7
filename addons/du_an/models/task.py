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
    resource_ids = fields.Many2many('resource_management', string="Danh sách tài nguyên")
    log_ids = fields.One2many('project_log', 'task_id', string="Nhật ký hoạt động")

    progress = fields.Float("Tiến độ (%)", compute="_compute_progress", store=True)

    @api.depends('status')
    def _compute_progress(self):
        for task in self:
            if task.status == 'pending':
                task.progress = 0
            elif task.status == 'in_progress':
                task.progress = 50
            elif task.status == 'done':
                task.progress = 100

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        if 'status' in vals or 'progress' in vals:
            for task in self:
                if task.project_id:
                    task.project_id._compute_progress()
        return res
    
    def action_approve(self):
        for task in self:
            task.status = 'in_progress'
            if task.project_id:  # Kiểm tra nếu project_id tồn tại
                self.env['project_log'].create({
                    'task_id': task.id,
                    'project_id': task.project_id.id,
                    'action': f"Nhiệm vụ {task.name} đã được xác nhận."
                })

    def action_complete(self):
        for task in self:
            task.status = 'done'
            task.progress = 100
            self.env['project_log'].create({
                'task_id': task.id,
                'project_id': task.project_id.id,
                'action': f"Nhiệm vụ {task.name} đã hoàn thành."
            })