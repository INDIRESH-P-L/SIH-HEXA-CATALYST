#!/usr/bin/env bash
set -e

PG_BIN="/home/keshav/.local/opt/postgres/usr/bin"
PG_DATA="/home/keshav/.local/share/sip_postgres_data"
PG_PORT=5434

if [ ! -d "$PG_DATA" ]; then
    echo "Initializing database cluster in $PG_DATA..."
    "$PG_BIN/initdb" -D "$PG_DATA" -U sip --auth=trust
fi

echo "Starting local PostgreSQL server on port $PG_PORT..."
"$PG_BIN/pg_ctl" -D "$PG_DATA" -o "-p $PG_PORT -k /tmp" -l "$PG_DATA/postgres.log" start

echo "PostgreSQL started successfully on port $PG_PORT."
