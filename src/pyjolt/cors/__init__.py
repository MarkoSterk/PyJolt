"""
CORS module
"""
from .cors import CORSMiddleware, cors_allow, set_rules

__all__ = ['CORSMiddleware', 'cors_allow', 'set_rules']
