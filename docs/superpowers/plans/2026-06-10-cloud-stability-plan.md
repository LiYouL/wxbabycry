# WeChat Cloud Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the current WeChat Cloud Hosting deployment easier to verify and less likely to fail on dependency or runtime drift.

**Architecture:** Keep the current single-container FastAPI deployment. Pin the Python base image family, keep sklearn as the active model runtime, expose model health via a read-only endpoint, and commit the current miniapp cloud API configuration.

**Tech Stack:** FastAPI, SQLAlchemy async, SQLite for test deployment, scikit-learn RandomForest model, WeChat Mini Program.

---

### Task 1: Stabilize Docker Runtime

**Files:**
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Pin Python image family**

Change the base image to `python:3.10-slim-bookworm` so cloud builds do not unexpectedly jump Debian versions.

- [ ] **Step 2: Install small runtime libraries**

Install `ffmpeg`, `libsndfile1`, and `libgomp1`. `ffmpeg` and `libsndfile1` support audio decoding; `libgomp1` avoids sklearn/OpenMP runtime surprises.

- [ ] **Step 3: Verify Dockerfile syntax**

Run: `Get-Content backend/Dockerfile`
Expected: file starts with `FROM python:3.10-slim-bookworm`.

### Task 2: Add Model Health Endpoint

**Files:**
- Modify: `backend/app/services/cry_classifier.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add classifier status method**

Expose model type, class count, labels, and runtime availability from `CryClassifier.status()`.

- [ ] **Step 2: Add `/api/health/model` endpoint**

Return `{"status": "ok", "model": classifier.status()}` from FastAPI.

- [ ] **Step 3: Verify locally**

Run:
`cd backend && python -c "from app.main import app; print(len(app.routes), 'routes')"`

Expected: route count increases from 21 to 22.

### Task 3: Commit Cloud Miniapp Config

**Files:**
- Modify: `miniapp/app.js`
- Modify: `miniapp/utils/api.js`
- Modify: `miniapp/project.config.json`

- [ ] **Step 1: Keep cloud API base URL**

Confirm both API base values point to `https://babycry-268031-4-1441517375.sh.run.tcloudbase.com/api`.

- [ ] **Step 2: Keep real AppID**

Confirm `miniapp/project.config.json` uses `wx8e8e8a1b14d5f762`.

- [ ] **Step 3: Commit and push**

Run:
`git add backend/Dockerfile backend/app/main.py backend/app/services/cry_classifier.py miniapp/app.js miniapp/utils/api.js miniapp/project.config.json docs/superpowers/plans/2026-06-10-cloud-stability-plan.md && git commit -m "fix: stabilize wechat cloud deployment" && git push origin master`

Expected: push succeeds.
