CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    tool_type TEXT NOT NULL,
    input_data TEXT NOT NULL,
    result_json JSONB,
    phishing_score INTEGER,
    threat_level TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address TEXT,
    domain TEXT,
    email_address TEXT
);