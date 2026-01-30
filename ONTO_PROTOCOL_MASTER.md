# ONTO PROTOCOL — MASTER DOCUMENT

**Version:** 2.3  
**Date:** 2026-01-30  
**Status:** CANONICAL  
**Purpose:** Knowledge transfer between sessions

---

## 0. EXECUTION PROTOCOL (Claude ↔ Tommy)

### 0.1 Core Loop

```
┌─────────────────────────────────────────────────────────┐
│  ROADMAP → PATCH → DEPLOY → CHECK → TEST → FIX → NEXT  │
└─────────────────────────────────────────────────────────┘
```

| Step | Who | Action |
|------|-----|--------|
| **ROADMAP** | Claude | Определяет следующую задачу по приоритету |
| **PATCH** | Claude | Создаёт файлы → ZIP → Downloads |
| **DEPLOY** | Tommy | Запускает PS команды |
| **CHECK** | Tommy | Проверяет терминалы/порты |
| **TEST** | Tommy | Запускает, тестирует endpoints |
| **FIX** | Claude | Если баг — фиксит |
| **NEXT** | Claude | Следующая задача по roadmap |
| **GIT** | Tommy | Периодически commit + push |

### 0.2 Output Format (Claude)

```
[STAGE]     Название этапа
[ACTION]    Что делаю
[FILE]      → путь/к/файлу
[CMD]       PS команда для Tommy
[CLOSED]    Этап закрыт
```

### 0.3 Deploy Commands (Tommy)

```powershell
# Extract
Expand-Archive -Path "$env:USERPROFILE\Downloads\{name}.zip" `
               -DestinationPath "$env:USERPROFILE\Downloads\{name}" -Force

# Copy to target
Copy-Item -Path "$env:USERPROFILE\Downloads\{name}\*" `
          -Destination "C:\ONTO\{target}\" -Force

# Git
cd C:\ONTO
git add .
git commit -m "{message}"
git push origin main
```

### 0.4 File Locations

```
C:\ONTO\                    ← Main repo (GitHub sync)
C:\ONTO\onto-internal\      ← Private docs
C:\ONTO\backend\            ← API backend
C:\ONTO\onto-signal\        ← Signal server
C:\ONTO\onto-notary\        ← Notary server
$env:USERPROFILE\Downloads\ ← Patch landing zone
```

### 0.5 Rules

```
[MUST]  Полные пути в PS
[MUST]  RU язык
[MUST]  "Stage CLOSED" в конце этапа
[MUST]  Указывать куда класть файл
[MUST]  Проверять порты перед запуском
[MUST]  РЕДАКТИРОВАТЬ файлы, НЕ ПЕРЕПИСЫВАТЬ заново
[MUST]  Составлять ROADMAP самостоятельно до production
[MUST]  Следовать ROADMAP даже после патчей/отклонений
[MUST]  Отмечать выполненные задачи в этом протоколе
[MUST]  Вписывать новые задачи в логической последовательности
[MUST]  Быть инициатором улучшений и патчей
[MUST]  Оценивать предложенный вариант и улучшать до 10/10
[MUST]  Использовать ТОЛЬКО утверждённый дизайн (см. 0.11)
[DO]    Сразу делать, не спрашивать
[DO]    Один вариант, лучший
[DO]    Следовать логической последовательности
[DO]    Явно сообщать если данных нет
[DO]    Самостоятельно определять что делать первым
[DONT]  Варианты/brainstorm
[DONT]  Код без пути назначения
[DONT]  Объяснять очевидное
[DONT]  Удалять существующий контент при обновлении
[DONT]  Спрашивать "что делаем первым?"
```

### 0.6 Identity

```yaml
role: Product Engineer
mode: Execution & Delivery
language: RU
verbosity: Minimal
```

### 0.7 Analysis Framework (при аудите)

```
┌────────────────────────────────────────────┐
│  1. CLIENT      │  User experience, UX     │
│  2. ADMIN       │  Management, control     │
│  3. SECURITY    │  Auth, encryption, keys  │
│  4. CODE        │  Clean, typed, tested    │
│  5. MAINTAIN    │  Easy to change/fix      │
│  6. ENGINEERING │  Infra, scale, HA        │
└────────────────────────────────────────────┘
```

