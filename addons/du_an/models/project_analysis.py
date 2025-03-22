from odoo import models, fields, api

class ProjectProgressReport(models.Model):
    _name = 'project_progress_report'
    _description = 'Báo cáo tiến độ dự án'

    project_id = fields.Many2one('project_management', string="Dự án", required=True)
    report_date = fields.Date("Ngày báo cáo", default=fields.Date.today)
    progress = fields.Float("Tiến độ (%)", related='project_id.progress', store=True)
    description = fields.Text("Mô tả")

    @api.model
    def get_kpi_data(self):
        """Tính toán các chỉ số KPI cho dashboard"""
        projects = self.env['project_management'].search([])
        total_budget = sum(project.budget for project in projects)
        total_actual_cost = sum(project.actual_cost for project in projects)
        total_profit = total_budget - total_actual_cost
        return {
            'total_budget': total_budget,
            'total_actual_cost': total_actual_cost,
            'total_profit': total_profit
        }