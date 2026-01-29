#!/usr/bin/env python3
"""
ONTO Full Chain Test
Signal Server → Rust Core → Notary → Certificate

This demonstrates the complete certification flow.
"""

import time
import json
import hashlib
import requests

SIGNAL_URL = "http://localhost:8081"
NOTARY_URL = "http://localhost:8082"
API_KEY = "test-api-key-12345678"

def test_full_chain():
    print("=" * 60)
    print("ONTO Full Chain Test: Signal → Core → Notary → Certificate")
    print("=" * 60)
    
    # Step 1: Get current signal
    print("\n[1/5] Fetching signal from Signal Server...")
    try:
        r = requests.get(f"{SIGNAL_URL}/signal/status", timeout=5)
        signal = r.json()
        sigma_id = signal["sigma_id"]
        print(f"      ✓ Got σ(t): {sigma_id}")
        print(f"        Entropy: {signal['entropy_preview']}...")
    except Exception as e:
        print(f"      ✗ Signal Server error: {e}")
        print("        Start with: cd onto-signal && python server.py")
        return False
    
    # Step 2: Simulate evaluation with onto_core
    print("\n[2/5] Running evaluation through Rust Core...")
    try:
        import onto_core
        onto_core.init(SIGNAL_URL)
        
        result = onto_core.evaluate(
            model_id="production-model-v2",
            predictions=[0.9, 0.1, 0.8, 0.3, 0.7, 0.2, 0.85, 0.15],
            uncertainties=[0.05, 0.1, 0.08, 0.2, 0.1, 0.15, 0.03, 0.12]
        )
        
        print(f"      ✓ Evaluation complete")
        print(f"        U-Recall: {result.u_recall:.4f}")
        print(f"        ECE: {result.ece:.4f}")
        print(f"        Risk Score: {result.risk_score:.1f}")
        print(f"        Status: {result.status}")
        print(f"        Proof Hash: {result.proof_hash}")
    except ImportError:
        print("      ✗ onto_core not installed")
        print("        Build with: cd onto-core && maturin develop")
        return False
    except Exception as e:
        print(f"      ✗ Evaluation error: {e}")
        return False
    
    # Step 3: Create Merkle root (simulated batch)
    print("\n[3/5] Creating Merkle root for batch...")
    
    # In real scenario, this comes from MerkleBatcher
    # For now, simulate with hash of proof
    merkle_root = hashlib.sha256(result.proof_hash.encode()).hexdigest()
    print(f"      ✓ Merkle Root: {merkle_root[:32]}...")
    
    # Step 4: Submit to Notary
    print("\n[4/5] Submitting to Notary for certification...")
    try:
        payload = {
            "merkle_root": merkle_root,
            "sigma_id": sigma_id,
            "model_id": "production-model-v2",
            "batch_size": 1,
            "metrics_summary": {
                "u_recall": result.u_recall,
                "ece": result.ece,
                "risk_score": result.risk_score,
                "status": result.status
            },
            "client_id": API_KEY[:16],
            "timestamp": int(time.time())
        }
        
        r = requests.post(
            f"{NOTARY_URL}/v1/sign-root",
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        if r.status_code == 200:
            cert = r.json()
            cert_id = cert["certificate_id"]
            print(f"      ✓ Certificate issued!")
            print(f"        ID: {cert_id}")
            print(f"        Signature: {cert['signature'][:32]}...")
            print(f"        Expires: {cert['expires_at']}")
        else:
            print(f"      ✗ Notary error: {r.status_code}")
            print(f"        {r.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("      ✗ Notary Server not running")
        print("        Start with: cd onto-notary && python server.py")
        return False
    except Exception as e:
        print(f"      ✗ Notary error: {e}")
        return False
    
    # Step 5: Verify certificate
    print("\n[5/5] Verifying certificate (public endpoint)...")
    try:
        r = requests.get(f"{NOTARY_URL}/registry/{cert_id}", timeout=5)
        verify = r.json()
        
        if verify.get("verified"):
            print(f"      ✓ Certificate VERIFIED!")
            print(f"        Model: {verify['model_id']}")
            print(f"        Issued: {verify['issued_at']}")
            print(f"        Batch Size: {verify['batch_size']}")
            print(f"        Metrics: {json.dumps(verify['metrics'], indent=2)}")
        else:
            print(f"      ✗ Verification failed: {verify.get('reason')}")
            return False
    except Exception as e:
        print(f"      ✗ Verify error: {e}")
        return False
    
    # Success!
    print("\n" + "=" * 60)
    print("🎉 FULL CHAIN TEST PASSED!")
    print("=" * 60)
    print(f"""
    Flow completed:
    
    1. Signal Server    → σ({sigma_id})
                           ↓
    2. Rust Core        → Poisoned metrics (drift applied)
                           ↓
    3. Merkle Batcher   → Root: {merkle_root[:16]}...
                           ↓
    4. Notary Server    → Certificate: {cert_id}
                           ↓
    5. Public Registry  → VERIFIED ✓
    
    Anyone can verify: {NOTARY_URL}/registry/{cert_id}
    """)
    
    return True


if __name__ == "__main__":
    import sys
    success = test_full_chain()
    sys.exit(0 if success else 1)
