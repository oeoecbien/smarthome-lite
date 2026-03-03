#!/usr/bin/env bash
# Restauration de la base smarthome depuis un fichier backup (paramètres depuis .env)
# Usage: ./restore.sh [fichier.sql]
#   Sans argument: restaure le backup le plus récent dans db/backups/
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Fichier .env introuvable: $ENV_FILE"
  exit 1
fi

while IFS= read -r line; do
  [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
  if [[ "$line" =~ ^DATABASE_ ]]; then
    export "$line"
  fi
done < <(grep -v '^#' "$ENV_FILE" | grep -E '^DATABASE_' | sed 's/^export //')

export PGPASSWORD="${DATABASE_PASSWORD}"

if [ -n "$1" ]; then
  BACKUP_FILE="$1"
  if [ ! -f "$BACKUP_FILE" ]; then
    echo "Fichier introuvable: $BACKUP_FILE"
    exit 1
  fi
else
  BACKUP_DIR="$SCRIPT_DIR/backups"
  if [ ! -d "$BACKUP_DIR" ]; then
    echo "Aucun dossier backups/ et aucun fichier fourni. Lancez d'abord ./backup.sh"
    exit 1
  fi
  BACKUP_FILE="$(ls -t "$BACKUP_DIR"/smarthome_*.sql 2>/dev/null | head -1)"
  if [ -z "$BACKUP_FILE" ]; then
    echo "Aucun fichier smarthome_*.sql dans $BACKUP_DIR"
    exit 1
  fi
  echo "Restauration du backup le plus récent: $BACKUP_FILE"
fi

echo "Drop et recréation de la base ${DATABASE_NAME}..."
psql -h "${DATABASE_HOST}" -p "${DATABASE_PORT}" -U "${DATABASE_USER}" -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS ${DATABASE_NAME};"
psql -h "${DATABASE_HOST}" -p "${DATABASE_PORT}" -U "${DATABASE_USER}" -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "CREATE DATABASE ${DATABASE_NAME} WITH OWNER = ${DATABASE_USER} ENCODING = 'UTF8';"

echo "Restauration depuis $BACKUP_FILE ..."
psql -h "${DATABASE_HOST}" -p "${DATABASE_PORT}" -U "${DATABASE_USER}" -d "${DATABASE_NAME}" \
  -v ON_ERROR_STOP=1 \
  -f "$BACKUP_FILE"

echo "Restauration terminée."
unset PGPASSWORD
