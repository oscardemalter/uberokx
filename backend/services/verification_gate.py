import hashlib, json
from pathlib import Path
from backend.config import settings
class VerificationGate:
    def pine_hash(self):
        p = Path(settings.VERIFICATION_PINE_PATH)
        if not p.is_file(): return "0"*64
        data = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return hashlib.sha256(data).hexdigest()
    def record(self):
        p = Path(settings.VERIFICATION_RECORDS_PATH)
        if not p.is_file(): return None
        try: data = json.loads(p.read_text(encoding="utf-8"))
        except Exception: return None
        for r in data.get("records", []):
            if r.get("id") == "TV-UBEROX-EMITTER-001": return r
        return None
    def is_verified(self):
        r = self.record()
        return bool(r and r.get("result") == "pass" and r.get("sha256") == self.pine_hash())
    def status(self):
        r = self.record() or {}
        return {"verified": self.is_verified(), "record": r.get("id"), "result": r.get("result"),
                "tested_on": r.get("tested_on"), "hash_match": bool(r.get("sha256") == self.pine_hash()),
                "pine_sha256": self.pine_hash()[:16]}
verification_gate = VerificationGate()
