-- =============================================================
-- DocuVerify — Supabase Database & Storage Setup Script
-- Run this in your Supabase SQL Editor: Dashboard -> SQL Editor
-- =============================================================

-- 1. Create verification_reports table
CREATE TABLE IF NOT EXISTS public.verification_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    size_kb NUMERIC,
    extension TEXT,
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- High level scores
    authenticity_index NUMERIC NOT NULL DEFAULT 100.0,
    risk_index NUMERIC NOT NULL DEFAULT 0.0,
    modules_flagged INT DEFAULT 0,
    total_anomalies INT DEFAULT 0,
    integrity_label TEXT NOT NULL,
    summary_report TEXT,
    
    -- Detailed forensic payloads (JSONB)
    test_cases JSONB DEFAULT '[]'::jsonb,
    regions JSONB DEFAULT '[]'::jsonb,
    visualizations JSONB DEFAULT '{}'::jsonb,
    raw_results JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata & Auditing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    client_ip TEXT,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- 2. Create indices for fast lookup & filtering
CREATE INDEX IF NOT EXISTS idx_verification_reports_file_id ON public.verification_reports(file_id);
CREATE INDEX IF NOT EXISTS idx_verification_reports_created_at ON public.verification_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_verification_reports_integrity ON public.verification_reports(integrity_label);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.verification_reports ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS Policies (Allow public read & insert for seamless frontend reporting)
DROP POLICY IF EXISTS "Allow anonymous read access" ON public.verification_reports;
CREATE POLICY "Allow anonymous read access" 
ON public.verification_reports 
FOR SELECT 
USING (true);

DROP POLICY IF EXISTS "Allow anonymous insert access" ON public.verification_reports;
CREATE POLICY "Allow anonymous insert access" 
ON public.verification_reports 
FOR INSERT 
WITH CHECK (true);

-- 5. Create Storage Buckets (Optional for forensic documents & heatmap caching)
INSERT INTO storage.buckets (id, name, public)
VALUES ('forensic-vault', 'forensic-vault', true)
ON CONFLICT (id) DO NOTHING;

-- 6. Storage Bucket Policy (Public read access)
DROP POLICY IF EXISTS "Public Access to forensic vault" ON storage.objects;
CREATE POLICY "Public Access to forensic vault"
ON storage.objects FOR SELECT
USING ( bucket_id = 'forensic-vault' );

DROP POLICY IF EXISTS "Allow upload to forensic vault" ON storage.objects;
CREATE POLICY "Allow upload to forensic vault"
ON storage.objects FOR INSERT
WITH CHECK ( bucket_id = 'forensic-vault' );