### 0.8 Priority Order

```
INFRASTRUCTURE:  DB Schema → Validation → Security → Features → UI
FEATURES:        Backend → API → Integration → Frontend
FIXES:           Critical → High → Medium → Low
```

### 0.9 Terminal Management

```powershell
# Check ports
Get-NetTCPConnection -LocalPort 8081,8082 -ErrorAction SilentlyContinue

# Kill process on port
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8081).OwningProcess -Force

# Check processes
Get-Process python, cloudflared -ErrorAction SilentlyContinue
```

### 0.10 Status Checks

```powershell
# Backend
Invoke-RestMethod -Uri "https://api.ontostandard.org/health"

# Signal
Invoke-RestMethod -Uri "https://signal.ontostandard.org/signal/status"

# Notary
Invoke-RestMethod -Uri "https://notary.ontostandard.org/health"
```

### 0.11 Design System (IMMUTABLE)

**Fonts:**
- Primary: Inter (400, 500, 600, 700, 800)
- Mono: JetBrains Mono (400, 500, 600, 700)

**Light Theme:**
```css
--bg: #ffffff;
--bg-secondary: #f9fafb;
--bg-card: #ffffff;
--bg-elevated: #f3f4f6;
--border: #e5e7eb;
--border-hover: #d1d5db;
--text: #111827;
--text-secondary: #6b7280;
--text-muted: #9ca3af;
--accent: #3b82f6;
--danger: #ef4444;
--safe: #22c55e;
--warning: #f59e0b;
```

**Dark Theme:**
```css
--bg: #0f0f10;
--bg-secondary: #18181b;
--bg-card: #1f1f23;
--bg-elevated: #27272a;
--border: #3f3f46;
--border-hover: #52525b;
--text: #fafafa;
--text-secondary: #a1a1aa;
--text-muted: #71717a;
```

**Reference:** `onto-v15-1-95-percent.html`

### 0.12 Current ROADMAP

```
STATUS KEY: ✅ Done | 🔄 In Progress | ⏳ Pending | ❌ Blocked

INFRASTRUCTURE:
  ✅ Backend refactor (tier → layer)
  ✅ Signal delay (OPEN +1h)
  ✅ Watermark (OPEN)
  ✅ Certificate limits
  ✅ Audit trail endpoint (CRITICAL)
  ✅ Register endpoint fix (pilot → open)
  ⏳ DB schema validation
  
API:
  ✅ /v1/signal/current (layer-aware)
  ✅ /v1/audit (CRITICAL only)
  🔄 Full user flow test
  
FRONTEND:
  ⏳ Landing page (Connect to Protocol)
  ⏳ Client Portal integration
  
PAYMENTS:
  ⏳ Airwallex integration
  
PRODUCTION CHECKLIST:
  ✅ User can register
  ⏳ User can get API key
  ⏳ User can submit evaluation
  ⏳ User can get certificate
  ⏳ Public verify works
```

### 0.13 Test Credentials (REUSE!)

```
Company:  ONTO Test Org
Email:    test@ontostandard.org
Password: OntoTest2026!
API Key:  (получить после первой регистрации)
Layer:    open
```

**НЕ создавать новые тестовые компании — использовать эти!**

---

## 1. WHAT IS ONTO

### 1.1 Core Definition

ONTO — это **протокол верификации надёжности ИИ**, а не SaaS продукт.

```
ONTO = Base Layer (как TCP/IP, HTTP)
     = Единый сигнал + Единое ядро + Бесконечность применений
     = "Мы измеряем температуру. Мы не лечим пациента."
```

### 1.2 Philosophy

> "Мы создали Ядро, которое непредвзято. Оно не знает, кто ты — священник, биолог или создатель терминаторов. Оно просто гарантирует, что твой слой данных не врет."

**Tommy = Эволюционер, не институтка.**

