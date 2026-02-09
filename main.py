import os
from flask import Flask, render_template, request, jsonify
from parsers.factory import ParserFactory 
from core.processor import SlipProcessor

app = Flask(__name__)

processor = SlipProcessor(tesseract_cmd=r"D:\Tesseract-OCR\tesseract.exe")

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400


    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filename)

    try:
        cleaned_text = processor.process_image(filename)
        bank_name = processor.detect_bank(cleaned_text)
        
        parser = ParserFactory.get_parser(bank_name)
        
        if parser:
            result_data = parser.parse(cleaned_text)
            status = "success"
        else:
            status = "unknown_bank"
        
            result_data = {
                "transaction": {"date": "-", "time": "-", "amount": "-", "fee": "-"},
                "from": {"name": "-", "account": "-", "bank": "-"},
                "to": {"name": "-", "account": "-", "bank": "-"},
                "references": {"ref_id": "-", "trace_id": "-"},
            }

        return jsonify({
            'status': status,
            'bank_name': bank_name,
            'similarity': 0,
            'data': result_data,  
            'raw_text': cleaned_text,
            'image_path': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
   
    app.run(debug=True, host='0.0.0.0', port=8080)