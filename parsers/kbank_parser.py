import re
from .base_parser import BaseParser

class KBankParser(BaseParser):
    def __init__(self):
        super().__init__(bank_name='kbank')
        
    def parse(self, text):
        lines = self.clean_lines(text)
        fields = self.get_default_structure()
        full_text = "\n".join(lines)
        
        # 1. เลขที่รายการ (Transaction ID)
        ref_match = re.search(r'เลข\s*ที่\s*ร\s*า\s*ย\s*ก\s*า\s*ร\s*[:\s]*(\d+)', full_text)
        if ref_match:
            fields['references']['ref_id'] = ref_match.group(1)

        # 2. จำนวนเงิน (Amount) - ปรับให้จับเฉพาะตัวเลขที่มีจุดทศนิยมและตามหลังคำว่าจำนวน
        amount_match = re.search(r'จำ\s*น\s*ว\s*น\s*[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))', full_text)
        if amount_match:
            fields['transaction']['amount'] = amount_match.group(1)

        # 3. วันที่และเวลา - รองรับรูปแบบ ก . พ . ที่มีช่องว่าง
        dt_pattern = r'(\d{1,2}\s+[ก-์\s\.]+\s+\d{2,4})\s+(\d{2}:\d{2})'
        dt_match = re.search(dt_pattern, full_text)
        if dt_match:
            fields['transaction']['date'] = dt_match.group(1).replace(" ", "")
            fields['transaction']['time'] = dt_match.group(2)

        # 4. ข้อมูลชื่อ - รองรับชื่อที่มีช่องว่างระหว่างตัวอักษร
        # แก้ไข Regex ให้รองรับสระและวรรณยุกต์ไทยที่หลากหลายขึ้น
        name_pattern = r'(?:นาย|นาง|น\s*\.\s*ส\s*\.|นางสาว)\s*([ก-์\s\.]+)'
        name_matches = re.findall(name_pattern, full_text)
        if len(name_matches) >= 1: fields['from']['name'] = name_matches[0].strip()
        if len(name_matches) >= 2: fields['to']['name'] = name_matches[1].strip()

        return fields