-- Migration 001: Create configurations table
CREATE TABLE IF NOT EXISTS configurations (
    id SERIAL PRIMARY KEY,
    service VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(service, version)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_configurations_service ON configurations(service);
CREATE INDEX IF NOT EXISTS idx_configurations_service_version ON configurations(service, version);
CREATE INDEX IF NOT EXISTS idx_configurations_created_at ON configurations(created_at);