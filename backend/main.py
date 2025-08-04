from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import os
import aiohttp
import logging
from datetime import datetime
from typing import Optional
import base64
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cardio360-Lite API",
    description="FastAPI backend for MI detection and alert system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DB_URL = os.getenv("DATABASE_URL")
WA_TOKEN = os.getenv("WHATSAPP_TOKEN")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
DOCTOR_NUMBER = os.getenv("DOCTOR_WHATSAPP_NUMBER")

# Pydantic models
class Event(BaseModel):
    device_id: str
    timestamp: str  # ISO-8601 format
    risk_score: float
    csv: Optional[str] = None  # base64 encoded ECG data
    
class EventResponse(BaseModel):
    status: str
    message: str
    event_id: Optional[int] = None

class EventQuery(BaseModel):
    limit: Optional[int] = 50
    offset: Optional[int] = 0
    min_risk_score: Optional[float] = None

# Database connection pool
@app.on_event("startup")
async def startup():
    try:
        app.state.pool = await asyncpg.create_pool(
            DB_URL,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database connection pool created successfully")
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    if hasattr(app.state, 'pool'):
        await app.state.pool.close()
        logger.info("Database connection pool closed")

def hash_device_id(device_id: str) -> str:
    """Hash device ID for privacy"""
    return hashlib.sha256(device_id.encode()).hexdigest()

async def send_whatsapp_alert(device_id: str, timestamp: str, risk_score: float):
    """Send WhatsApp alert to doctor"""
    if not all([WA_TOKEN, WA_PHONE_ID, DOCTOR_NUMBER]):
        logger.warning("WhatsApp credentials not configured")
        return False
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages"
            headers = {
                "Authorization": f"Bearer {WA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Simple text message for now (can be enhanced with templates)
            data = {
                "messaging_product": "whatsapp",
                "to": DOCTOR_NUMBER,
                "type": "text",
                "text": {
                    "body": f"🚨 HIGH RISK MI ALERT\n\nDevice: {device_id[:8]}...\nRisk Score: {risk_score:.2f}\nTime: {timestamp}\n\nImmediate attention required!"
                }
            }
            
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    logger.info(f"WhatsApp alert sent successfully for device {device_id}")
                    return True
                else:
                    logger.error(f"WhatsApp alert failed: {response.status} - {await response.text()}")
                    return False
                    
    except Exception as e:
        logger.error(f"Error sending WhatsApp alert: {e}")
        return False

@app.get("/")
async def root():
    return {"message": "Cardio360-Lite API", "version": "1.0.0", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with app.state.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.post("/event", response_model=EventResponse)
async def receive_event(event: Event):
    """Receive and process MI detection event"""
    try:
        # Hash device ID for privacy
        hashed_device_id = hash_device_id(event.device_id)
        
        # Insert event into database
        async with app.state.pool.acquire() as conn:
            event_id = await conn.fetchval(
                """
                INSERT INTO events (device_id, timestamp, risk_score, csv_data, created_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                hashed_device_id,
                datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')),
                event.risk_score,
                event.csv,
                datetime.utcnow()
            )
        
        logger.info(f"Event stored with ID: {event_id}, Risk Score: {event.risk_score}")
        
        # Send WhatsApp alert for high-risk events
        whatsapp_sent = False
        if event.risk_score > 0.8:  # High risk threshold
            whatsapp_sent = await send_whatsapp_alert(
                event.device_id, 
                event.timestamp, 
                event.risk_score
            )
        
        return EventResponse(
            status="success",
            message=f"Event processed successfully. WhatsApp alert: {'sent' if whatsapp_sent else 'not sent'}",
            event_id=event_id
        )
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process event: {str(e)}")

@app.get("/events")
async def get_events(
    limit: int = 50,
    offset: int = 0,
    min_risk_score: Optional[float] = None
):
    """Get events for clinician dashboard"""
    try:
        async with app.state.pool.acquire() as conn:
            query = """
                SELECT id, device_id, timestamp, risk_score, created_at
                FROM events
                WHERE ($3::float IS NULL OR risk_score >= $3)
                ORDER BY timestamp DESC
                LIMIT $1 OFFSET $2
            """
            
            rows = await conn.fetch(query, limit, offset, min_risk_score)
            
            events = []
            for row in rows:
                events.append({
                    "id": row["id"],
                    "device_id": row["device_id"][:8] + "...",  # Show only first 8 chars for privacy
                    "timestamp": row["timestamp"].isoformat(),
                    "risk_score": row["risk_score"],
                    "created_at": row["created_at"].isoformat(),
                    "risk_level": "HIGH" if row["risk_score"] > 0.8 else "MEDIUM" if row["risk_score"] > 0.5 else "LOW"
                })
            
            # Get total count
            total_count = await conn.fetchval(
                "SELECT COUNT(*) FROM events WHERE ($1::float IS NULL OR risk_score >= $1)",
                min_risk_score
            )
            
            return {
                "events": events,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
            
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

@app.get("/events/{event_id}/csv")
async def get_event_csv(event_id: int):
    """Get ECG CSV data for a specific event"""
    try:
        async with app.state.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT csv_data, timestamp, device_id FROM events WHERE id = $1",
                event_id
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="Event not found")
            
            if not row["csv_data"]:
                raise HTTPException(status_code=404, detail="No CSV data available for this event")
            
            # Decode base64 CSV data
            try:
                csv_data = base64.b64decode(row["csv_data"]).decode('utf-8')
                return {
                    "event_id": event_id,
                    "timestamp": row["timestamp"].isoformat(),
                    "device_id": row["device_id"][:8] + "...",
                    "csv_data": csv_data
                }
            except Exception as decode_error:
                raise HTTPException(status_code=400, detail="Invalid CSV data format")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching CSV data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch CSV data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)