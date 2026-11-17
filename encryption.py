import secrets
from pathlib import Path


def init_secret_file(path: str | Path) -> Path:
    """Initialize a secret file if it doesn't exist, and return its contents."""
    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        path.write_text(
            secrets.token_hex(32), 
            encoding='utf-8'
        )
    
    return path

def get_secret(path: str | Path) -> str:
    """Get the contents of a secret file."""
    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Secret file {path} does not exist.")
    
    return path.read_text(encoding='utf-8').strip()