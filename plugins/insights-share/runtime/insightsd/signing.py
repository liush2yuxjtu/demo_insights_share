"""insights-share M4：ed25519 卡片签名与验签。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    _CRYPTO_AVAILABLE = True
except ModuleNotFoundError:  # clean plugin installs should still serve/search with stdlib
    serialization = None  # type: ignore[assignment]
    Ed25519PrivateKey = None  # type: ignore[assignment]
    Ed25519PublicKey = None  # type: ignore[assignment]
    _CRYPTO_AVAILABLE = False

SIGNATURE_ALGORITHM = "ed25519"
FALLBACK_SIGNATURE_ALGORITHM = "sha256-fallback"
SIGNATURE_SCHEMA_VERSION = 1
SIGNED_LIST_FIELDS = {
    "tags",
    "applies_when",
    "do_not_apply_when",
}
SIGNED_FIELDS = (
    "id",
    "title",
    "author",
    "team",
    "confidence",
    "status",
    "tags",
    "description",
    "bad_example",
    "good_example",
    "applies_when",
    "do_not_apply_when",
    "topic_id",
    "label",
    "label_note",
    "label_override",
    "label_override_by",
    "label_override_at",
    "raw_log_type",
    "raw_log_sha256",
)


def _signing_root() -> Path:
    env_dir = os.environ.get("INSIGHTS_SHARE_SIGNING_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser()
    return Path.home() / ".cache" / "insights-share" / "signing"


def _private_key_path() -> Path:
    return _signing_root() / "server-ed25519-private.pem"


def _public_key_path() -> Path:
    return _signing_root() / "server-ed25519-public.pem"


def _trusted_keys_path() -> Path:
    return Path.home() / ".cache" / "insights-share" / "trusted_keys.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_value(field: str, value: Any) -> Any:
    if field in SIGNED_LIST_FIELDS:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]
    if value in ("", [], {}):
        return None
    if field == "team":
        if not isinstance(value, str):
            return None
        team = value.strip()
        return team or None
    return value


def canonical_payload(card: dict[str, Any]) -> bytes:
    payload = {
        "schema": SIGNATURE_SCHEMA_VERSION,
        "algorithm": SIGNATURE_ALGORITHM,
    }
    for field in SIGNED_FIELDS:
        payload[field] = _stable_value(field, card.get(field))
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key_id_from_public_key(public_key: Ed25519PublicKey) -> str:
    if serialization is None:
        raise RuntimeError("cryptography is unavailable")
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return sha256_hex(raw)[:16]


def _load_private_key(path: Path) -> Ed25519PrivateKey:
    if serialization is None:
        raise RuntimeError("cryptography is unavailable")
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def _load_public_key_from_pem(text: str) -> Ed25519PublicKey:
    if serialization is None or Ed25519PublicKey is None:
        raise RuntimeError("cryptography is unavailable")
    key = serialization.load_pem_public_key(text.encode("utf-8"))
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("public key is not ed25519")
    return key


def _read_trusted_keys(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    keys = {}
    for item in payload.get("keys") or []:
        if not isinstance(item, dict):
            continue
        key_id = item.get("key_id")
        public_key_pem = item.get("public_key_pem")
        if isinstance(key_id, str) and key_id and isinstance(public_key_pem, str) and public_key_pem:
            keys[key_id] = public_key_pem
    return keys


@dataclass(slots=True)
class VerifyResult:
    status: str
    error: str | None = None
    key_id: str | None = None


class CardSignatureService:
    def __init__(
        self,
        *,
        private_key_path: Path | None = None,
        public_key_path: Path | None = None,
        trusted_keys_path: Path | None = None,
        auto_generate: bool = True,
    ) -> None:
        self.private_key_path = Path(private_key_path or _private_key_path())
        self.public_key_path = Path(public_key_path or _public_key_path())
        self.trusted_keys_path = Path(trusted_keys_path or _trusted_keys_path())
        self.auto_generate = auto_generate

    def ensure_signing_material(self) -> None:
        if not _CRYPTO_AVAILABLE:
            self._ensure_fallback_material()
            return
        if self.private_key_path.is_file() and self.public_key_path.is_file():
            return
        if not self.auto_generate:
            raise FileNotFoundError("signing material is missing")
        self.private_key_path.parent.mkdir(parents=True, exist_ok=True)
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.private_key_path.write_bytes(private_bytes)
        self.public_key_path.write_bytes(public_bytes)
        os.chmod(self.private_key_path, 0o600)
        os.chmod(self.public_key_path, 0o644)

    def _ensure_fallback_material(self) -> None:
        if self.private_key_path.is_file() and self.public_key_path.is_file():
            return
        if not self.auto_generate:
            raise FileNotFoundError("signing material is missing")
        self.private_key_path.parent.mkdir(parents=True, exist_ok=True)
        secret = base64.b64encode(os.urandom(32)).decode("ascii")
        key_id = hashlib.sha256(secret.encode("ascii")).hexdigest()[:16]
        self.private_key_path.write_text(secret, encoding="utf-8")
        self.public_key_path.write_text(
            f"{FALLBACK_SIGNATURE_ALGORITHM}:{key_id}\n",
            encoding="utf-8",
        )
        os.chmod(self.private_key_path, 0o600)
        os.chmod(self.public_key_path, 0o644)

    def _fallback_secret(self) -> bytes:
        self._ensure_fallback_material()
        return self.private_key_path.read_text(encoding="utf-8").strip().encode("ascii")

    def _fallback_key_id(self) -> str:
        return hashlib.sha256(self._fallback_secret()).hexdigest()[:16]

    def export_public_keys_payload(self) -> dict[str, Any]:
        self.ensure_signing_material()
        if not _CRYPTO_AVAILABLE:
            key_id = self._fallback_key_id()
            return {
                "keys": [
                    {
                        "key_id": key_id,
                        "algorithm": FALLBACK_SIGNATURE_ALGORITHM,
                        "public_key_pem": self.public_key_path.read_text(encoding="utf-8"),
                    }
                ],
                "updated_at": _now_iso(),
            }
        public_key = _load_public_key_from_pem(self.public_key_path.read_text(encoding="utf-8"))
        key_id = key_id_from_public_key(public_key)
        return {
            "keys": [
                {
                    "key_id": key_id,
                    "algorithm": SIGNATURE_ALGORITHM,
                    "public_key_pem": self.public_key_path.read_text(encoding="utf-8"),
                }
            ],
            "updated_at": _now_iso(),
        }

    def _trusted_public_keys(self) -> dict[str, Ed25519PublicKey]:
        trusted: dict[str, Ed25519PublicKey] = {}
        for key_id, pem in _read_trusted_keys(self.trusted_keys_path).items():
            try:
                trusted[key_id] = _load_public_key_from_pem(pem)
            except Exception:
                continue
        if self.public_key_path.is_file():
            try:
                public_key = _load_public_key_from_pem(self.public_key_path.read_text(encoding="utf-8"))
            except Exception:
                return trusted
            trusted.setdefault(key_id_from_public_key(public_key), public_key)
        return trusted

    def sign_card(self, card: dict[str, Any]) -> dict[str, Any]:
        self.ensure_signing_material()
        if not _CRYPTO_AVAILABLE:
            secret = self._fallback_secret()
            key_id = self._fallback_key_id()
            signature = hmac.new(secret, canonical_payload(card), hashlib.sha256).hexdigest()
            signed = dict(card)
            signed["signature_algorithm"] = FALLBACK_SIGNATURE_ALGORITHM
            signed["signature_schema"] = SIGNATURE_SCHEMA_VERSION
            signed["signature_key_id"] = key_id
            signed["signature"] = signature
            signed["signature_signed_at"] = _now_iso()
            signed["signature_status"] = "verified"
            signed.pop("signature_error", None)
            return signed
        private_key = _load_private_key(self.private_key_path)
        public_key = private_key.public_key()
        key_id = key_id_from_public_key(public_key)
        signature = private_key.sign(canonical_payload(card))
        signed = dict(card)
        signed["signature_algorithm"] = SIGNATURE_ALGORITHM
        signed["signature_schema"] = SIGNATURE_SCHEMA_VERSION
        signed["signature_key_id"] = key_id
        signed["signature"] = base64.b64encode(signature).decode("ascii")
        signed["signature_signed_at"] = _now_iso()
        signed["signature_status"] = "verified"
        signed.pop("signature_error", None)
        return signed

    def verify_card(self, card: dict[str, Any], *, raw_log_bytes: bytes | None = None) -> VerifyResult:
        raw_hash = card.get("raw_log_sha256")
        if raw_log_bytes is not None and isinstance(raw_hash, str) and raw_hash:
            actual = sha256_hex(raw_log_bytes)
            if actual != raw_hash:
                return VerifyResult(status="invalid", error="raw_log_sha256_mismatch")

        signature = card.get("signature")
        key_id = card.get("signature_key_id")
        algorithm = card.get("signature_algorithm")
        if not signature or not key_id or not algorithm:
            return VerifyResult(status="legacy-unsigned")
        if not _CRYPTO_AVAILABLE:
            if algorithm == SIGNATURE_ALGORITHM:
                return VerifyResult(status="legacy-unsigned", key_id=str(key_id))
            if algorithm != FALLBACK_SIGNATURE_ALGORITHM:
                return VerifyResult(status="invalid", error="unsupported_algorithm", key_id=str(key_id))
            expected_key_id = self._fallback_key_id()
            if str(key_id) != expected_key_id:
                return VerifyResult(status="invalid", error="untrusted_key", key_id=str(key_id))
            expected = hmac.new(
                self._fallback_secret(),
                canonical_payload(card),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(str(signature), expected):
                return VerifyResult(status="invalid", error="signature_mismatch", key_id=str(key_id))
            return VerifyResult(status="verified", key_id=str(key_id))
        if algorithm != SIGNATURE_ALGORITHM:
            return VerifyResult(status="invalid", error="unsupported_algorithm", key_id=key_id)
        trusted = self._trusted_public_keys()
        public_key = trusted.get(str(key_id))
        if public_key is None:
            return VerifyResult(status="invalid", error="untrusted_key", key_id=str(key_id))
        try:
            signature_bytes = base64.b64decode(str(signature))
        except Exception:
            return VerifyResult(status="invalid", error="bad_signature_encoding", key_id=str(key_id))
        try:
            public_key.verify(signature_bytes, canonical_payload(card))
        except Exception:
            return VerifyResult(status="invalid", error="signature_mismatch", key_id=str(key_id))
        return VerifyResult(status="verified", key_id=str(key_id))
