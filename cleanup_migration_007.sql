-- Cleanup script for partial migration 007
-- Run this if the migration 007 failed partway through

-- Drop indexes if they exist
DROP INDEX IF EXISTS ix_document_versions_is_latest;
DROP INDEX IF EXISTS ix_document_versions_version_string;

-- Drop foreign key constraints if they exist
ALTER TABLE document_versions DROP CONSTRAINT IF EXISTS fk_dv_replaced_by_version_id;
ALTER TABLE document_versions DROP CONSTRAINT IF EXISTS fk_dv_parent_version_id;

-- Drop columns if they exist
ALTER TABLE document_versions DROP COLUMN IF EXISTS obsolete_date CASCADE;
ALTER TABLE document_versions DROP COLUMN IF EXISTS effective_date CASCADE;
ALTER TABLE document_versions DROP COLUMN IF EXISTS change_type CASCADE;
ALTER TABLE document_versions DROP COLUMN IF EXISTS change_reason CASCADE;
ALTER TABLE document_versions DROP COLUMN IF EXISTS replaced_by_version_id CASCADE;
ALTER TABLE document_versions DROP COLUMN IF EXISTS is_latest CASCADE;
ALTER TABLE document_versions DROP COLUMN IF EXISTS parent_version_id CASCADE;
ALTER TABLE document_versions DROP COLUMN IF EXISTS version_string CASCADE;

-- Mark the migration as not applied
DELETE FROM alembic_version WHERE version_num = '007_controlled_versioning';

-- Success message
SELECT 'Cleanup complete! Now run: alembic upgrade head' as message;

