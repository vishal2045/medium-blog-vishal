# Deployment Guide - Cardio360-Lite

This guide covers deploying the complete Cardio360-Lite system to production using free-tier services.

## 🏗️ Architecture Overview

```
[Mobile App] ──── POST /event ────▶ [FastAPI Backend] ──── [PostgreSQL]
                                         │                      │
                                         ▼                      │
                                   [WhatsApp API]               │
                                         │                      │
                                         ▼                      ▼
                              [React Dashboard] ◀──── GET /events
```

## 📋 Prerequisites

- GitHub account
- Supabase account (free tier)
- Render account (free tier)
- Vercel account (free tier)
- WhatsApp Business API account (free tier)

## 🚀 Step-by-Step Deployment

### 1. Database Setup (Supabase)

1. **Create Supabase Project**
   ```bash
   # Visit https://supabase.com/dashboard
   # Create new project
   # Note down the database URL
   ```

2. **Run Database Schema**
   ```sql
   -- Copy and run backend/schema.sql in Supabase SQL Editor
   -- This creates the events table and sample data
   ```

3. **Configure Environment Variables**
   ```
   DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
   ```

### 2. WhatsApp Business API Setup

1. **Create Meta Developer Account**
   - Visit [developers.facebook.com](https://developers.facebook.com)
   - Create WhatsApp Business API app

2. **Get API Credentials**
   ```
   WHATSAPP_TOKEN=your_permanent_token
   WHATSAPP_PHONE_ID=your_phone_number_id
   DOCTOR_WHATSAPP_NUMBER=+1234567890
   ```

3. **Create Message Template** (optional)
   ```json
   {
     "name": "mi_alert",
     "language": "en_US",
     "category": "ALERT_UPDATE",
     "components": [
       {
         "type": "BODY",
         "text": "🚨 HIGH RISK MI ALERT\n\nDevice: {{1}}\nTime: {{2}}\n\nImmediate attention required!"
       }
     ]
   }
   ```

### 3. Backend Deployment (Render)

1. **Connect GitHub Repository**
   - Fork this repository
   - Connect to Render dashboard
   - Select `backend` directory as root

2. **Configure Environment Variables**
   ```
   DATABASE_URL=your_supabase_database_url
   WHATSAPP_TOKEN=your_whatsapp_token
   WHATSAPP_PHONE_ID=your_phone_id
   DOCTOR_WHATSAPP_NUMBER=your_doctor_number
   ```

3. **Deploy Settings**
   ```yaml
   # render.yaml is already configured
   # Deployment will use:
   # - Python 3.11
   # - FastAPI with Uvicorn
   # - Automatic health checks
   ```

4. **Verify Deployment**
   ```bash
   curl https://your-app.onrender.com/health
   # Should return: {"status": "healthy", "database": "connected"}
   ```

### 4. Frontend Deployment (Vercel)

1. **Connect GitHub Repository**
   - Import project in Vercel dashboard
   - Select `frontend` directory as root

2. **Configure Environment Variables**
   ```
   VITE_API_URL=https://your-backend.onrender.com
   ```

3. **Deploy Settings**
   ```json
   // vercel.json is already configured
   // Deployment will:
   // - Build React app with Vite
   // - Serve static files
   // - Handle SPA routing
   ```

4. **Verify Deployment**
   - Visit your Vercel URL
   - Check dashboard loads correctly
   - Verify API connection in browser console

### 5. Mobile App Deployment

#### Option A: Android APK (Development)

1. **Setup Android Studio**
   ```bash
   # Install Android Studio
   # Open mobile/android project
   # Sync Gradle files
   ```

2. **Add TFLite Model**
   ```bash
   # Copy trained model to:
   # mobile/android/app/src/main/assets/stemi_int8.tflite
   ```

3. **Build APK**
   ```bash
   cd mobile/android
   ./gradlew assembleDebug
   # APK will be in app/build/outputs/apk/debug/
   ```

#### Option B: Play Store (Production)

1. **Create Play Console Account**
2. **Generate Signed APK**
3. **Upload to Play Store**
4. **Configure App Listing**

### 6. CI/CD Pipeline Setup

1. **Configure GitHub Secrets**
   ```
   RENDER_SERVICE_ID=your_render_service_id
   RENDER_API_KEY=your_render_api_key
   VERCEL_TOKEN=your_vercel_token
   VERCEL_ORG_ID=your_vercel_org_id
   VERCEL_PROJECT_ID=your_vercel_project_id
   ```

2. **Enable GitHub Actions**
   - Actions will run automatically on push to main
   - Includes testing, building, and deployment

## 🔧 Configuration

### Environment Variables Summary

| Service | Variable | Description |
|---------|----------|-------------|
| Backend | `DATABASE_URL` | Supabase PostgreSQL connection string |
| Backend | `WHATSAPP_TOKEN` | WhatsApp Business API token |
| Backend | `WHATSAPP_PHONE_ID` | WhatsApp phone number ID |
| Backend | `DOCTOR_WHATSAPP_NUMBER` | Doctor's WhatsApp number |
| Frontend | `VITE_API_URL` | Backend API base URL |

### Service URLs

- **Backend API**: `https://cardio360-lite-api.onrender.com`
- **Frontend Dashboard**: `https://cardio360-lite.vercel.app`
- **Database**: Supabase PostgreSQL
- **Monitoring**: Render dashboard + Vercel analytics

## 📊 Monitoring & Maintenance

### Health Checks

1. **Backend Health**
   ```bash
   curl https://your-backend.onrender.com/health
   ```

2. **Database Connection**
   ```bash
   curl https://your-backend.onrender.com/events?limit=1
   ```

3. **Frontend Availability**
   ```bash
   curl -I https://your-frontend.vercel.app
   ```

### Log Monitoring

- **Render**: View logs in Render dashboard
- **Vercel**: Check function logs and analytics
- **Supabase**: Monitor database performance

### Scaling Considerations

#### Free Tier Limits

| Service | Limit | Upgrade Path |
|---------|-------|--------------|
| Render | 750 hours/month | $7/month for Pro |
| Vercel | 100GB bandwidth | $20/month for Pro |
| Supabase | 500MB database | $25/month for Pro |
| WhatsApp | 1000 messages/month | Pay per message |

#### Performance Optimization

1. **Backend**
   - Enable connection pooling
   - Add Redis caching (upgrade required)
   - Implement rate limiting

2. **Frontend**
   - Enable Vercel Edge caching
   - Optimize bundle size
   - Add service worker

3. **Database**
   - Add database indexes
   - Implement query optimization
   - Consider read replicas

## 🚨 Troubleshooting

### Common Issues

1. **Backend Won't Start**
   ```bash
   # Check environment variables
   # Verify database connection
   # Check Render logs
   ```

2. **Frontend API Errors**
   ```bash
   # Verify VITE_API_URL is correct
   # Check CORS configuration
   # Inspect network requests
   ```

3. **WhatsApp Not Sending**
   ```bash
   # Verify token and phone ID
   # Check message template
   # Review WhatsApp API logs
   ```

### Support Resources

- **Render**: [render.com/docs](https://render.com/docs)
- **Vercel**: [vercel.com/docs](https://vercel.com/docs)
- **Supabase**: [supabase.com/docs](https://supabase.com/docs)
- **WhatsApp API**: [developers.facebook.com](https://developers.facebook.com/docs/whatsapp)

## 🔒 Security Checklist

- [ ] Environment variables properly configured
- [ ] HTTPS enabled on all services
- [ ] Database access restricted
- [ ] API rate limiting enabled
- [ ] Secrets not committed to Git
- [ ] Regular security updates
- [ ] Vulnerability scanning enabled

---

**Total Cost**: ₹0-350 (depending on optional ECG sensor)

This deployment provides a production-ready MI detection system suitable for academic projects and small-scale clinical trials.