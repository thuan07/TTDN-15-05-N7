from odoo import api, models, fields

class ProjectFinanceReport(models.Model):
    _name = 'project_finance_report'
    _description = 'Báo cáo tài chính dự án'

    project_id = fields.Many2one('project_management', string="Dự án", required=True, ondelete='cascade')
    report_date = fields.Date("Ngày báo cáo", default=fields.Date.today)
    budget = fields.Float(related='project_id.budget', string="Ngân sách")
    actual_cost = fields.Float(related='project_id.actual_cost', string="Chi phí thực tế")
    profit = fields.Float("Lợi nhuận", compute="_compute_profit", store=True)

    @api.depends('budget', 'actual_cost')
    def _compute_profit(self):
        for report in self:
            report.profit = report.budget - report.actual_cost