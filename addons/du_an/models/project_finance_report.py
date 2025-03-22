from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProjectFinanceReport(models.Model):
    _name = 'project_finance_report'
    _description = 'Báo cáo tài chính dự án'

    project_id = fields.Many2one('project_management', string="Dự án", required=True, ondelete="cascade")
    report_date = fields.Date("Ngày báo cáo", required=True, default=fields.Date.today)
    budget = fields.Float("Ngân sách", related="project_id.budget", readonly=True)
    actual_cost = fields.Float("Chi phí thực tế", compute="_compute_actual_cost", store=True)
    profit = fields.Float("Lợi nhuận", compute="_compute_profit", store=True)
    status = fields.Selection([
        ('draft', 'Nháp'),
        ('approved', 'Đã duyệt'),
        ('paid', 'Đã thanh toán'),
        ('canceled', 'Hủy')
    ], string="Trạng thái", default='draft', readonly=True)

    @api.depends('project_id.invoice_ids.amount', 'project_id.invoice_ids.status')
    def _compute_actual_cost(self):
        for report in self:
            report.actual_cost = sum(
                invoice.amount for invoice in report.project_id.invoice_ids if invoice.status == 'approved'
            )

    @api.depends('budget', 'actual_cost')
    def _compute_profit(self):
        for report in self:
            report.profit = report.budget - report.actual_cost

    def action_approve(self):
        """Duyệt báo cáo tài chính"""
        for report in self:
            if report.status != 'draft':
                raise ValidationError("Chỉ có thể duyệt báo cáo ở trạng thái Nháp!")
            report.status = 'approved'
            report.project_id.status = 'approved'

    def action_paid(self):
        """Đánh dấu báo cáo đã thanh toán"""
        for report in self:
            if report.status != 'approved':
                raise ValidationError("Chỉ có thể thanh toán báo cáo đã được duyệt!")
            report.status = 'paid'
            report.project_id.status = 'completed'

    def action_cancel(self):
        """Hủy báo cáo tài chính"""
        for report in self:
            report.status = 'canceled'
            report.project_id.status = 'pending'