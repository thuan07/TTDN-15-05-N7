from odoo import models, fields, api

class PhongBan(models.Model):
    _name = 'phong.ban'
    _description = 'Phòng Ban'
    _rec_name = 'ten_phong_ban'

    ten_phong_ban = fields.Char(string="Tên Phòng Ban", required=True)
    mo_ta = fields.Text(string="Mô tả")
    truong_phong_id = fields.Many2one('res.users', string="Trưởng Phòng")
    nhan_vien_ids = fields.One2many('res.users', 'phong_ban_id', string="Nhân Viên")
