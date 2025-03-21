from odoo import models, fields, api

class Project(models.Model):
    _name = 'project_management'
    _description = 'Quản lý dự án'

    name = fields.Char(string="Tên dự án", required=True)
    description = fields.Text(string="Mô tả")
    start_date = fields.Date(string="Ngày bắt đầu")
    end_date = fields.Date(string="Ngày kết thúc")
    status = fields.Selection([
        ('pending', 'Đang chờ'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành')
    ], string="Trạng thái", default='pending')

    budget = fields.Float(string="Ngân sách dự án")
    actual_cost = fields.Float(string="Chi phí thực tế", compute="_compute_actual_cost", store=True)
    invoice_ids = fields.One2many('project_invoice', 'project_id', string="Danh sách hóa đơn")
    finance_report_ids = fields.One2many('project_finance_report', 'project_id', string="Báo cáo tài chính")
    
    employee_ids = fields.Many2many("nhan_vien", string="Nhân viên tham gia",)
    task_ids = fields.Many2many("project_task", string="Danh sách nhiệm vụ")
    log_ids = fields.One2many('project_log', 'project_id', string="Nhật ký hoạt động")

    progress = fields.Float("Tiến độ (%)", compute="_compute_progress", store=True)

    @api.depends('task_ids.progress')
    def _compute_progress(self):
        for project in self:
            if project.task_ids:
                total_progress = sum(task.progress for task in project.task_ids)
                project.progress = total_progress / len(project.task_ids)
            else:
                project.progress = 0
    def write(self, vals):
        if 'status' in vals:
            for project in self:
                status_mapping = {
                'pending': 'Đang chờ',
                'in_progress': 'Đang thực hiện',
                'completed': 'Hoàn thành'
                }
                new_status = status_mapping.get(vals['status'], 'Không xác định')
                self.env['project_log'].create({
                    'project_id': project.id,
                    'action': f"Trạng thái dự án {project.name} thay đổi thành {new_status}",
                })
        return super(Project, self).write(vals)

    @api.depends('invoice_ids.amount', 'invoice_ids.status')
    def _compute_actual_cost(self):
        for project in self:
            project.actual_cost = sum(invoice.amount for invoice in project.invoice_ids if invoice.status == 'approved')

    @api.depends('invoice_ids')
    def _compute_progress(self):
        for project in self:
            project.progress = (sum(invoice.amount for invoice in project.invoice_ids if invoice.status == 'paid') / project.budget) * 100 if project.budget else 0