from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _name = 'purchase_order'
    _description = 'Yêu cầu mua hàng'

    name = fields.Char(string="Mã đơn hàng", required=True, copy=False, default='New')
    project_id = fields.Many2one('project_management', string="Dự án", required=True)
    supplier_id = fields.Many2one('supplier_management', string="Nhà cung cấp", required=True)
    order_date = fields.Date(string="Ngày đặt hàng", default=fields.Date.today)
    state = fields.Selection([
        ('waitting', 'Đang chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('delivered', 'Đã giao hàng'),
        ('canceled', 'Đã hủy')
    ], string="Trạng thái", default='waitting')
    
    order_line_ids = fields.One2many('purchase_order_line', 'order_id', string="Chi tiết đơn hàng")
    total_amount = fields.Float(string="Tổng tiền", compute="_compute_total_amount", store=True)
    
    resource_id = fields.Many2one('resource_management', string="Tài nguyên liên quan")  # Thêm trường này

    @api.depends('order_line_ids.subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.subtotal for line in order.order_line_i)

    def action_confirm(self):
        for order in self:
            if not order.order_line_ids:
                raise ValidationError("Đơn hàng phải có ít nhất một dòng chi tiết!")
            order.state = 'confirmed'
            if order.resource_id:
                order.resource_id.action_approve() 

    def action_deliver(self):
        for order in self:
            if order.state != 'confirmed':
                raise ValidationError("Chỉ có thể giao hàng cho đơn hàng đã xác nhận!")
            order.state = 'delivered'

    def action_cancel(self):
        for order in self:
            order.state = 'canceled'
            if order.resource_id:
                order.resource_id.action_reject()


class PurchaseOrderLine(models.Model):
    _name = 'purchase_order_line'
    _description = 'Chi tiết đơn hàng'

    order_id = fields.Many2one('purchase_order', string="Đơn hàng", required=True, ondelete='cascade')
    product_id = fields.Many2one('resource_management', string="Sản phẩm", required=True)
    quantity = fields.Integer(string="Số lượng", required=True, default=1)
    unit_price = fields.Float(string="Đơn giá", required=True)
    subtotal = fields.Float(string="Thành tiền", compute="_compute_subtotal", store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price


class Supplier(models.Model):
    _name = 'supplier_management'
    _description = 'Quản lý Nhà cung cấp'

    name = fields.Char(string="Tên nhà cung cấp", required=True)
    contact = fields.Char(string="Thông tin liên hệ")
    address = fields.Text(string="Địa chỉ")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Số điện thoại")
    product_ids = fields.One2many('resource_management', 'supplier_id', string="Sản phẩm cung cấp")


class MaterialInventory(models.Model):
    _name = 'material_inventory'
    _description = 'Tồn kho vật tư'

    product_id = fields.Many2one('resource_management', string="Sản phẩm", required=True)
    project_id = fields.Many2one('project_management', string="Dự án", required=True)
    quantity = fields.Integer(string="Số lượng tồn kho", required=True)
    location = fields.Char(string="Vị trí lưu trữ")