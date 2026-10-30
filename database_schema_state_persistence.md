# Database Design & Persistence Schema (DATABASE)

## 1. Storage Architecture
Krishi Mitra uses a dual-layer persistence strategy:
1. **Redis (Hot Session Cache)**: Stores active `FarmerProfile` state, conversation history window, and latest `EligibilityAuditResult` with a $24\text{-hour}$ TTL for sub-$5\text{ ms}$ read/write access during live voice turns.
2. **PostgreSQL (Relational Audit & Knowledge Store)**: Stores the versioned Scheme Rule Catalog, Regional Dialect Lexicons, Conversation Turn Logs, and Auditable Eligibility Evaluations.

---

## 2. Entity-Relationship Schema (PostgreSQL DDL)

    -- 1. Conversation Sessions Table
    CREATE TABLE sessions (
        session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        modality_mode VARCHAR(20) NOT NULL DEFAULT 'PHASE1_TEXT', -- 'PHASE1_TEXT' or 'PHASE2_VOICE'
        detected_dialect VARCHAR(50),
        farmer_profile_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- 2. Conversation Turns Table (Full Context Retention & Audit Log)
    CREATE TABLE conversation_turns (
        turn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        turn_index INTEGER NOT NULL,
        user_raw_input TEXT NOT NULL,
        user_normalized_text TEXT,
        asr_confidence NUMERIC(4,3),
        extracted_slots_delta JSONB NOT NULL DEFAULT '{}'::jsonb,
        eligibility_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
        assistant_spoken_kn TEXT NOT NULL,
        assistant_display_kn TEXT NOT NULL,
        latency_ms INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (session_id, turn_index)
    );

    -- 3. Reference Schemes Master Table
    CREATE TABLE schemes_catalog (
        scheme_id VARCHAR(64) PRIMARY KEY,
        scheme_name_en VARCHAR(255) NOT NULL,
        scheme_name_kn VARCHAR(255) NOT NULL,
        is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
        category VARCHAR(64) NOT NULL,
        rules_definition JSONB NOT NULL,
        benefits_kn TEXT NOT NULL,
        conditions_kn TEXT NOT NULL,
        required_documents JSONB NOT NULL,
        application_steps_kn JSONB NOT NULL,
        version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- 4. Dialect & Crop Lexicon Table
    CREATE TABLE regional_lexicon (
        lexicon_id SERIAL PRIMARY KEY,
        entity_type VARCHAR(32) NOT NULL, -- 'CROP', 'UNIT', 'SEASON', 'OWNERSHIP', 'DISTRICT'
        colloquial_term VARCHAR(128) NOT NULL,
        canonical_code VARCHAR(64) NOT NULL,
        dialect_region VARCHAR(64) DEFAULT 'ALL_KARNATAKA',
        metadata_json JSONB DEFAULT '{}'::jsonb
    );

    CREATE INDEX idx_turns_session ON conversation_turns(session_id, turn_index);
    CREATE INDEX idx_lexicon_term ON regional_lexicon(colloquial_term);