Проект создаёт фундаментальный слой, на который разные индустрии накладывают свой смысл:
- AI Labs → верификация что модель не галлюцинирует
- Медицина → цена ошибки = жизнь
- Робототехника → AI-to-AI протокол
- Наука → детерминация данных
- Финансы → аудит AI-решений

### 1.3 What ONTO Does

| ONTO делает | ONTO НЕ делает |
|-------------|----------------|
| Измеряет calibration (ECE) | Не улучшает модель |
| Измеряет uncertainty (U-Recall) | Не лечит галлюцинации |
| Выдаёт Risk Score | Не гарантирует качество модели |
| Подписывает Certificate | Не несёт ответственность за модель клиента |
| Хранит в публичном реестре | Не видит данные клиента (только хэши) |

**Ключевая метафора:** ONTO — это градусник, а не врач. Мы измеряем температуру, но не лечим пациента.

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 Components

```
┌─────────────────────────────────────────────────────────────┐
│                      ONTO PROTOCOL                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   SIGNAL    │    │    CORE     │    │   NOTARY    │     │
│  │   SERVER    │    │   (SDK)     │    │   SERVER    │     │
│  │             │    │             │    │             │     │
│  │ 104 bytes   │───▶│ ECE, U-Rec  │───▶│ ED25519     │     │
│  │ hourly σ(t) │    │ Risk Score  │    │ Certificate │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                                     │             │
│         │                                     ▼             │
│         │                          ┌─────────────────┐     │
│         │                          │  PUBLIC REGISTRY │     │
│         │                          │  verify.onto...  │     │
│         │                          └─────────────────┘     │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   BACKEND API                        │   │
│  │  • Auth (register, login, API keys)                  │   │
│  │  • Evaluations (submit, list, get)                   │   │
│  │  • Certificates (issue, verify)                      │   │
│  │  • Billing (layers, invoices)                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Signal (σ)

| Parameter | Value |
|-----------|-------|
| Size | 104 bytes |
| Broadcast | Hourly |
| Cryptography | ED25519 signature |
| Purpose | Temporal binding — prevents backdating |

**Signal создаёт "пульс реальности"** — криптографическую энтропию, которая привязывает каждый расчёт к конкретному моменту времени.

### 2.3 Core Mathematics

| Metric | What it measures | Range |
|--------|------------------|-------|
| **ECE** | Expected Calibration Error — насколько уверенность модели соответствует реальной точности | 0.0 - 1.0 (ниже = лучше) |
| **U-Recall** | Uncertainty Recall — умеет ли модель говорить "я не знаю" | 0.0 - 1.0 (выше = лучше) |
| **Risk Score** | Composite risk indicator | 0 - 100 (ниже = лучше) |

**Математика ОДИНАКОВАЯ для всех Layers.** Ядро не "урезается".

### 2.4 Certificate

```json
{
  "certificate_id": "cert_a1b2c3d4",
  "organization_id": "org_xyz789",
  "model_id": "gpt-4-medical",
  "timestamp": "2026-01-30T15:30:00Z",
  "sigma_hash": "0x7f3a...",
  "metrics": {
    "ece": 0.08,
    "u_recall": 0.85,
    "risk_score": 25
  },
  "signature": "ed25519_sig_...",
  "status": "VALID"
}
```

Verification: https://verify.ontostandard.org/{certificate_id}

---

## 3. BUSINESS MODEL: LAYERS (не Tiers!)

### 3.1 Paradigm

```
НЕ продаём софт.
Взимаем налог на легитимность.

Вычисления в ядре = БЕСПЛАТНО (клиент тратит свои ресурсы)
Печать в реестре = ПЛАТНО (gas fee за верификацию)
```

### 3.2 Three Layers

```
────────────────────────────────────────────────────────────────

     ◠─────◠              ◠─────◠              ◠─────◠
    ╱   ↑   ╲            ╱   ↗   ╲            ╱    →   ╲
   ░░░░░░░░░░░          ████████░░░          ███████████
   
      OPEN                STANDARD              CRITICAL
       $0                 $15,000               $100,000+
                          /year                  /year

