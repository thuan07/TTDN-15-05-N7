from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Resource(models.Model):
    _name = 'resource_management'
    _description = 'Quản lý tài nguyên'

    name = fields.Char(string='Tên sản phẩm', required=True)
    quantity = fields.Integer(string='Số lượng sản phẩm')
    description = fields.Text(string='Mô tả')

    project_id = fields.Many2many('project_management', string='Dự án', ondelete='cascade')
    task_id = fields.Many2many('project_task', string='Công việc', ondelete='cascade')

    purchase_order_ids = fields.One2many('purchase_order', 'resource_id', string="Yêu cầu mua hàng liên quan")
    supplier_id = fields.Many2one('supplier_management', string='Nhà cung cấp', ondelete='set null')
    state = fields.Selection([
        ('waiting_approval', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ], string="Trạng thái", default='waiting_approval')

    @api.model
    def create(self, vals):
        """ Khi thêm tài nguyên, nếu số lượng dưới ngưỡng, tự động tạo yêu cầu mua hàng """
        resource = super(Resource, self).create(vals)
        if resource.quantity < 10:  # Nếu số lượng nhỏ hơn 10
            resource._create_purchase_order()
        return resource

    def _create_purchase_order(self):
        """ Tự động tạo Yêu cầu mua hàng khi số lượng tài nguyên thấp """
        for resource in self:
            supplier = resource.supplier_id
            if not supplier:
                raise ValidationError("Tài nguyên phải có nhà cung cấp để tạo đơn hàng!")

            purchase_order = self.env['purchase_order'].create({
                'name': self.env['ir.sequence'].next_by_code('purchase.order') or 'New',
                'supplier_id': supplier.id,
                'order_date': fields.Date.today(),
                'state': 'waitting',
                'resource_id': resource.id,  # Liên kết tài nguyên với đơn hàng
                'order_line_ids': [(0, 0, {
                    'product_id': resource.id,
                    'quantity': 20,  # Mua thêm 20 sản phẩm (tuỳ chỉnh)
                    'unit_price': 0,  # Cập nhật sau
                })]
            })

            resource.state = 'waiting_approval'  # Đánh dấu tài nguyên là chờ duyệt

    def action_approve(self):
        """ Duyệt tài nguyên """
        for resource in self:
            resource.state = 'approved'

    def action_reject(self):
        """ Từ chối tài nguyên """
        for resource in self:
            resource.state = 'rejected'
