"""
Authentication module
"""

from .authentication import Authentication
from .authentication_mw import login_required, role_required, Authentication as AuthenticationMW

__all__ = ['Authentication', 'login_required', 'role_required', 'AuthenticationMW']
