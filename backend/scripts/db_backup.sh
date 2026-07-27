#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# GITAM CareerHub — Automated PostgreSQL Backup Script
#
# Features:
#   - Daily compressed pg_dump to /backups/
#   - Retains last 30 days of backups
#   - Logs success/failure with timestamps
#   - Can be triggered via cron or Celery beat
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BACKUP_DIR="/backups"
DB_NAME="${POSTGRES_DB:-gitam_careerhub}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_SERVER:-localhost}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/careerhub_${DB_NAME}_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting database backup: $DB_NAME"

# Create compressed backup
PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    | gzip > "$BACKUP_FILE"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup completed: $BACKUP_FILE ($(du -sh $BACKUP_FILE | cut -f1))"

# Rotate old backups
find "$BACKUP_DIR" -name "careerhub_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Old backups cleaned (retention: ${RETENTION_DAYS} days)"
