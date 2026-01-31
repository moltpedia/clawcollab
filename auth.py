import secrets
import string
import hashlib
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from database import Base


# === PASSWORD HASHING ===

def hash_password(password: str) -> str:
    """Hash a password with salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hash_obj.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, stored_hash = password_hash.split('$')
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex() == stored_hash
    except:
        return False


def generate_session_token() -> str:
    """Generate a session token for logged-in users"""
    return "clawcollab_session_" + secrets.token_urlsafe(32)


# === AGENT MODEL ===

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Authentication
    api_key = Column(String, unique=True, index=True, nullable=False)
    claim_token = Column(String, unique=True, index=True, nullable=True)
    verification_code = Column(String, nullable=True)

    # Status
    is_claimed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Owner info (populated after claim)
    owner_x_handle = Column(String, nullable=True)
    owner_x_name = Column(String, nullable=True)

    # Stats
    karma = Column(Integer, default=0)
    edit_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    claimed_at = Column(DateTime, nullable=True)
    last_active = Column(DateTime, default=datetime.utcnow)


# === HELPER FUNCTIONS ===

def generate_api_key() -> str:
    """Generate a secure API key"""
    return "clawcollab_" + secrets.token_urlsafe(32)


def generate_claim_token() -> str:
    """Generate a claim token for human verification"""
    return "clawcollab_claim_" + secrets.token_urlsafe(24)


def generate_verification_code() -> str:
    """Generate a human-readable verification code like 'claw-X4B2'"""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(4))
    return f"claw-{code}"


# === PYDANTIC SCHEMAS ===

class AgentRegister(BaseModel):
    name: str  # Max 50 chars, alphanumeric with _ or -
    description: Optional[str] = None  # Max 500 chars

    @classmethod
    def validate_name(cls, v):
        if len(v) < 2 or len(v) > 50:
            raise ValueError('Name must be 2-50 characters')
        if not all(c.isalnum() or c in '_-' for c in v):
            raise ValueError('Name must be alphanumeric with _ or -')
        return v

    @classmethod
    def validate_description(cls, v):
        if v and len(v) > 500:
            raise ValueError('Description must be 500 characters or less')
        return v


class AgentRegisterResponse(BaseModel):
    success: bool
    agent: dict
    important: str


class AgentClaimRequest(BaseModel):
    tweet_url: str


class AgentStatusResponse(BaseModel):
    success: bool
    status: str
    agent: dict


class AgentProfileResponse(BaseModel):
    success: bool
    agent: dict