────────────────────────────────────────────────────────────────
```

| Parameter | OPEN | STANDARD | CRITICAL |
|-----------|------|----------|----------|
| **Price** | $0 | $15,000/year | $100,000+/year |
| **Signal** | +1 hour delay | Real-time | Real-time |
| **Certificates** | 100/month | 10,000/year | Unlimited |
| **Watermark** | "ONTO Open" badge | Clean | Clean |
| **Audit Trail** | ❌ | ❌ | ✅ 24 months |
| **Support** | Community | Email 48h | Dedicated 4h |
| **SLA** | Best effort | 99.9% | 99.99% |
| **Attribution** | Required | No | No |

### 3.3 Layer Logic

**OPEN (Genesis)** — $0
- Для: учёные, open source, стартапы в R&D
- Signal с задержкой +1 час (нельзя использовать для production fraud)
- Watermark на сертификатах
- Обязательная атрибуция: "Verified by ONTO Open Source"

**STANDARD (Business)** — $15,000/year
- Для: AI Labs, SaaS, дроны, коммерческие AI
- Real-time signal
- Чистые сертификаты без watermark
- Overage: $1/certificate сверх 10,000

**CRITICAL (Life & Logic)** — $100,000+/year
- Для: медицина, автономные системы, банки, ВПК
- Unlimited certificates
- Audit Trail 24 месяца
- Dedicated support
- Custom pricing

### 3.4 Why Signal Delay for OPEN?

Технически честный способ разделить Layers без "урезания" математики:
- Математика одинаковая
- Но delayed signal нельзя использовать для realtime production
- Это защита экосистемы, а не paywall

---

## 4. LEGAL FRAMEWORK

### 4.1 Documents

| Document | Purpose | File |
|----------|---------|------|
| **MSA** | Master Service Agreement | MSA_TEMPLATE.md |
| **PAA** | Protocol Access Agreement (бывший SOW) | SOW_TEMPLATE.md |
| **DPA** | Data Processing Agreement (GDPR) | DPA_TEMPLATE.md |
| **CP** | Certificate Policy (для регуляторов) | CP_TEMPLATE.md |
| **INV** | Invoice | INV_TEMPLATE.md |

### 4.2 Key Clauses

**"Градусник не врач" (MSA Section 10.1):**
> ONTO is a measurement instrument, not a remediation tool. ONTO shall have no liability for hallucinations, errors, or inaccuracies in Client's AI model outputs.

**SLA Split (MSA Section 3.2):**
- Availability SLA: 99.9% uptime
- Integrity SLA: Every certificate has valid signature + temporal binding

**SLA Exclusions (MSA Section 3.3):**
- Client's network issues = client's problem
- We broadcast signal, they must receive it

**Audit Clause (MSA Section 3.7):**
- SOC2/ISO reports: YES
- Physical server audit: NO (protects other clients)

### 4.3 Compliance Pack by Layer

| Layer | Documents |
|-------|-----------|
| OPEN | MSA + PAA + CP (watermark) |
| STANDARD | MSA + PAA + CP + INV |
| STANDARD (EU) | MSA + PAA + DPA + CP + INV |
| CRITICAL | MSA + PAA + DPA + CP + INV + Custom |

---

## 5. TARGET CLIENTS

### 5.1 Priority Order

| # | Segment | Pain Point | Error Cost |
|---|---------|------------|------------|
| 1 | **AI Labs** | Prove model doesn't hallucinate | Reputation, $$ |
| 2 | **Medicine** | AI diagnosis must be reliable | Human life |
| 3 | **Robotics** | AI-to-AI protocol for drones/autonomous | Crashes, deaths |
| 4 | **Finance** | AI trading/scoring audit | Millions $$ |

### 5.2 Value Proposition by Segment

**AI Labs:**
> "Your model costs millions to train. Its reliability costs $0 without our signature. Protocol access is cheap insurance."

**Medicine:**
> "ONTO Certificate = mathematical guarantee that diagnostic AI knew its confidence limits at evaluation time."

**Robotics:**
> "When one AI tells another AI 'fly there', both need deterministic verification that the instruction isn't corrupted."

---

## 6. MONETIZATION CONTEXT

### 6.1 Jurisdiction

**UZ IT Park (Uzbekistan)**
- 0% corporate tax
- 0% VAT
- 7.5% personal income tax (minimum)
- Payment via Airwallex (USD/EUR accounts)

### 6.2 Payment Flow

```
Client → Invoice (PDF + PO) → Wire/ACH → Airwallex → TBC Bank UZ
```

### 6.3 No Stripe

Wire/ACH only for enterprise. No chargebacks, no credit cards.

---

## 7. PRODUCTION URLS

| Service | URL | Status |
|---------|-----|--------|
| Backend API | https://api.ontostandard.org | ✅ LIVE |
| Signal Server | https://signal.ontostandard.org | ⚠️ 403 (needs fix) |
| Notary Server | https://notary.ontostandard.org | ✅ LIVE |
| Website | https://ontostandard.org | ✅ LIVE |
| Verify | https://verify.ontostandard.org | ✅ LIVE |
| Docs | https://docs.ontostandard.org | ✅ LIVE |

**Railway Project:** glorious-delight

---

## 8. TERMINOLOGY

### 8.1 Correct Terms (v2)

| Use This | NOT This |
|----------|----------|
| Layer | ~~Tier~~ |
| OPEN / STANDARD / CRITICAL | ~~L1 / L2 / L3~~ |
| Protocol Access | ~~Subscription~~ |
| Connect to Protocol | ~~Buy~~ |
| Certificate allocation | ~~Slots~~ |
| Protocol Access Agreement (PAA) | ~~SOW~~ |

### 8.2 Key Phrases

- "One signal — infinite layers"
- "We measure the temperature. We don't cure the patient."
- "ONTO is a measurement instrument, not a remediation tool."
- "Tax on legitimacy, not software subscription"
- "Base layer for AI verification"

---

## 9. FILE STRUCTURE

### 9.1 Legal Templates

```
/legal/
├── MSA_TEMPLATE.md       # Master Service Agreement
├── SOW_TEMPLATE.md       # Protocol Access Agreement (PAA)
├── DPA_TEMPLATE.md       # Data Processing Agreement
├── CP_TEMPLATE.md        # Certificate Policy
├── INV_TEMPLATE.md       # Invoice
└── compliance_generator.py  # Python generator for all docs
```

### 9.2 Generator Usage

```bash
python compliance_generator.py \
  --client-name "MedTech AI Corp" \
  --client-address "500 Health Avenue" \
  --client-email "billing@medtech.ai" \
  --layer CRITICAL \
  --eu
