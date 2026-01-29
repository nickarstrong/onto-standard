# ONTO API Requirements Specification

**Version:** 1.0  
**Date:** 2026-01-28  
**Status:** Draft  
**Author:** ONTO Foundation

---

## 1. Executive Summary

Спецификация REST API для ONTO Epistemic Risk Platform. Покрывает evaluation, certification, public registry, billing, и admin функционал.

**Deadline:** Backend MVP — Feb 2025  
**Hard deadline:** EU AI Act enforcement — Aug 2025

---

## 2. Gap Analysis (Current vs Required)

### 2.1 Текущее состояние (api.py)

| Компонент | Статус | Реализация |
|-----------|--------|------------|
| Framework | ✅ Done | FastAPI |
| POST /enterprise/evaluate | ✅ Done | Принимает predictions, вычисляет метрики |
| GET /enterprise/status/{id} | ✅ Done | Статус evaluation |
| GET /enterprise/report/{id} | ✅ Done | HTML report download |
| GET /enterprise/evaluations | ✅ Done | Список evaluations клиента |
| POST /enterprise/pilot | ✅ Done | Заявка на pilot |
| Metrics computation | ✅ Done | U-Recall, ECE, Risk Score |
| Report generation | ✅ Done | HTML template |
| API Key auth | ⚠️ Basic | JSON file storage |
| Customer management | ⚠️ CLI only | create_customer() function |

### 2.2 Требуется (Gap)

| Компонент | Приоритет | Блокер для |
|-----------|-----------|------------|
| PostgreSQL | P0 | Production |
| JWT/OAuth2 auth | P0 | Security |
| /v1/ versioning | P0 | API stability |
| POST /v1/certify | P0 | Business model |
| GET /v1/registry | P0 | Public verification |
| Stripe integration | P1 | Revenue |
| Rate limiting | P1 | Abuse prevention |
| Webhook notifications | P2 | UX |
| Admin dashboard API | P2 | Operations |

---

## 3. Architecture

### 3.1 Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| API Framework | FastAPI | Already in use, async support |
| Database | PostgreSQL 15+ | ACID, JSON support |
| ORM | SQLAlchemy 2.0 | Type hints, async |
| Migrations | Alembic | Standard |
| Auth | JWT + API Keys | Dual auth model |
| Cache | Redis | Rate limiting, sessions |
| Queue | Celery + Redis | Background tasks |
| Payments | Stripe | Industry standard |
| Hosting | Railway / Render | MVP speed |

### 3.2 URL Structure

```
Production: https://api.ontostandard.org/v1/
Staging:    https://api-staging.ontostandard.org/v1/
```

---

## 4. Data Models (PostgreSQL)

### 4.1 Core Tables

