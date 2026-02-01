# ONTO-Bench Leaderboard Infrastructure

## Overview

Public leaderboard for epistemic calibration benchmarking. Forces AI labs to compare on calibration metrics.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  onto-bench.org                  │
├─────────────────────────────────────────────────┤
│  Frontend (React/Next.js)                       │
│  - Leaderboard table                            │
│  - Submission form                              │
│  - Dataset download                             │
│  - Paper/citation info                          │
├─────────────────────────────────────────────────┤
│  Backend (FastAPI)                              │
│  - /api/submit       POST predictions           │
│  - /api/leaderboard  GET rankings               │
│  - /api/evaluate     Compute metrics            │
│  - /api/dataset      Download test set (no GT)  │
├─────────────────────────────────────────────────┤
│  Storage                                        │
│  - PostgreSQL: submissions, users               │
│  - S3: prediction files, logs                   │
│  - Redis: cache                                 │
└─────────────────────────────────────────────────┘
```

---

## API Specification

### Submit Predictions

```http
POST /api/submit
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "model_name": "gpt-4-turbo",
  "model_version": "2024-01-25",
  "organization": "OpenAI",
  "predictions": [
    {"id": "sample_001", "label": "KNOWN", "confidence": 0.85},
    {"id": "sample_002", "label": "UNKNOWN", "confidence": 0.72},
    ...
  ],
  "metadata": {
    "temperature": 0,
    "system_prompt": "...",
    "timestamp": "2024-01-26T12:00:00Z"
  }
}
```

Response:
```json
{
  "submission_id": "sub_abc123",
  "status": "pending",
  "message": "Evaluation in progress"
}
```

### Get Leaderboard

```http
GET /api/leaderboard?sort=u_f1&limit=20
```

Response:
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "model": "ONTO",
      "organization": "ONTO Project",
      "u_precision": 0.41,
      "u_recall": 0.96,
      "u_f1": 0.58,
      "ece": 0.30,
      "submitted_at": "2024-01-26",
      "verified": true
    },
    {
      "rank": 2,
      "model": "Claude 3 Sonnet",
      "organization": "Anthropic",
      "u_f1": 0.15,
      ...
    }
  ],
  "last_updated": "2024-01-26T16:00:00Z"
}
```

---

## Database Schema

```sql
CREATE TABLE submissions (
    id UUID PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(100),
    organization VARCHAR(255),
    
    -- Metrics (computed)
    u_precision FLOAT,
    u_recall FLOAT,
    u_f1 FLOAT,
    c_f1 FLOAT,
    ece FLOAT,
    brier_score FLOAT,
    accuracy FLOAT,
    
    -- Metadata
    predictions_file VARCHAR(500),
    config JSONB,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    verified BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    submitted_at TIMESTAMP DEFAULT NOW(),
    evaluated_at TIMESTAMP
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    organization VARCHAR(255),
    api_key VARCHAR(64) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_submissions_u_f1 ON submissions(u_f1 DESC);
CREATE INDEX idx_submissions_ece ON submissions(ece ASC);
```

---

## Frontend Components

### Leaderboard Table

```tsx
// components/Leaderboard.tsx
export function Leaderboard({ data }) {
  return (
    <table className="w-full">
      <thead>
        <tr>
          <th>Rank</th>
          <th>Model</th>
          <th>Org</th>
          <th>U-F1 ↑</th>
          <th>U-Recall ↑</th>
          <th>ECE ↓</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={row.id} className={i === 0 ? 'bg-green-50' : ''}>
            <td>{row.rank}</td>
            <td className="font-bold">{row.model}</td>
            <td>{row.organization}</td>
            <td>{row.u_f1.toFixed(2)}</td>
            <td>{row.u_recall.toFixed(2)}</td>
            <td>{row.ece.toFixed(2)}</td>
            <td>{row.submitted_at}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### Submission Form

```tsx
// components/SubmitForm.tsx
export function SubmitForm() {
  const [file, setFile] = useState(null);
  
  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append('predictions', file);
    formData.append('model_name', modelName);
    
    await fetch('/api/submit', {
      method: 'POST',
      body: formData,
      headers: { Authorization: `Bearer ${apiKey}` }
    });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input type="file" accept=".jsonl" onChange={e => setFile(e.target.files[0])} />
      <input type="text" placeholder="Model name" />
      <button type="submit">Submit</button>
    </form>
  );
}
```

---

## Evaluation Pipeline

```python
# leaderboard/evaluate.py

def evaluate_submission(predictions_file: str) -> dict:
    """Evaluate submission against hidden test set."""
    
    # Load predictions
    predictions = load_jsonl(predictions_file)
    
    # Load ground truth (hidden)
    ground_truth = load_ground_truth()  # Not public
    
    # Validate format
    validate_predictions(predictions, ground_truth)
    
    # Compute metrics
    metrics = {
        "u_precision": compute_u_precision(predictions, ground_truth),
        "u_recall": compute_u_recall(predictions, ground_truth),
        "u_f1": compute_u_f1(predictions, ground_truth),
        "ece": compute_ece(predictions, ground_truth),
        "brier_score": compute_brier(predictions, ground_truth),
        "accuracy": compute_accuracy(predictions, ground_truth),
    }
    
    return metrics
```

---

## Deployment

### Infrastructure

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:8000
  
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
  
  redis:
    image: redis:7

volumes:
  pgdata:
```

### Hosting Options

| Option | Cost | Pros | Cons |
|--------|------|------|------|
| Vercel + Supabase | $0-20/mo | Easy, free tier | Limited compute |
| Railway | $5-20/mo | Simple, good DX | Less control |
| AWS | $50+/mo | Full control | Complex |
| Cloudflare Pages + D1 | $0-5/mo | Edge, fast | New stack |

**Recommendation**: Vercel (frontend) + Railway (API) + Supabase (DB)

---

## Anti-Gaming Measures

1. **Hidden test set**: Ground truth labels not public
2. **Submission limits**: 3 per day per organization
3. **Confidence audit**: Suspicious confidence patterns flagged
4. **Manual verification**: Top submissions reviewed
5. **Version tracking**: Model version required

---

## Launch Checklist

- [ ] Domain: onto-bench.org
- [ ] API deployed
- [ ] Frontend deployed
- [ ] Database seeded with initial submissions
- [ ] SSL certificates
- [ ] Rate limiting
- [ ] Monitoring (Sentry, Datadog)
- [ ] Documentation
- [ ] Terms of service
