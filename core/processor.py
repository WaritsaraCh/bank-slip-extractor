import cv2
import pytesseract
import re
import os

class SlipProcessor:
    def __init__(self, tesseract_cmd=None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
    def get_processed_image(self, img):
       
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        return thresh_otsu

    def clean_ocr_text(self, text):
       
        text = re.sub(r'(?<=[ก-์])\s+(?=[ก-์])', '', text)
        text = re.sub(r'ํ\s+า', 'ำ', text) # แก้ไข จํ านวน -> จำนวน
        
        corrections = {
            "จ ํ า น ว น": "จำนวน", "จํ านวน": "จำนวน",
            "เล ข ท ี ่ ร า ย ก า ร": "เลขที่รายการ",
            "ค ่ า ธร ร ม เน ี ย ม": "ค่าธรรมเนียม",
            "โอ น เง ิ น": "โอนเงิน", "ส ํ า เร ็ จ": "สำเร็จ"
        }
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
        return text

    def process_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None: return ""
        
        # ต้องใช้ภาพที่ผ่าน Adaptive Threshold เพื่อความแม่นยำ
        processed = self.get_processed_image(img)
        raw_text = pytesseract.image_to_string(processed, lang='tha+eng')
        
        return self.clean_ocr_text(raw_text)

    def detect_bank(self, text):
        text_lower = text.lower().replace(" ", "")
        if 'scb' in text_lower or 'ไทยพาณิชย์' in text_lower: return "scb_bank"
        if 'กสิกร' in text_lower or 'kbank' in text_lower or 'k+' in text_lower: return "kbank"
        return "unknown"