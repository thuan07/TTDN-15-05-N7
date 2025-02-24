from odoo import models, fields, api

class ChucVu(models.Model):
    _name = 'chung_chi'
    _description = 'Bảng chứa thông tin chứng chỉ'

    ma_chuc_vu = fields.Char("Mã chứng chỉ", required=True)
    ten_chuc_vu = fields.Char("Tên chứng chỉ")
# lich_su_cong_tac_ids = fields.One2many("lich_su_cong_tac", inverse_name= "chuc_vu_id", string="Lịch sử công tác")