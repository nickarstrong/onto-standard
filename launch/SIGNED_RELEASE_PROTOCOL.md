# ONTO Signed Release Protocol

## Cryptographic Integrity for Institutional Trust

---

## WHY SIGNED RELEASES MATTER

Regulators and enterprise procurement require:
1. **Tamper evidence**: Know if something changed
2. **Attribution**: Know who published it
3. **Permanence**: Verify years later

Unsigned releases = "trust me bro"
Signed releases = verifiable institutional artifact

---

## GPG KEY SETUP

### 1. Generate Key (if not exists)

```bash
gpg --full-generate-key

# Select:
# - RSA and RSA
# - 4096 bits
# - 2 years expiry
# - Real name: ONTO Standards Council
# - Email: standards@onto-bench.org
```

### 2. Export Public Key

```bash
# Export for publication
gpg --armor --export standards@onto-bench.org > ONTO_SIGNING_KEY.asc

# Fingerprint (publish this)
gpg --fingerprint standards@onto-bench.org
```

### 3. Publish Key

Upload to:
- onto-bench.org/gpg-key
- keys.openpgp.org
- keyserver.ubuntu.com

---

## SIGNING THE STANDARD PDF

### 1. Generate PDF

```bash
# From LaTeX or markdown
pandoc ONTO_STANDARD_v1.0.md -o ONTO-ERS-1.0.pdf
```

### 2. Create Detached Signature

```bash
gpg --armor --detach-sign ONTO-ERS-1.0.pdf
# Creates: ONTO-ERS-1.0.pdf.asc
```

### 3. Verify Signature

```bash
gpg --verify ONTO-ERS-1.0.pdf.asc ONTO-ERS-1.0.pdf
# Should show: Good signature from "ONTO Standards Council"
```

### 4. Generate Hash

```bash
sha256sum ONTO-ERS-1.0.pdf > ONTO-ERS-1.0.pdf.sha256
```

---

## SIGNING GIT RELEASES

### 1. Configure Git Signing

```bash
git config --global user.signingkey [KEY_ID]
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

### 2. Create Signed Tag

```bash
git tag -s v1.0.0 -m "ONTO Standard v1.0.0 - Initial Release

ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)
Reference implementation release.

Standard: https://onto-bench.org/standard/v1
"

# Verify
git tag -v v1.0.0
```

### 3. Push Signed Tag

```bash
git push origin v1.0.0
```

---

## PYPI RELEASE VERIFICATION

### 1. Note PyPI Hashes

After upload, PyPI shows hashes:
```
SHA256: abc123...
```

### 2. Document in CHECKSUMS.txt

```
# ONTO Standard v1.0.0 Release Checksums
# Generated: 2026-01-XX

## Standard Document
ONTO-ERS-1.0.pdf
SHA-256: [hash]

## Reference Implementation
onto_standard-1.0.0-py3-none-any.whl
SHA-256: [hash from PyPI]

onto_standard-1.0.0.tar.gz
SHA-256: [hash from PyPI]

## Verification
GPG Key: https://onto-bench.org/gpg-key
Fingerprint: XXXX XXXX XXXX XXXX XXXX
```

---

## INTEGRITY PAGE

Create at `onto-bench.org/standard/v1/integrity`:

```html
<h1>ONTO-ERS-1.0 Integrity Verification</h1>

<h2>Standard Document</h2>
<table>
  <tr><td>File</td><td>ONTO-ERS-1.0.pdf</td></tr>
  <tr><td>SHA-256</td><td><code>[hash]</code></td></tr>
  <tr><td>Signature</td><td><a href="ONTO-ERS-1.0.pdf.asc">Download</a></td></tr>
</table>

<h2>Reference Implementation</h2>
<table>
  <tr><td>Package</td><td>onto-standard 1.0.0</td></tr>
  <tr><td>PyPI</td><td>pypi.org/project/onto-standard/1.0.0</td></tr>
  <tr><td>SHA-256 (wheel)</td><td><code>[hash]</code></td></tr>
</table>

<h2>GPG Public Key</h2>
<p>Fingerprint: <code>XXXX XXXX XXXX XXXX XXXX</code></p>
<p><a href="/gpg-key">Download Public Key</a></p>

<h2>Verification Instructions</h2>
<pre>
# Import key
gpg --import ONTO_SIGNING_KEY.asc

# Verify PDF
gpg --verify ONTO-ERS-1.0.pdf.asc ONTO-ERS-1.0.pdf

# Verify pip package
pip download onto-standard==1.0.0 --no-deps
sha256sum onto_standard-1.0.0-py3-none-any.whl
# Compare with hash above
</pre>
```

---

## GITHUB RELEASE SETTINGS

### Enable Verified Commits

In repository settings:
- Require signed commits (optional but recommended)
- Show verified badge on releases

### Release Assets

Upload to each release:
- `ONTO-ERS-1.0.pdf`
- `ONTO-ERS-1.0.pdf.asc` (signature)
- `CHECKSUMS.txt`
- `onto_standard-1.0.0-py3-none-any.whl`
- `onto_standard-1.0.0.tar.gz`

---

## SIGNING CHECKLIST

### Before Release

- [ ] GPG key generated and published
- [ ] Git configured for signing
- [ ] Standard PDF finalized

### During Release

- [ ] PDF signed with detached signature
- [ ] SHA256 hash generated
- [ ] Git tag signed
- [ ] PyPI upload completed
- [ ] PyPI hashes recorded

### After Release

- [ ] Integrity page updated
- [ ] CHECKSUMS.txt committed
- [ ] GitHub release assets uploaded
- [ ] Verification tested

---

## VERIFICATION BY THIRD PARTIES

### For Auditors

```bash
# 1. Get the signing key
curl -O https://onto-bench.org/gpg-key
gpg --import gpg-key

# 2. Verify the standard
curl -O https://onto-bench.org/standard/v1/ONTO-ERS-1.0.pdf
curl -O https://onto-bench.org/standard/v1/ONTO-ERS-1.0.pdf.asc
gpg --verify ONTO-ERS-1.0.pdf.asc ONTO-ERS-1.0.pdf

# 3. Verify the package
pip download onto-standard==1.0.0 --no-deps
sha256sum onto_standard-1.0.0-py3-none-any.whl
# Compare with published hash
```

### For Enterprise Procurement

Include in RFP response:
```
The ONTO Epistemic Risk Standard v1.0 is cryptographically 
signed and verifiable. Integrity verification instructions 
are available at onto-bench.org/standard/v1/integrity.

GPG Fingerprint: XXXX XXXX XXXX XXXX XXXX
```

---

## KEY ROTATION PROTOCOL

### Annual Key Renewal

1. Generate new key 60 days before expiry
2. Sign new key with old key (cross-signing)
3. Publish transition notice
4. Update signing infrastructure
5. Revoke old key after transition period

### Emergency Key Revocation

If key compromised:
1. Generate revocation certificate
2. Publish to keyservers
3. Generate new key
4. Re-sign all active releases
5. Publish security advisory

---

*ONTO Signed Release Protocol v1.0*
*Cryptographic integrity for institutional trust*
