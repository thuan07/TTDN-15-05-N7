from odoo import models, fields

class Resource(models.Model):
    _name = 'resource_management'
    _description = 'Quản lý tài nguyên'

    name = fields.Char(string='Tên sản phẩm', required=True)
    quantity = fields.Integer(string='Số lượng sản phẩm')
    description = fields.Text(string='Mô tả')

    project_id = fields.Many2many('project_management', string='Dự án')
    task_id = fields.Many2many('project_task', string='Công việc')
