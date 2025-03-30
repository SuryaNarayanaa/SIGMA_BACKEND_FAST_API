import hashlib

def get_hash(clear: str) -> str:
    return hashlib.sha224(clear.encode("utf-8")).hexdigest()
