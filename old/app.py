from flask import Flask, render_template, request, jsonify
import cv2
import pytesseract
import os
import re
import numpy as np
from skimage.metrics import structural_similarity as ssim
from collections import defaultdict

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
TEMPLATE_FOLDER = 'static/images/bank_templates'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# สร้างโฟลเดอร์สำหรับเก็บไฟล์ที่อัพโหลด
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_bank(image_path):
    # อ่านรูปภาพที่อัพโหลด
    uploaded_img = cv2.imread(image_path)
    uploaded_img = cv2.resize(uploaded_img, (300, 500))  # ปรับขนาดให้เท่ากัน
    uploaded_gray = cv2.cvtColor(uploaded_img, cv2.COLOR_BGR2GRAY)

    best_match = None
    highest_similarity = -1

    # เปรียบเทียบกับ template ของแต่ละธนาคาร
    for template_file in os.listdir(TEMPLATE_FOLDER):
        if template_file.endswith(('.jpg', '.png', '.jpeg')):
            template_path = os.path.join(TEMPLATE_FOLDER, template_file)
            template_img = cv2.imread(template_path)
            template_img = cv2.resize(template_img, (300, 500))  # ปรับขนาดให้เท่ากัน
            template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

            # คำนวณความเหมือน
            similarity = ssim(uploaded_gray, template_gray)

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = template_file.split('.')[0]  # ชื่อธนาคารจากชื่อไฟล์

    return best_match, highest_similarity

def extract_fields_by_bank(text, bank_name):
    # โครงสร้างข้อมูลที่จะส่งกลับ
    fields = {
        "bank": bank_name,
        "transaction": {
            "date": "",
            "time": "",
            "amount": "",
            "fee": ""
        },
        "from": {
            "name": "",
            "account": "",
            "bank": ""
        },
        "to": {
            "name": "",
            "account": "",
            "bank": ""
        },
        "references": {
            "ref_id": "",
            "trace_id": ""
        }
    }

    # แยกข้อความเป็นบรรทัด
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    print(lines)

    # เลือกฟังก์ชันการแยกข้อมูลตามธนาคาร
    if bank_name == "bangkok_bank":
        fields = extract_bangkok_bank(lines, fields)
    elif bank_name == "krungthai_bank":
        fields = extract_krungthai(lines, fields) 
    elif bank_name == "scb_bank":
        fields = extract_scb(lines, fields)
        print(fields)
    elif bank_name == "gsb_bank":
        fields = extract_gsb(lines, fields)
        print(fields)
    elif bank_name == "ttb_bank":
        fields = extract_ttb(lines, fields)
        print(fields)
    # elif bank_name == "kasikorn":
    #     fields = extract_kasikorn(lines, fields)
    # เพิ่มธนาคารอื่นๆ ตามต้องการ

    return fields

def extract_bangkok_bank(lines, fields):
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

def extract_krungthai(lines, fields):
    found_from = False
    found_to = False

    for i, line in enumerate(lines):
        line = line.strip()  # ลบช่องว่างหน้าและหลังบรรทัด
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

def extract_scb(lines, fields):
    found_from = False
    found_to = False

    for i, line in enumerate(lines):
        line = line.strip()

        # ค้นหาวันที่และเวลา
        date_match = re.search(r'(\d{1,2}\s+พ\.[ก-์]+\.\s+\d{4})\s*-\s*(\d{2}:\d{2})', line)
        if date_match:
            fields['transaction']['date'] = date_match.group(1)
            fields['transaction']['time'] = date_match.group(2)

        # ค้นหาเลขที่อ้างอิง
        if 'รหัสอ้างอิง:' in line:
            ref_match = re.findall(r'[A-Za-z0-9]+', line)
            if len(ref_match) >= 2:
                fields['references']['ref_id'] = f"{ref_match[0]} {ref_match[1]}"

        # ค้นหาข้อมูลบัญชีและชื่อ
        if 'จาก' in line and not found_from:
            # แยกข้อความหลังคำว่า "จาก"
            name_text = line.split('จาก')[-1].strip()
            name_match = re.search(r'©?\s*([a-zA-Z0-9\.\s]+)?([ก-์\s]+)', name_text)
            if name_match:
                prefix = name_match.group(1).strip() if name_match.group(1) else ""
                name = name_match.group(2).strip()
                fields['from']['name'] = f"{prefix} {name}".strip()
                found_from = True
                
                # ค้นหาเลขบัญชีในบรรทัดถัดไป
                if i + 1 < len(lines):
                    account_match = re.search(r'([X\d-]+)', lines[i + 1])
                    if account_match:
                        fields['from']['account'] = account_match.group(1)

        if 'ไปยัง' in line and not found_to:
            # แยกข้อความหลังคำว่า "ไปยัง"
            name_text = line.split('ไปยัง')[-1].strip()
            name_match = re.search(r'([0-9a-zA-Z\.\s]+)?([ก-์\s]+)', name_text)
            if name_match:
                prefix = name_match.group(1).strip() if name_match.group(1) else ""
                name = name_match.group(2).strip()
                fields['to']['name'] = f"{prefix} {name}".strip()
                found_to = True
                
                # ค้นหาเลขบัญชีในบรรทัดถัดไป
                if i + 1 < len(lines):
                    account_match = re.search(r'([X\d-]+)', lines[i + 1])
                    if account_match:
                        fields['to']['account'] = account_match.group(1)

        # ค้นหาจำนวนเงิน
        if 'จํานวนเงิน' in line:
            amount_match = re.search(r'(\d+(?:\.\d{2})?)', line)
            if amount_match:
                fields['transaction']['amount'] = amount_match.group(1)

    return fields

