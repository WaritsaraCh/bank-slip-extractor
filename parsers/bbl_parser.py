import re
from .base_parser import BaseParser

class BBLParser(BaseParser):
    def __init__(self):
        super().__init__(bank_name='bbl_bank')
        
    def parse(self, text):
        lines = self.clean_lines(text)
        fields = self.get_default_structure()
        
        found_from = False
        found_to = False
        
        for i, line in enumerate(lines):
            # ค้นหาวันที่และเวลา
            date_time_match = re.search(r'(\d{1,2}\s+[ก-์.]+\d{2}|\d{1,2}/\d{1,2}/\d{4}),?\s*(\d{2}:\d{2})', line)
            if date_time_match:
                fields['transaction']['date'] = date_time_match.group(1)
                fields['transaction']['time'] = date_time_match.group(2)

            # ค้นหาจำนวนเงิน
            if 'จํานวนเงิน' in line or 'จำนวนเงิน' in line or 'จำนวน' in line:
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
                fee_match = re.search(r'(\d+(?:,\d+)*\.?\d*)', line)
                if fee_match:
                    fields['transaction']['fee'] = fee_match.group(1)

            # ค้นหาข้อมูลบัญชีและชื่อ
            name_prefixes = ['นาย', 'นาง', 'น.ส.', 'นางสาว']
            if any(prefix in line for prefix in name_prefixes):
                account_pattern = r'\d+(?:[-.]?[x\d]+)*'
                
                if not found_from:
                    fields['from']['name'] = line
                    found_from = True

                    if i + 1 < len(lines) and re.search(account_pattern, lines[i + 1]):
                        fields['from']['account'] = lines[i + 1]
                    if i + 2 < len(lines):
                        fields['from']['bank'] = lines[i + 2]

                elif not found_to:
                    fields['to']['name'] = line
                    found_to = True
                    if i + 1 < len(lines) and re.search(account_pattern, lines[i + 1]):
                        fields['to']['account'] = lines[i + 1]
                    if i + 2 < len(lines):
                        fields['to']['bank'] = lines[i + 2]

            # ค้นหาเลขที่อ้างอิง
            if 'หมายเลขอ้างอิง' in line:
                ref_match = re.search(r'\d+', line)
                if ref_match:
                    fields['references']['ref_id'] = ref_match.group(0)
                else:
                    ref_match = re.search(r'\d+', lines[i+1])
                    if ref_match:
                        fields['references']['ref_id'] = ref_match.group(0)

            elif 'เลขที่อ้างอิง' in line:
                if i + 1 < len(lines):
                    trace_match = re.search(r'\d+', lines[i + 1])
                    if trace_match:
                        fields['references']['trace_id'] = trace_match.group(0)

        return fields