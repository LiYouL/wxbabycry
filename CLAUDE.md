# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

智能育儿助手 — WeChat Mini Program that uses AI to recognize baby cries and provide parenting advice, white noise, growth tracking, and vaccine reminders.

## Commands

```bash
# Backend dev server (starts on :8000, works without PostgreSQL for health check)
cd backend && uvicorn app.main:app --reload --port 8000

# Verify all routes are registered
cd backend && python -c "from app.main import app; print(len(app.routes), 'routes')"

# Frontend: open miniapp/ in WeChat DevTools with urlCheck disabled
```

## Architecture

```
Request flow for cry recognition:
  WeChat audio → POST /api/cry/recognize → audio_processor.py (librosa MFCC)
  → cry_classifier.py (CNN placeholder) → ai_client.py (Claude API)
  → CryRecord saved to DB → JSON response with advice

All 7 models: User → Baby → Feeding / Sleep / Diaper / Vaccine / CryRecord
All 6 route modules: user, baby, cry, records, vaccine, noise
```

## Environment notes

- Python 3.8 in current environment — use `Optional[X]` not `X | None`, `List[X]` not `list[X]`
- PostgreSQL is required for full functionality; server starts without it but DB endpoints will fail
- CNN classifier is a placeholder (random predictions) — to be replaced with a trained model
- `.env` goes in `backend/` (see `.env.example`)