```sql
-- Organizations (companies using ONTO)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL DEFAULT 'pilot',  -- pilot, starter, pro, enterprise
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users (people in organizations)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',  -- owner, admin, member
    password_hash VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- API Keys (for programmatic access)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,  -- SHA256 of actual key
    key_prefix VARCHAR(12) NOT NULL,  -- First 12 chars for identification
    name VARCHAR(100),
    scopes TEXT[],  -- ['evaluate', 'certify', 'read']
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

-- Evaluations
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    
    -- Input
    predictions_count INTEGER,
    predictions_hash VARCHAR(64),  -- SHA256 for integrity
    
    -- Results
    metrics JSONB,
    risk_score VARCHAR(20),
    risk_score_numeric INTEGER,  -- 0-100
    recommendations JSONB,
    
    -- Timestamps
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Metadata
    notes TEXT,
    error_message TEXT
);

-- Evaluation Predictions (stored separately for size)
CREATE TABLE evaluation_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluations(id) ON DELETE CASCADE,
    sample_id VARCHAR(100) NOT NULL,
    predicted_label VARCHAR(50) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    ground_truth_label VARCHAR(50)  -- Filled after evaluation
);

-- Certificates
CREATE TABLE certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) NOT NULL,
    evaluation_id UUID REFERENCES evaluations(id),
    
    -- Certificate data
    certificate_number VARCHAR(50) UNIQUE NOT NULL,  -- ONTO-2026-001234
    level INTEGER NOT NULL,  -- 1, 2, 3
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(100),
    
    -- Validity
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    revocation_reason TEXT,
    
    -- Metrics snapshot
    metrics_snapshot JSONB NOT NULL,
    risk_score VARCHAR(20) NOT NULL,
    
    -- Verification
    verification_hash VARCHAR(64) NOT NULL,  -- For public verification
    
    -- Status
    status VARCHAR(50) DEFAULT 'active'  -- active, expired, revoked
);

-- Subscriptions (Stripe sync)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) NOT NULL,
    stripe_subscription_id VARCHAR(255),
    tier VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',  -- active, past_due, canceled
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    evaluations_limit INTEGER,
    evaluations_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usage Tracking
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- evaluation, certification, api_call
    resource_id UUID,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pilot Applications
CREATE TABLE pilot_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    model_description TEXT,
    use_case TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected, converted
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    converted_at TIMESTAMPTZ
);

-- Audit Log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 Indexes

```sql
CREATE INDEX idx_evaluations_org ON evaluations(organization_id);
CREATE INDEX idx_evaluations_status ON evaluations(status);
CREATE INDEX idx_certificates_org ON certificates(organization_id);
CREATE INDEX idx_certificates_number ON certificates(certificate_number);
CREATE INDEX idx_certificates_status ON certificates(status);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_usage_org_date ON usage_events(organization_id, created_at);
```

---

## 5. API Endpoints

### 5.1 Authentication

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /v1/auth/register | POST | None | Create organization + user |
| /v1/auth/login | POST | None | Get JWT token |
| /v1/auth/refresh | POST | JWT | Refresh token |
| /v1/auth/logout | POST | JWT | Invalidate token |
| /v1/auth/password/reset | POST | None | Request password reset |
| /v1/auth/password/change | POST | JWT | Change password |
| /v1/auth/verify-email | POST | None | Verify email with code |

### 5.2 API Keys

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /v1/keys | GET | JWT | List API keys |
| /v1/keys | POST | JWT | Create API key |
| /v1/keys/{id} | DELETE | JWT | Revoke API key |

### 5.3 Evaluation (Core)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /v1/evaluate | POST | API Key | Submit evaluation |
| /v1/evaluations | GET | API Key | List evaluations |
| /v1/evaluations/{id} | GET | API Key | Get evaluation details |
| /v1/evaluations/{id}/report | GET | API Key | Download report (HTML/PDF) |
| /v1/evaluations/{id}/report.json | GET | API Key | Report as JSON |

### 5.4 Certification

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /v1/certify | POST | API Key | Request certification |
| /v1/certificates | GET | API Key | List certificates |
| /v1/certificates/{id} | GET | API Key | Get certificate details |
| /v1/certificates/{id}/download | GET | API Key | Download certificate (PDF) |
| /v1/certificates/{id}/badge | GET | None | Get embeddable badge (SVG) |

### 5.5 Public Registry

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /v1/registry | GET | None | Search certificates |
| /v1/registry/{certificate_number} | GET | None | Verify certificate |
| /v1/registry/verify | POST | None | Verify by hash |

### 5.6 Usage & Billing

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /v1/usage | GET | API Key | Get usage stats |
| /v1/usage/limits | GET | API Key | Get current limits |
| /v1/billing/portal | GET | JWT | Stripe customer portal URL |
| /v1/billing/checkout | POST | JWT | Create checkout session |

### 5.7 Pilot Program

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /v1/pilot/apply | POST | None | Submit pilot application |
| /v1/pilot/status | GET | Email token | Check application status |

### 5.8 Webhooks (Outbound)

| Event | Trigger |
|-------|---------|
| evaluation.completed | Evaluation finished |
| evaluation.failed | Evaluation error |
| certificate.issued | Certificate created |
| certificate.expiring | 30 days before expiry |
| certificate.expired | Certificate expired |
| subscription.updated | Tier change |

### 5.9 Admin (Internal)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /admin/organizations | GET | Admin JWT | List all orgs |
| /admin/organizations/{id} | PATCH | Admin JWT | Update org |
| /admin/evaluations | GET | Admin JWT | List all evaluations |
| /admin/pilots | GET | Admin JWT | List pilot applications |
| /admin/pilots/{id}/approve | POST | Admin JWT | Approve pilot |
| /admin/pilots/{id}/reject | POST | Admin JWT | Reject pilot |
| /admin/certificates/{id}/revoke | POST | Admin JWT | Revoke certificate |
| /admin/stats | GET | Admin JWT | Platform statistics |

---

## 6. Request/Response Schemas

### 6.1 POST /v1/evaluate

**Request:**
```json
{
  "model_name": "FinanceGPT",
  "model_version": "2.1.0",
  "predictions": [
    {
      "id": "sample_001",
      "label": "KNOWN",
      "confidence": 0.85
    },
    {
      "id": "sample_002",
      "label": "UNKNOWN",
      "confidence": 0.72
    }
  ],
  "notes": "Q1 2026 evaluation",
  "webhook_url": "https://example.com/webhook"
}
```

**Response (202 Accepted):**
```json
{
  "evaluation_id": "eval_a1b2c3d4",
  "status": "pending",
  "estimated_completion": "2026-01-28T15:30:00Z",
  "status_url": "/v1/evaluations/eval_a1b2c3d4"
}
```

### 6.2 GET /v1/evaluations/{id}

**Response (200 OK):**
```json
{
  "evaluation_id": "eval_a1b2c3d4",
  "status": "completed",
  "model_name": "FinanceGPT",
  "model_version": "2.1.0",
  "submitted_at": "2026-01-28T15:00:00Z",
  "completed_at": "2026-01-28T15:05:23Z",
  "metrics": {
    "accuracy": 0.7612,
    "unknown_detection": {
      "precision": 0.4500,
      "recall": 0.0900,
      "f1": 0.1500
    },
    "calibration": {
      "ece": 0.3100,
      "mean_confidence": 0.7800
    },
    "per_class": {
      "KNOWN": {"precision": 0.82, "recall": 0.91, "f1": 0.86},
      "UNKNOWN": {"precision": 0.45, "recall": 0.09, "f1": 0.15},
      "CONTRADICTION": {"precision": 0.30, "recall": 0.25, "f1": 0.27}
    },
    "n_samples": 268
  },
  "risk_score": "HIGH",
  "risk_score_numeric": 65,
  "recommendations": [
    {
      "category": "unknown_detection",
      "severity": "critical",
      "message": "Model detects only 9% of unknowns",
      "action": "Implement uncertainty quantification"
    }
  ],
  "report_url": "/v1/evaluations/eval_a1b2c3d4/report",
  "certifiable": false,
  "certification_blockers": [
    "U-Recall below 0.30 threshold for Level 1"
  ]
}
```

### 6.3 POST /v1/certify

**Request:**
```json
{
  "evaluation_id": "eval_a1b2c3d4",
  "level": 2,
  "validity_months": 12
}
```

**Response (201 Created):**
```json
{
  "certificate_id": "cert_x1y2z3",
  "certificate_number": "ONTO-2026-001234",
  "level": 2,
  "status": "active",
  "issued_at": "2026-01-28T16:00:00Z",
  "valid_until": "2027-01-28T16:00:00Z",
  "verification_url": "https://ontostandard.org/verify/ONTO-2026-001234",
  "badge_url": "/v1/certificates/cert_x1y2z3/badge",
  "download_url": "/v1/certificates/cert_x1y2z3/download"
}
```

### 6.4 GET /v1/registry/{certificate_number}

**Response (200 OK):**
```json
{
  "valid": true,
  "certificate_number": "ONTO-2026-001234",
  "organization": "Example Corp",
  "model_name": "FinanceGPT",
  "level": 2,
  "level_name": "Standard Compliance",
  "issued_at": "2026-01-28T16:00:00Z",
  "valid_until": "2027-01-28T16:00:00Z",
  "status": "active",
  "metrics_summary": {
    "u_recall": 0.45,
    "ece": 0.15,
    "risk_score": "MEDIUM"
  }
}
```

---

## 7. Certification Levels

### 7.1 Thresholds

| Level | Name | U-Recall | ECE | Risk Score | Price |
|-------|------|----------|-----|------------|-------|
| L1 | Basic | ≥ 0.30 | ≤ 0.35 | ≤ 70 | $5,000 |
| L2 | Standard | ≥ 0.50 | ≤ 0.25 | ≤ 50 | $25,000 |
| L3 | Advanced | ≥ 0.70 | ≤ 0.15 | ≤ 30 | $75,000 |
| Enterprise | Custom | Negotiated | Negotiated | Negotiated | $150,000+ |

### 7.2 Certification Logic

```python
def check_certifiable(metrics: dict, level: int) -> tuple[bool, list[str]]:
    thresholds = {
        1: {"u_recall": 0.30, "ece": 0.35, "risk": 70},
        2: {"u_recall": 0.50, "ece": 0.25, "risk": 50},
        3: {"u_recall": 0.70, "ece": 0.15, "risk": 30},
    }
    
    t = thresholds[level]
    blockers = []
    
    u_recall = metrics["unknown_detection"]["recall"]
    ece = metrics["calibration"]["ece"]
    risk = metrics.get("risk_score_numeric", 100)
    
    if u_recall < t["u_recall"]:
        blockers.append(f"U-Recall {u_recall:.2f} below {t['u_recall']} threshold")
    if ece > t["ece"]:
        blockers.append(f"ECE {ece:.2f} above {t['ece']} threshold")
    if risk > t["risk"]:
        blockers.append(f"Risk score {risk} above {t['risk']} threshold")
    
    return len(blockers) == 0, blockers