```

Layers: `OPEN`, `STANDARD`, `CRITICAL`

---

## 10. CURRENT STATUS

### 10.1 Completed ✅

- [x] MSA v2 (Protocol Access, Layers)
- [x] PAA/SOW v2 (Layer specs, no slots)
- [x] DPA (GDPR ready)
- [x] CP v2 (Layers)
- [x] Invoice v2 (Layer pricing)
- [x] Compliance Generator v2
- [x] "Градусник" clause
- [x] SLA Split clause
- [x] Client Portal MVP (HTML)

### 10.2 TODO

- [ ] Signal 403 fix (Railway access needed)
- [ ] Backend: replace tier logic with layers
- [ ] Client Portal: integrate with backend
- [ ] Landing page: "Connect to Protocol" flow
- [ ] Airwallex integration (waiting on account)

---

## 11. CONTACT

- **Protocol:** protocol@ontostandard.org
- **Sales:** sales@ontostandard.org
- **Technical:** admin@ontostandard.org
- **GitHub:** nickarstrong/onto-standard

---

## 12. SESSION HISTORY

This document synthesizes decisions from multiple sessions:
- UZ IT Park monetization (0% tax)
- Enterprise billing (Wire/ACH, Airwallex)
- Legal templates (MSA, SOW, DPA, CP, INV)
- **Paradigm shift: Tiers → Layers**
- **Philosophy: Protocol, not SaaS**
- **"Градусник не врач" principle**
- Speedometer visualization concept

---

*ONTO Protocol Master Document v2.0*
*This is the canonical reference for project understanding.*
