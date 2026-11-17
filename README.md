# SmartHome Lite

Modular smart-home stack: FastAPI backend, Next.js web UI, Kotlin Android app, Raspberry Pi Z-Wave bridge, and TimescaleDB.

## Overview

Controls lamps and plugs, presence detection, IF-THEN automation, and light ML adaptation. Designed as a multi-component university showcase.

## Features

- Manual device control and central dashboard
- Presence detection and history
- Rule engine and preset scenarios
- Multi-model ML helpers (classification, intensity, clustering)
- TimescaleDB time-series storage
- Raspberry Pi + Z-Wave JS integration

## Stack

- FastAPI, Python, TimescaleDB / PostgreSQL
- Next.js, React
- Kotlin Android
- Flask on Raspberry Pi, Z-Wave JS
- Docker for local DB services

## Layout

```
smarthome-lite/
├── docs/          → architecture and project docs
├── backend/       → FastAPI API and ML
├── web/           → Next.js frontend
├── mobile/        → Kotlin Android app
├── raspberry/     → Pi bridge services
├── db/            → database schemas / compose
└── zwave-js/      → Z-Wave JS config
```

## Run

```bash
cp .env.example .env
# fill DATABASE_*, SECRET_KEY, API keys locally (never commit .env)

cd db && docker compose up -d
cd ../backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd ../web && npm install && npm run dev
```

See `docs/` and each component README for mobile and Raspberry setup. Rotate any secrets that were previously committed.
