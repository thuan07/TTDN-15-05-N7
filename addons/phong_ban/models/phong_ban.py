from odoo import models, fields, api

class PhongBan(models.Model):
    _name = 'phong_ban'
    _description = 'Phòng Ban'

    ten_phong_ban = fields.Char("Tên Phòng Ban", required=True)
    mo_ta = fields.Text("Mô tả")