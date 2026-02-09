import re
from .base_parser import BaseParser

class SCBParser(BaseParser):
    def __init__(self):
        super().__init__(bank_name="scb_bank")

    def parse(self, text):
        lines = self.clean_lines(text)
        fields = self.get_default_structure()
        
        found_from = False
        found_to = False

        for i, line in enumerate(lines):
            # 1. วันที่และเวลา
            date_match = re.search(r'(\d{1,2}\s+พ\.[ก-์]+\.\s+\d{4})\s*-\s*(\d{2}:\d{2})', line)
            if date_match:
                fields['transaction']['date'] = date_match.group(1)
                fields['transaction']['time'] = date_match.group(2)

            # 2. จำนวนเงิน (ใช้ helper จากคลาสแม่)
            if 'จํานวนเงิน' in line:
                fields['transaction']['amount'] = self.extract_amount(line)

            # 3. ข้อมูลผู้โอน (จาก)
            if 'จาก' in line and not found_from:
                name_text = line.split('จาก')[-1].strip()
                # ปรับ Regex ให้รองรับชื่อไทย/อังกฤษ
                fields['from']['name'] = name_text
                if i + 1 < len(lines):
                    acc_match = re.search(r'([X\d-]+)', lines[i+1])
                    if acc_match:
                        fields['from']['account'] = acc_match.group(1)
                found_from = True

            # 4. ข้อมูลผู้รับ (ไปยัง)
            if 'ไปยัง' in line and not found_to:
                name_text = line.split('ไปยัง')[-1].strip()
                fields['to']['name'] = name_text
                if i + 1 < len(lines):
                    acc_match = re.search(r'([X\d-]+)', lines[i+1])
                    if acc_match:
                        fields['to']['account'] = acc_match.group(1)
                found_to = True

            # 5. รหัสอ้างอิง
            ref_pattern = r'(?:ร\s*ห\s*ั\s*ส|เ\s*ล\s*ข\s*ท\s*ี\s*่)\s*อ\s*้\s*า\s*ง\s*อ\s*ิ\s*ง\s*[:\-]?\s*([A-Z0-9\s]+)'
            ref_match = re.search(ref_pattern, line)
            if ref_match:
                fields['references']['ref_id'] = ref_match.group(1).strip()

        return fields