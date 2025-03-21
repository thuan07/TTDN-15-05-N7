from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProjectInvoice(models.Model):
    _name = 'project_invoice'
    _description = 'Hóa đơn dự án'

    project_id = fields.Many2one('project_management', string="Dự án", required=True, ondelete="cascade")
    date = fields.Date("Ngày hóa đơn", required=True, default=fields.Date.today)
    amount = fields.Float("Số tiền", required=True)
    description = fields.Text("Mô tả")
    status = fields.Selection([
        ('draft', 'Nháp'),
        ('waiting_approval', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('paid', 'Đã thanh toán'),
        ('canceled', 'Hủy')
    ], string="Trạng thái", default='waiting_approval', readonly=True)
    
    approved_by = fields.Many2one('res.users', string="Người duyệt", readonly=True)
    
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError('Số tiền phải lớn hơn 0!')

    @api.constrains('amount', 'status')
    def _check_budget(self):
        for invoice in self:
            if invoice.project_id and invoice.status == 'approved':
                if invoice.project_id.actual_cost + invoice.amount > invoice.project_id.budget:
                    raise ValidationError("Chi phí vượt quá ngân sách dự án!")

    def action_submit_for_approval(self):
        """Gửi yêu cầu duyệt"""
        for invoice in self:
            invoice.status = 'waiting_approval'

    def action_approve(self):
        """Duyệt hóa đơn"""
        for invoice in self:
            if not self.env.user.has_group('base.group_manager'):
                raise ValidationError("Bạn không có quyền duyệt hóa đơn!")
            invoice.status = 'approved'
            invoice.approved_by = self.env.user

    def action_paid(self):
        """Đánh dấu hóa đơn đã thanh toán"""
        for invoice in self:
            if invoice.status != 'approved':
                raise ValidationError("Hóa đơn phải được duyệt trước khi thanh toán!")
            invoice.status = 'paid'

    def action_cancel(self):
        """Hủy hóa đơn"""
        for invoice in self:
            invoice.status = 'canceled'