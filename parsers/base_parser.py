import re

class BaseParser:
    def __init__(self, bank_name):
        self.bank_name = bank_name

    def get_default_structure(self):
        """โครงสร้างมาตรฐานที่ทุกธนาคารต้องส่งกลับ"""
        return {
            "bank": self.bank_name,
            "transaction": {"date": "", "time": "", "amount": "0", "fee": "0"},
            "from": {"name": "", "account": "", "bank": ""},
            "to": {"name": "", "account": "", "bank": ""},
            "references": {"ref_id": "", "trace_id": ""}
        }

    def clean_lines(self, text):
        """Helper สำหรับทำความสะอาดข้อความเบื้องต้น"""
        return [line.strip() for line in text.split('\n') if line.strip()]

    def extract_amount(self, text):
        """Helper สำหรับสกัดตัวเลขและแปลงเป็น Float"""
        match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        if match:
            return float(match.group(1).replace(',', ''))
        return 0.0

    def parse(self, text):
        """ฟังก์ชันหลักที่ลูกๆ ต้องเอาไปเขียน Logic เอง (Override)"""
        raise NotImplementedError("Subclasses must implement parse() method")