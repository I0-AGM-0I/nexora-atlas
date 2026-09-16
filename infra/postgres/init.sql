-- PostgreSQL Initialization Script for NEXORA ATLAS
-- Ensures uuid-ossp extension is enabled for high-performance UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log initialization
DO $$
BEGIN
   RAISE NOTICE 'NEXORA ATLAS PostgreSQL database initialized successfully.';
END
$$;