```

---

## 8. Authentication & Authorization

### 8.1 Dual Auth Model

| Method | Use Case | Token Type | Lifetime |
|--------|----------|------------|----------|
| JWT | Web dashboard | Bearer token | 15 min (access), 7 days (refresh) |
| API Key | Programmatic | X-API-Key header | Until revoked |

### 8.2 API Key Format

```
onto_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
onto_test_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
     │       │
     │       └── 32 random hex chars
     └── Environment prefix
```

### 8.3 Scopes

| Scope | Permissions |
|-------|-------------|
| evaluate | POST /v1/evaluate |
| certify | POST /v1/certify |
| read | GET all owned resources |
| admin | Full access to org |

### 8.4 Rate Limits

| Tier | Requests/min | Evaluations/month |
|------|--------------|-------------------|
| Pilot | 10 | 1 |
| Starter | 60 | 10 |
| Pro | 300 | 100 |
| Enterprise | 1000 | Unlimited |

---

## 9. Error Handling

### 9.1 Error Response Format

```json
{
  "error": {
    "code": "EVALUATION_LIMIT_EXCEEDED",
    "message": "Monthly evaluation limit reached",
    "details": {
      "limit": 10,
      "used": 10,
      "resets_at": "2026-02-01T00:00:00Z"
    },
    "docs_url": "https://docs.ontostandard.org/errors/EVALUATION_LIMIT_EXCEEDED"
  }
}
```

### 9.2 Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 400 | INVALID_REQUEST | Malformed request |
| 400 | INVALID_PREDICTIONS | Predictions format error |
| 401 | UNAUTHORIZED | Missing/invalid auth |
| 403 | FORBIDDEN | Insufficient permissions |
| 403 | SUBSCRIPTION_EXPIRED | Subscription ended |
| 403 | EVALUATION_LIMIT_EXCEEDED | Quota reached |
| 404 | NOT_FOUND | Resource not found |
| 409 | ALREADY_CERTIFIED | Evaluation already has certificate |
| 422 | NOT_CERTIFIABLE | Metrics don't meet threshold |
| 429 | RATE_LIMITED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

---

## 10. Webhooks (Inbound)

### 10.1 Stripe Webhooks

| Event | Action |
|-------|--------|
| checkout.session.completed | Create subscription |
| customer.subscription.updated | Update tier |
| customer.subscription.deleted | Downgrade to free |
| invoice.payment_failed | Mark past_due |

**Endpoint:** POST /webhooks/stripe

---

## 11. Implementation Phases

### Phase 1: Core MVP (2 weeks)

| Task | Priority | Est. |
|------|----------|------|
| PostgreSQL setup + models | P0 | 2d |
| Alembic migrations | P0 | 1d |
| JWT auth | P0 | 2d |
| Migrate /enterprise/evaluate → /v1/evaluate | P0 | 1d |
| Migrate /enterprise/status → /v1/evaluations/{id} | P0 | 1d |
| Add /v1/certify | P0 | 2d |
| Add /v1/registry | P0 | 1d |
| Basic rate limiting | P1 | 1d |
| Deploy to Railway | P0 | 1d |

**Deliverable:** Working API at api.ontostandard.org/v1/

### Phase 2: Billing (1 week)

| Task | Priority | Est. |
|------|----------|------|
| Stripe integration | P1 | 2d |
| Checkout flow | P1 | 1d |
| Customer portal | P1 | 1d |
| Usage tracking | P1 | 1d |
| Webhook handlers | P1 | 1d |

**Deliverable:** Self-service paid subscriptions

### Phase 3: Polish (1 week)

| Task | Priority | Est. |
|------|----------|------|
| PDF report generation | P2 | 2d |
| PDF certificate generation | P2 | 1d |
| Email notifications | P2 | 1d |
| Admin endpoints | P2 | 1d |
| API documentation (OpenAPI) | P2 | 1d |

**Deliverable:** Production-ready platform

---

## 12. Migration Path from Current Code

### 12.1 Preserve

- `compute_metrics()` — работает корректно
- `compute_risk_score()` — логика валидна
- `generate_recommendations()` — сохранить
- `generate_report_html()` — базовый шаблон

### 12.2 Replace

| Current | New |
|---------|-----|
| JSON file storage | PostgreSQL |
| JSON API keys | Hashed keys in DB |
| File-based reports | S3/R2 + DB reference |
| Sync processing | Celery background tasks |
| /enterprise/ prefix | /v1/ prefix |

### 12.3 Add

- Certificate generation
- Public registry
- Stripe billing
- JWT authentication
- Audit logging

---

## 13. Security Requirements

| Requirement | Implementation |
|-------------|----------------|
| API key storage | SHA256 hash only, never plaintext |
| Password storage | bcrypt with cost 12 |
| JWT signing | RS256 with key rotation |
| HTTPS only | Enforce in production |
| CORS | Whitelist ontostandard.org |
| Input validation | Pydantic strict mode |
| SQL injection | SQLAlchemy ORM only |
| Rate limiting | Redis sliding window |
| Audit logging | All mutations logged |

---

## 14. Monitoring & Observability

| Metric | Tool |
|--------|------|
| Request latency | Prometheus + Grafana |
| Error rates | Sentry |
| API usage | Custom dashboard |
| Database performance | pg_stat_statements |
| Background jobs | Flower (Celery) |

---

## 15. Open Questions

| # | Question | Decision Needed By |
|---|----------|-------------------|
| 1 | Hosting: Railway vs Render vs Fly.io? | Phase 1 start |
| 2 | PDF generation: WeasyPrint vs Puppeteer? | Phase 3 start |
| 3 | Email provider: Resend vs Postmark? | Phase 3 start |
| 4 | Do we need GraphQL or REST only? | Phase 1 start |

---

## 16. Appendix: Pricing Tiers (Locked)

| Tier | Evaluations | Price | Duration |
|------|-------------|-------|----------|
| Pilot | 1 | Free | 14 days |
| Starter | 10 | $2,000/mo | 30 days |
| Pro | 100 | $10,000/mo | 30 days |
| Enterprise | Unlimited | $50,000/yr | 365 days |

**Certification fees (one-time):**
- Level 1: $5,000
- Level 2: $25,000
- Level 3: $75,000
- Enterprise: $150,000+

---

*Document generated: 2026-01-28*  
*Next review: Before Phase 1 start*
