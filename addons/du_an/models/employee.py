from odoo import models, fields

class Employee(models.Model):
    _name = "project.employee"
    _description = "Quản lý Nhân viên Dự án"

    name = fields.Char(string="Tên nhân viên", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Số điện thoại")
    position = fields.Char(string="Chức vụ")

    project_ids = fields.Many2many("project.management", string="Dự án tham gia")
    task_ids = fields.One2many("project.task", "employee_id", string="Nhiệm vụ được giao")
