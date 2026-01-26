# ONTO Canonical Site Structure

## Domain Configuration

### Primary Domain
```
onto-bench.org (or onto-standard.org)
```

### URL Structure
```
onto-bench.org/
├── /                           # Landing page
├── /standard                   # Standard landing
│   ├── /standard/v1           # ONTO-ERS-1.0 (current)
│   ├── /standard/v1/pdf       # PDF download
│   └── /standard/versions     # Version history
├── /reference                  # Reference implementation
│   ├── /reference/install     # pip install guide
│   ├── /reference/api         # API documentation
│   └── /reference/cli         # CLI documentation
├── /certified                  # Certification program
│   ├── /certified/verify      # Badge verification
│   └── /certified/apply       # Application form
├── /council                    # Standards Council
├── /benchmark                  # ONTO-Bench leaderboard
├── /enterprise                 # Enterprise services
└── /verify/{id}               # Trust Mark verification endpoint
```

---

## Required Pages

### 1. Standard Page (`/standard/v1`)

```html
<title>ONTO Epistemic Risk Standard v1.0</title>

Content:
- Executive summary (2-3 paragraphs)
- Key metrics (U-Recall, ECE)
- Compliance levels table
- Regulatory mapping summary
- PDF download link
- Citation format
- Reference implementation link
```

### 2. Reference Implementation (`/reference`)

```html
<title>ONTO Reference Implementation</title>

Content:
- pip install onto-standard
- Quick start code example
- CLI usage
- API reference link
- GitHub link
- PyPI link
```

### 3. Verification Endpoint (`/verify/{id}`)

```html
<title>ONTO Trust Mark Verification</title>

Input: Trust Mark ID
Output:
- Company name
- Certification level
- Issue date
- Expiration date
- Status (valid/expired/revoked)
```

---

## Technical Requirements

### HTTPS
- TLS 1.3 required
- HSTS enabled
- Valid certificate

### Performance
- < 2s page load
- CDN for static assets
- PDF served from CDN

### SEO
- Proper meta tags
- Structured data (JSON-LD)
- robots.txt allowing indexing

### Analytics
- Privacy-respecting (no cookies)
- Plausible or similar
- Track: page views, PDF downloads, pip install referrals

---

## Canonical URLs for Citation

### Standard Document
```
https://onto-bench.org/standard/v1

BibTeX:
@misc{onto_standard_2026,
  title = {ONTO Epistemic Risk Standard},
  author = {ONTO Standards Council},
  year = {2026},
  version = {1.0},
  url = {https://onto-bench.org/standard/v1}
}
```

### Reference Implementation
```
https://pypi.org/project/onto-standard/
https://github.com/onto-project/onto-standard
```

### Benchmark
```
https://onto-bench.org/benchmark
```

---

## Integrity Anchors

### Standard PDF Hash
```
File: ONTO-ERS-1.0.pdf
SHA-256: [hash]
Published: onto-bench.org/standard/v1
```

### Reference Impl Hash
```
Package: onto-standard-1.0.0
SHA-256: [hash from PyPI]
Published: pypi.org/project/onto-standard/1.0.0
```

### Verification Page
Display hashes at:
```
onto-bench.org/standard/v1/integrity
```

---

## DNS Configuration

### Records
```
A     onto-bench.org         → [IP]
AAAA  onto-bench.org         → [IPv6]
CNAME www.onto-bench.org     → onto-bench.org
TXT   onto-bench.org         → "v=spf1 include:_spf.google.com ~all"
```

### Cloudflare Settings (if using)
- SSL: Full (strict)
- Always Use HTTPS: On
- HSTS: On (max-age=31536000)
- Minimum TLS: 1.2

---

## Content Security

### Headers
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'
```

### Backup
- Daily backups
- Off-site storage
- Tested restore

---

## Launch Checklist

- [ ] Domain registered and configured
- [ ] SSL certificate active
- [ ] Standard page live at /standard/v1
- [ ] PDF downloadable
- [ ] Reference impl page live
- [ ] Verification endpoint functional
- [ ] Analytics installed
- [ ] Backup configured
- [ ] Integrity hashes published
