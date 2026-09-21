"""Deterministic sub-seed derivation shared by every generation stage
(single master seed, per Global Constraints - each stage derives its own
sub-seed instead of taking a separate --seed flag)."""
import hashlib


def derive_seed(seed: int, *parts: str) -> int:
    key = f"{seed}:{':'.join(parts)}".encode()
    return int(hashlib.sha256(key).hexdigest(), 16) % (2**32)
