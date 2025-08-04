# Getting Started - Cardio360-Lite

Welcome to Cardio360-Lite! This guide will help you set up the development environment and get the system running locally.

## 🎯 Quick Overview

Cardio360-Lite is a complete myocardial infarction (MI) detection system featuring:

- **ML Pipeline**: 1D ResNet-18 trained on PTB-XL dataset for STEMI detection
- **FastAPI Backend**: Event processing, WhatsApp alerts, PostgreSQL storage
- **React Dashboard**: Clinician interface for monitoring and event management
- **Android App**: Real-time ECG/PPG monitoring with on-device ML inference

## 📋 Prerequisites

### Required Software
- **Python 3.9+** (for ML training and backend)
- **Node.js 18+** (for React dashboard)
- **Android Studio** (for mobile app development)
- **Git** (version control)
- **PostgreSQL** (database - or use Supabase)

### Optional Tools
- **Docker** (for containerized deployment)
- **VS Code** (recommended IDE)
- **Postman** (API testing)

## 🚀 Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-username/cardio360-lite.git
cd cardio360-lite
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database and WhatsApp credentials

# Run database migrations (if using local PostgreSQL)
python -c "
import asyncpg
import asyncio
async def setup_db():
    conn = await asyncpg.connect('postgresql://localhost/cardio360lite')
    with open('schema.sql', 'r') as f:
        await conn.execute(f.read())
    await conn.close()
asyncio.run(setup_db())
"

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### 4. Model Training Setup

```bash
cd model

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download PTB-XL dataset (manual step)
# Visit: https://physionet.org/content/ptb-xl/1.0.3/
# Extract to: model/ptb-xl/

# Test model creation (without training)
python resnet1d.py
```

### 5. Mobile App Setup

```bash
# Open Android Studio
# File -> Open -> select mobile/android directory
# Let Gradle sync complete

# Add TensorFlow Lite model (after training)
# Copy model/outputs/stemi_int8.tflite to:
# mobile/android/app/src/main/assets/

# Run on emulator or device
# Click "Run" button in Android Studio
```

## 🔧 Configuration

### Environment Variables

Create these files with your specific values:

#### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/cardio360lite
WHATSAPP_TOKEN=your_whatsapp_business_token
WHATSAPP_PHONE_ID=your_phone_number_id  
DOCTOR_WHATSAPP_NUMBER=+1234567890
```

#### Frontend (.env.local)
```env
VITE_API_URL=http://localhost:8000
```

### Database Setup Options

#### Option A: Local PostgreSQL
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu
brew install postgresql                              # macOS

# Create database
sudo -u postgres createdb cardio360lite
sudo -u postgres psql -c "CREATE USER cardio360 WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cardio360lite TO cardio360;"
```

#### Option B: Supabase (Recommended)
1. Visit [supabase.com](https://supabase.com)
2. Create new project
3. Copy database URL from Settings -> Database
4. Run `backend/schema.sql` in SQL Editor

## 🧪 Testing the System

### 1. Backend API Tests
```bash
cd backend

# Test health endpoint
curl http://localhost:8000/health

# Test event creation
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-device-123",
    "timestamp": "2024-01-01T12:00:00Z",
    "risk_score": 0.85,
    "csv": null
  }'

# Test event retrieval
curl http://localhost:8000/events?limit=10
```

### 2. Frontend Dashboard
1. Open `http://localhost:3000`
2. Check dashboard loads with statistics
3. Navigate to Events page
4. Verify event table displays data

### 3. Model Training (Basic Test)
```bash
cd model

# Quick test with dummy data (no actual training)
python train.py --epochs 1 --no_wandb --data_path dummy/
```

## 📱 Development Workflow

### Typical Development Session

1. **Start Backend**
   ```bash
   cd backend && uvicorn main:app --reload
   ```

2. **Start Frontend**
   ```bash
   cd frontend && npm run dev
   ```

3. **Open Android Studio** (if working on mobile)

4. **Make Changes**
   - Backend changes auto-reload with `--reload`
   - Frontend changes auto-refresh with Vite HMR
   - Mobile changes require rebuild

### Code Quality Tools

```bash
# Backend linting and formatting
cd backend
ruff check .        # Linting
black .            # Formatting
pytest tests/      # Testing

# Frontend linting and type checking
cd frontend
npm run lint       # ESLint
npx tsc --noEmit  # Type check
npm run build     # Build check
```

## 🐛 Common Issues & Solutions

### Backend Issues

**Issue**: Database connection failed
```bash
# Solution: Check PostgreSQL is running
sudo service postgresql start  # Linux
brew services start postgresql # macOS

# Verify connection string in .env
```

**Issue**: WhatsApp API not working
```bash
# Solution: Verify credentials
# Check token has required permissions
# Ensure phone number is verified
```

### Frontend Issues

**Issue**: API requests fail with CORS error
```bash
# Solution: Backend CORS is configured for development
# Ensure backend is running on port 8000
# Check VITE_API_URL in .env.local
```

**Issue**: Build fails with TypeScript errors
```bash
# Solution: Fix type errors
npx tsc --noEmit  # Check all type errors
npm run lint      # Check linting issues
```

### Mobile Issues

**Issue**: TensorFlow Lite model not found
```bash
# Solution: Copy model file to assets
cp model/outputs/stemi_int8.tflite mobile/android/app/src/main/assets/
```

**Issue**: Gradle sync fails
```bash
# Solution: Check Android SDK and build tools
# File -> Project Structure -> SDK Location
# Update Gradle version if needed
```

## 📚 Next Steps

1. **Read the Architecture Guide**: `docs/ARCHITECTURE.md`
2. **Review Deployment Guide**: `docs/DEPLOYMENT.md`
3. **Check API Documentation**: Visit `http://localhost:8000/docs`
4. **Explore Model Training**: `model/README.md`
5. **Mobile Development**: `mobile/README.md`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: cardio360lite@example.com

---

Happy coding! 🚀 Let's build the future of cardiac care together.