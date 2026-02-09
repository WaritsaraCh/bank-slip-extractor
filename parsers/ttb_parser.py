import re
from .base_parser import BaseParser

class TTBParser(BaseParser):
    def __init__(self):
        super().__init__(bank_name='ttb_bank')
        
    def parse(self, text):
        lines = self.clean_lines()
        fields = self.get_default_structure()
        
        found_from = False
        found_to = False

        for i, line in enumerate(lines):
            line = line.strip()

            # ค้นหาวันที่และเวลา
            date_match = re.search(r'(\d{1,2}\s+[ก-์]+\.?\d{2})\s+(\d{2}:\d{2})\s*น\.?', line)
            if date_match:
                fields['transaction']['date'] = date_match.group(1)
                fields['transaction']['time'] = date_match.group(2)

            # ค้นหาเลขที่อ้างอิง
            if 'ธหัสฮ้างอิง:' in line:
                ref_match = re.search(r'ธหัสฮ้างอิง:\s*([A-Za-z0-9]+)', line)
                if ref_match:
                    fields['references']['ref_id'] = ref_match.group(1)

            # ค้นหาจำนวนเงิน
            amount_match = re.search(r'^(\d+(?:,\d{3})*\.?\d{2})$', line)
            if amount_match:
                fields['transaction']['amount'] = amount_match.group(1)
                
            # ค้นหาค่าธรรมเนียม
            fee_match = re.search(r'ค่าธรรมเนียม\s*(\d+\.\d{2})', line)
            if fee_match:
                fields['transaction']['fee'] = fee_match.group(1)

            # ค้นหาข้อมูลผู้โอน (ttb)
            if 'ttb' in line.lower() and not found_from:
                # ย้อนกลับไปหาข้อมูลผู้โอน
                for j in range(i-1, max(-1, i-5), -1):
                    current = lines[j].strip()
                    if not current:
                        continue
                        
                    # ค้นหาเลขบัญชี
                    if re.search(r'[X\d-]+', current):
                        fields['from']['account'] = current
                    # ค้นหาชื่อ
                    elif re.search(r'[ก-์]', current):
                        fields['from']['name'] = current
                
                fields['from']['bank'] = 'ttb'
                found_from = True

            # ค้นหาข้อมูลผู้รับ
            if found_from and not found_to:
                # ย้อนกลับไปหาข้อมูลผู้รับ
                for j in range(i-1, max(-1, i-5), -1):
                    current = lines[j].strip()
                    if not current:
                        continue
                        
                    # ค้นหาเลขบัญชี
                    if re.search(r'[X\d-]+', current):
                        fields['to']['account'] = current
                    # ค้นหาชื่อ
                    elif re.search(r'[ก-์]', current):
                        fields['to']['name'] = current
                    # ค้นหาธนาคาร (ถ้ามี)
                    elif re.search(r'[A-Za-z]+', current):
                        fields['to']['bank'] = current
                
                found_to = True

        return fields