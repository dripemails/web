"""
Custom authentication classes for REST Framework.
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _


class BearerTokenAuthentication(TokenAuthentication):
    """
    Token authentication that supports both "Token" and "Bearer" prefixes.
    
    Clients can authenticate using either:
    - Authorization: Token <token>
    - Authorization: Bearer <token>
    """
    keyword = 'Token'
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        # Split the header
        parts = auth_header.split()
        
        if not parts:
            return None
        
        # Check if it's "Token" or "Bearer"
        keyword = parts[0]
        if keyword.lower() not in ['token', 'bearer']:
            return None
        
        if len(parts) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(parts) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)
        
        token = parts[1]
        return self.authenticate_credentials(token)

