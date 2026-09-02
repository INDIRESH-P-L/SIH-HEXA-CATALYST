#!/usr/bin/env bash
set -e

PG_BIN="/home/keshav/.local/opt/postgres/usr/bin"
PG_DATA="/home/keshav/.local/share/sip_postgres_data"

echo "Stopping local PostgreSQL server..."
"$PG_BIN/pg_ctl" -D "$PG_DATA" stop
