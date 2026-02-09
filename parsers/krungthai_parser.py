import re
from .base_parser import BaseParser

def KrungThaiParser(BaseParser):
    def __init__(self):
        super().__init__(bank_name='krungthai_bank')

    def parse(self, text):
        lines = self.clean_lines(text)
        fields = self.get_default_structure()

        found_from = False
        found_to = False

        for i, line in enumerate(lines):
            line = line.strip()  
            clean_line = re.sub(r'\s+', ' ', line.strip()) 

            
            # ค้นหาวันที่และเวลา
            if 'วันที่ทํารายการ' in line:
                # เพิ่ม print เพื่อ debug
                print(f"Line being processed: {clean_line}")
                # print(f"M: {}")
                date, time = clean_line.replace('วันที่ทํารายการ', '').strip().split('-')
                fields['transaction']['date'] = date
                fields['transaction']['time'] = time
                
                # ปรับ pattern ให้ยืดหยุ่นมากขึ้นและรองรับช่องว่างหลายรูปแบบ
                date_time_match = re.search(r'.*?(\d{1,2}\s*[ก-์]+\.?\s*\d{4})\s*-\s*(\d{1,2}:\d{2})\'?', clean_line)
                
                # แสดงผลลัพธ์การ match
                print(f"Match result: {date_time_match}")
                
                if date_time_match:
                    fields['transaction']['date'] = date_time_match.group(1)
                    fields['transaction']['time'] = date_time_match.group(2)

            # ค้นหาจำนวนเงิน
            if 'จํานวนเงิน' in line or 'จำนวนเงิ' in line or 'จำนวน' in line:
                amount_match = re.search(r'\d+(?:,\d+)*\.?\d*', line)
                if amount_match:
                    fields['transaction']['amount'] = amount_match.group(0)
                else:
                    if i + 1 < len(lines):
                        amount_match = re.search(r'\d+(?:,\d+)*\.?\d*', lines[i+1])
                        if amount_match:
                            fields['transaction']['amount'] = amount_match.group(0)

            # ค้นหาค่าธรรมเนียม
            if 'ค่าธรรมเนียม' in line:
                fee_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', line)
                if fee_match:
                    fields['transaction']['fee'] = fee_match.group(1)

            # ค้นหาข้อมูลบัญชีและชื่อ
            name_prefixes = ['นาย', 'นาง', 'น.ส.', 'นางสาว']
            if any(prefix in line for prefix in name_prefixes):
                account_pattern = r'[xX\d]+(?:[-\s]*[xX\d]+)*'
                
                if not found_from:
                    fields['from']['name'] = line
                    found_from = True
                    if i + 2 < len(lines) and re.search(account_pattern, lines[i + 2]):
                        fields['from']['account'] = lines[i + 2]

                    if i + 1 < len(lines):
                        fields['from']['bank'] = lines[i + 1]

                elif not found_to:
                    fields['to']['name'] = line
                    found_to = True
                    if i + 2 < len(lines) and re.search(account_pattern, lines[i + 2]):
                        fields['to']['account'] = lines[i + 2]

                    if i + 1 < len(lines):
                        fields['to']['bank'] = lines[i + 1]
                        
            # ค้นหาเลขที่อ้างอิง
            if 'รหัส' in line:
                ref_match = re.search(r'[A-Za-z0-9]+', line)
                if ref_match:
                    fields['references']['ref_id'] = ref_match.group(0)

        return fields