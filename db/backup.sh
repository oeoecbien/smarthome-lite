#!/usr/bin/env bash
# Sauvegarde de la base smarthome (paramètres lus depuis .env)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Fichier .env introuvable: $ENV_FILE"
  exit 1
fi

# Charger uniquement les variables DATABASE_* depuis .env
while IFS= read -r line; do
  [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
  if [[ "$line" =~ ^DATABASE_ ]]; then
    export "$line"
  fi
done < <(grep -v '^#' "$ENV_FILE" | grep -E '^DATABASE_' | sed 's/^export //')

export PGPASSWORD="${DATABASE_PASSWORD}"

BACKUP_DIR="$SCRIPT_DIR/backups"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/smarthome_${STAMP}.sql"

echo "Sauvegarde vers $BACKUP_FILE ..."
pg_dump -h "${DATABASE_HOST}" -p "${DATABASE_PORT}" -U "${DATABASE_USER}" -d "${DATABASE_NAME}" \
  --no-owner --no-acl --clean --if-exists \
  -f "$BACKUP_FILE"

echo "Sauvegarde terminée: $BACKUP_FILE"
unset PGPASSWORD
