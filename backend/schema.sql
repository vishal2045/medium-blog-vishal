-- Cardio360-Lite Database Schema

-- Events table to store MI detection events
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,  -- SHA-256 hashed device ID for privacy
    timestamp TIMESTAMPTZ NOT NULL,  -- When the event occurred
    risk_score REAL NOT NULL CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    csv_data TEXT,  -- Base64 encoded ECG data (optional)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_events_timestamp (timestamp DESC),
    INDEX idx_events_risk_score (risk_score DESC),
    INDEX idx_events_device_id (device_id)
);

-- Optional: Create a view for dashboard queries
CREATE OR REPLACE VIEW events_summary AS
SELECT 
    id,
    LEFT(device_id, 8) || '...' as device_id_masked,
    timestamp,
    risk_score,
    CASE 
        WHEN risk_score > 0.8 THEN 'HIGH'
        WHEN risk_score > 0.5 THEN 'MEDIUM'
        ELSE 'LOW'
    END as risk_level,
    created_at,
    CASE WHEN csv_data IS NOT NULL THEN true ELSE false END as has_ecg_data
FROM events
ORDER BY timestamp DESC;

-- Insert some sample data for testing (optional - remove in production)
INSERT INTO events (device_id, timestamp, risk_score, csv_data) VALUES
(
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  -- SHA-256 of 'test-device-1'
    NOW() - INTERVAL '1 hour',
    0.95,
    NULL
),
(
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    NOW() - INTERVAL '2 hours',
    0.65,
    NULL
),
(
    'd7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592',  -- SHA-256 of 'test-device-2'
    NOW() - INTERVAL '3 hours',
    0.25,
    NULL
);