# ScholarStream Backend API

Production-ready FastAPI backend for ScholarStream scholarship discovery platform.

## 🏗️ Architecture

### Tech Stack
- **Framework**: FastAPI 0.115.5 (async-first, high performance)
- **Database**: Firebase Firestore (NoSQL, real-time)
- **Authentication**: Firebase Auth (integrated with frontend)
- **AI**: Google Gemini 2.5 Flash (scholarship enrichment)
- **Scraping**: BeautifulSoup4 + HTTPX (async web scraping)
- **Caching**: Redis (background jobs, rate limiting)
- **Storage**: Cloudinary (document uploads)

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── models.py               # Pydantic data models
│   ├── database.py             # Firebase Firestore layer
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── scholarships.py     # Scholarship endpoints
│   │   └── applications.py     # Application tracking endpoints
│   └── services/
│       ├── __init__.py
│       ├── scraper_service.py  # Web scraping logic
│       ├── ai_service.py       # Gemini AI integration
│       └── matching_service.py # Discovery orchestration
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+ (recommended: use Miniconda)
- Firebase project with Firestore enabled
- Google Gemini API key
- Redis server (for background tasks)
- Cloudinary account

### Step 1: Environment Setup

```bash
# Create conda environment
conda create -n scholarstream python=3.11
conda activate scholarstream

# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Firebase Configuration

1. Go to Firebase Console (https://console.firebase.google.com)
2. Create a new project or select existing "ScholarStream" project
3. Enable Firestore Database:
   - Click "Firestore Database" → "Create database"
   - Start in production mode
   - Choose region closest to users

4. Generate service account credentials:
   - Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save the JSON file securely (NEVER commit to git)

5. Enable Firebase Authentication:
   - Authentication → Sign-in method
   - Enable Email/Password and Google providers

### Step 3: Environment Variables

Create `.env` file in `backend/` directory:

```bash
cp .env.example .env
```

Fill in your credentials:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
ENVIRONMENT=development

# Firebase (from service account JSON)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=key-id-from-json
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=client-id-from-json
FIREBASE_CLIENT_X509_CERT_URL=cert-url-from-json

# Google Gemini AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS (add your frontend URLs)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### Step 4: Start Redis (Required for Background Jobs)

```bash
# macOS (with Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows (with WSL or Docker)
docker run -d -p 6379:6379 redis:latest
```

### Step 5: Start the API Server

```bash
# Development mode (auto-reload enabled)
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: **http://localhost:8000**

## 📚 API Documentation

Once the server is running, access interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔑 Key Endpoints

### Scholarship Discovery
```http
POST /api/scholarships/discover
Content-Type: application/json

{
  "user_id": "firebase-user-id",
  "profile": {
    "name": "John Doe",
    "academic_status": "Undergraduate",
    "gpa": 3.5,
    "major": "Computer Science",
    ...
  }
}
```

### Get Matched Scholarships
```http
GET /api/scholarships/matched?user_id={user_id}
```

### Get Scholarship Details
```http
GET /api/scholarships/{scholarship_id}
```

### Save/Unsave Scholarship
```http
POST /api/scholarships/save
Content-Type: application/json

{
  "user_id": "firebase-user-id",
  "scholarship_id": "scholarship-id"
}
```

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app tests/
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - contains sensitive credentials
2. **Firebase private key** - keep secure, rotate if exposed
3. **Gemini API key** - monitor usage, set quotas in Google Cloud Console
4. **Rate limiting** - configured via `RATE_LIMIT_PER_MINUTE`
5. **CORS** - only allow trusted frontend origins
6. **Input validation** - all inputs validated via Pydantic models
7. **Logging** - structured logs, never log sensitive data

## 🎯 Performance Optimizations

### Caching Strategy
- **Scholarship cache**: 24 hours (configurable)
- **AI enrichment cache**: 7 days (expensive operation)
- **In-memory cache** for AI responses within same session

### Rate Limiting
- **Gemini API**: 1000 requests/hour (adjustable)
- **Public endpoints**: 60 requests/minute per IP
- **Background jobs**: Process in batches of 5

### Database
- **Firestore indexes**: Created automatically for common queries
- **Batch operations**: Group writes for efficiency
- **Cached reads**: Reduce Firestore read costs

## 🐛 Troubleshooting

### Firebase Connection Issues
```bash
# Verify credentials
python -c "from app.database import db; print('Connected')"
```

### Gemini API Errors
- Check API key is valid
- Verify quota in Google Cloud Console
- Monitor rate limits in logs

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

## 📈 Monitoring & Logs

All logs are structured JSON format:
```json
{
  "event": "Request received",
  "method": "POST",
  "path": "/api/scholarships/discover",
  "timestamp": "2025-11-15T10:30:00Z"
}
```

### Production Monitoring
- **Health endpoint**: `/health` for uptime monitoring
- **Structured logs**: Pipe to Logstash/CloudWatch/DataDog
- **Error tracking**: Integrate Sentry (add to requirements.txt)

## 🚢 Deployment

### Option 1: Cloud Run (Recommended)
```bash
# Build container
docker build -t scholarstream-api .

# Deploy to Google Cloud Run
gcloud run deploy scholarstream-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 2: Railway/Render
- Connect GitHub repository
- Set environment variables in dashboard
- Deploy automatically on push

### Option 3: VPS (DigitalOcean, AWS EC2)
```bash
# Use systemd service
sudo nano /etc/systemd/system/scholarstream.service

# Enable and start
sudo systemctl enable scholarstream
sudo systemctl start scholarstream
```

## 🤝 Integration with Frontend

Frontend should set:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

All API calls go through `src/services/api.ts` in frontend.

## 📞 Support

Issues? Check logs first:
```bash
# Tail logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```

## 📝 License
Built with excellence.
