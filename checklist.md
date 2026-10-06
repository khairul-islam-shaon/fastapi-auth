# FastAPI Auth & RBAC — Phase Checklist

## Phase 1 — Project Setup
- [x] Install `uv`
- [x] Initialize FastAPI project
- [x] Create folder structure
- [x] Configure `.env`
- [x] Add `/health`
- [x] Run and verify app

## Phase 2 — Database
- [x] Setup PostgreSQL
- [x] Setup SQLAlchemy
- [ ] Setup Alembic
- [ ] Create `User` model
- [ ] Create `Role` enum
- [ ] Run first migration

## Phase 3 — Authentication
- [ ] Password hashing
- [ ] Register API
- [ ] Login API
- [ ] Generate JWT access token
- [ ] Test login flow

## Phase 4 — Protected Routes
- [ ] Create `get_current_user()`
- [ ] Validate JWT
- [ ] Add `/auth/me`
- [ ] Protect private APIs

## Phase 5 — RBAC
- [ ] Add `ADMIN`
- [ ] Add `MANAGER`
- [ ] Add `USER`
- [ ] Create `require_roles()`
- [ ] Protect routes by role
- [ ] Test role access

## Phase 6 — Refresh Token
- [ ] Create refresh token
- [ ] Store refresh session
- [ ] Add `/auth/refresh`
- [ ] Add logout
- [ ] Add token revocation

## Phase 7 — Production Ready
- [ ] Rate limiting
- [ ] CORS
- [ ] Error handling
- [ ] Logging
- [ ] Auth + RBAC tests
- [ ] Docker
- [ ] Production environment config

---

## Final Flow

```text
Setup
  ↓
Database
  ↓
Authentication
  ↓
Protected Routes
  ↓
RBAC
  ↓
Refresh Token
  ↓
Production Hardening
```