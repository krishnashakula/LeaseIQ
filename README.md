# PDF Extractor Web App

A simple, robust web application for extracting structured data from PDF documents using AI-powered marker library. Features a clean Three.js animated UI and one-click deployment to Render.

## ✨ Features

- 🚀 **Fast PDF Processing** - Powered by marker-pdf library
- 🎨 **Beautiful UI** - Three.js particle background with clean interface
- 📤 **Drag & Drop Upload** - Easy file uploads
- 📊 **Structured Output** - JSON formatted extraction results
- 💾 **Download Results** - Export processed data
- ☁️ **Cloud Ready** - Deploy to Render in minutes

## 🏗️ Architecture

```
├── backend/          # Flask API
│   ├── app.py       # Main API server
│   ├── requirements.txt
│   └── Procfile     # Render deployment
│
├── frontend/        # Static HTML/CSS/JS
│   └── index.html   # Single page app with Three.js
│
└── render.yaml      # Render deployment config
```

## 🚀 Quick Start (Local Development)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
```

Backend runs on `http://localhost:5000`

### Frontend Setup

```bash
cd frontend

# Serve static files (Python 3)
python -m http.server 8080

# OR use any static server
# npx serve .
```

Frontend runs on `http://localhost:8080`

## 📦 Deploy to Render

### Method 1: One-Click Deploy (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml` and deploy both services

### Method 2: Manual Deploy

**Backend:**
1. Go to Render Dashboard → "New Web Service"
2. Connect your repository
3. Settings:
   - **Name**: `pdf-extractor-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Root Directory**: `backend`

**Frontend:**
1. Go to Render Dashboard → "New Static Site"
2. Connect your repository
3. Settings:
   - **Name**: `pdf-extractor-frontend`
   - **Publish Directory**: `frontend`
4. Add environment variable:
   - `API_URL` = `<your-backend-url>`

## 🔧 Configuration

### Backend Environment Variables (Optional)

```bash
PORT=5000              # Server port (auto-set by Render)
```

### Frontend API Configuration

The frontend auto-detects the API URL:
- **Local**: Uses `http://localhost:5000`
- **Production**: Uses same domain (static site proxies to backend)

To customize, edit `frontend/index.html`:
```javascript
const API_URL = 'https://your-backend.onrender.com';
```

## 📝 API Endpoints

### Health Check
```
GET /health
Response: {"status": "healthy", "service": "PDF Extractor API"}
```

### Upload PDF
```
POST /api/upload
Body: multipart/form-data with 'file' field
Response: {
  "job_id": "uuid",
  "filename": "doc.pdf",
  "status": "success",
  "data": { ... extracted content ... }
}
```

### Download Result
```
GET /api/download/<job_id>
Response: JSON file download
```

### List Results
```
GET /api/results
Response: [ { "job_id": "...", "filename": "...", "status": "..." }, ... ]
```

## 🎯 Usage

1. Open the web app
2. Click "Choose PDF File" or drag & drop a PDF
3. Wait for processing (shows animated loader)
4. View structured JSON output
5. Download results if needed

## 🛠️ Tech Stack

- **Backend**: Flask, marker-pdf, gunicorn
- **Frontend**: Vanilla HTML/CSS/JS, Three.js
- **Deployment**: Render
- **Storage**: Local filesystem (ephemeral on Render)

## ⚡ Performance

- Processing speed: ~1-5 seconds per page (depends on content)
- Supports multi-page PDFs
- No file size limit (Render has 500MB request limit)

## 🔒 Security Notes

- Files are automatically deleted after processing
- Each job gets unique ID
- CORS enabled for frontend access
- No authentication (add if needed for production)

## 📋 Requirements

- Python 3.11+
- Modern browser with WebGL support
- Internet connection (for Three.js CDN)

## 🐛 Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (needs 3.11+)
- Install dependencies: `pip install -r requirements.txt`

**Frontend shows CORS error:**
- Ensure backend has `Flask-CORS` installed
- Check API_URL in frontend code

**Render deployment fails:**
- Verify `requirements.txt` has all dependencies
- Check build logs in Render dashboard
- Ensure Python version matches `runtime.txt`

**PDF processing fails:**
- Check PDF is not encrypted
- Ensure PDF is valid format
- Check backend logs for errors

## 📄 License

MIT License - feel free to use for any project!

## 🤝 Contributing

This is a quick-build production app. For improvements:
1. Fork the repo
2. Make changes
3. Test locally
4. Submit PR

## 🚀 Next Steps

Optional enhancements:
- Add user authentication
- Implement database for persistent storage
- Add batch processing for multiple files
- Add more export formats (CSV, XML)
- Implement webhooks for async processing
- Add rate limiting

---

Built with ❤️ for quick, robust PDF extraction
