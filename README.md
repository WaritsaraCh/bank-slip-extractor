## 🛠 Tech Stack

* **Frontend:** React.js (with Tailwind CSS for styling)
* **OCR Engine:** Tesseract.js / Google Vision API
* **State Management:** React Hooks (useState, useEffect)
* **Icons & UI:** Lucide React / Heroicons

## 🚀 Installation & Setup

Follow these steps to get the project running locally:

### 1. Clone the repository
```bash
git clone https://github.com/your-username/bank-slip-extractor.git
cd bank-slip-extractor
```

### 2. Install dependencies
```bash
npm install
# or
yarn install
```

### 3. Environment Configuration (Optional)
If you are using an external API for OCR, create a `.env` file in the root directory and add your keys:
```env
REACT_APP_OCR_API_KEY=your_api_key_here
```

### 4. Run the application
```bash
npm start
# or
yarn start
```
The app will be available at `http://localhost:3000`.