def extract_gsb(lines, fields):
    found_from = False
    found_to = False

    for i, line in enumerate(lines):
        line = line.strip()

        # ค้นหาวันที่และเวลา
        date_match = re.search(r'(\d{1,2}\s+พ\.[ก-์]+\.?\d{4})\s+(\d{2}:\d{2})', line)
        if date_match:
            fields['transaction']['date'] = date_match.group(1)
            fields['transaction']['time'] = date_match.group(2)

        # ค้นหาเลขที่อ้างอิง
        if 'รหัสอ้างอิง:' in line:
            ref_match = re.search(r'รหัสอ้างอิง:\s*([A-Za-z0-9]+)', line)
            if ref_match:
                fields['references']['ref_id'] = ref_match.group(1)

        # ค้นหาจำนวนเงินและค่าธรรมเนียม
        amount_match = re.search(r'^(\d+(?:,\d{3})*\.?\d{2})$', line)
        if amount_match:
            fields['transaction']['amount'] = amount_match.group(1)
            
        fee_match = re.search(r'^(\d+\.\d{2})\s*ค่าธรรมเนียม', line)
        if fee_match:
            fields['transaction']['fee'] = fee_match.group(1)

          # ค้นหาข้อมูลผู้โอน (จาก)
        if line == 'จาก' and not found_from:
            name_parts = []
            current_line = i + 1
            
            # รวบรวมส่วนของชื่อจนกว่าจะเจอคำว่า "ธนาคาร"
            while current_line < len(lines) and 'ธนาคาร' not in lines[current_line]:
                name_line = lines[current_line].strip()
                if name_line:  # ถ้าไม่ใช่บรรทัดว่าง
                    name_line = re.sub(r'^[@๑]\s*', '', name_line)
                    name_parts.append(name_line)
                current_line += 1
            
            if name_parts:
                fields['from']['name'] = ' '.join(name_parts).strip()
            
            # ค้นหาธนาคารและเลขบัญชี
            if current_line < len(lines):
                fields['from']['bank'] = lines[current_line].strip()
                if current_line + 1 < len(lines):
                    account_line = lines[current_line + 1].strip()
                    if re.search(r'[X\d-]+', account_line):
                        fields['from']['account'] = account_line
            found_from = True

        # ค้นหาข้อมูลผู้รับ (ถึง)
        if line == 'ถึง' and not found_to:
            current_line = i + 1
            found_name = False
            
            # ค้นหาชื่อ, ประเภท, และเลขบัญชี
            while current_line < len(lines):
                current = lines[current_line].strip()
                
                # ข้ามบรรทัดว่าง
                if not current:
                    current_line += 1
                    continue
                
                # ถ้าเป็นชื่อ (มี น.ส., นาย, นาง)
                if not found_name and re.search(r'[ก-์]\s*\.?\s*[ก-์]+', current):
                    current = re.sub(r'^[@๑]\s*', '', current)
                    fields['to']['name'] = current.strip()
                    found_name = True
                
                # ถ้าเป็นประเภท (พร้อมเพย์)
                elif 'พร้อมเพย์' in current:
                    fields['to']['type'] = current.strip()
                
                # ถ้าเป็นเลขบัญชี
                elif re.search(r'[X\d-]+', current):
                    fields['to']['account'] = current.strip().rstrip(',')
                
                current_line += 1
            found_to = True

    return fields

def extract_ttb(lines, fields):
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

def process_image(image_path):
    # ตรวจสอบธนาคาร
    bank_name, similarity = detect_bank(image_path)
    
    # อ่านรูปภาพ
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # สกัดข้อความ
    text = pytesseract.image_to_string(thresh, lang='tha+eng')
    
    # แยกข้อมูลตามธนาคาร
    fields = extract_fields_by_bank(text, bank_name)
    
    return fields, text, bank_name, similarity

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
            
        if file and allowed_file(file.filename):
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)
            
            fields, raw_text, bank_name, similarity = process_image(filename)
            
            return jsonify({
                'fields': fields,
                'raw_text': raw_text,
                'bank_name': bank_name,
                'similarity': similarity,
                'image_path': filename
            })
            
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)