from odoo import models, fields

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