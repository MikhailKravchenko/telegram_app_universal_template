import datetime

import pytz
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from src.config import config


class JWTAuthSupportCookie(JWTAuthentication):
    """
    Extend the JWTAuthentication class to support cookie based authentication
    """

    def authenticate(self, request):
        if (
            "access_token" in request.COOKIES
            and request.META["PATH_INFO"] != "/api/v1/accounts/metamask_login/"
        ):
            return self.authenticate_credentials(request.COOKIES.get("access_token"))
        return super().authenticate(request)

    def authenticate_credentials(self, raw_token):
        try:
            # Validate the token
            validated_token = AccessToken(raw_token)
            user = self.get_user(validated_token)
            
            if not user.is_active:
                raise exceptions.AuthenticationFailed("User inactive or deleted.")

            # Check token expiration if needed
            if config.TOKEN_CHECK:
                utc_now = datetime.datetime.utcnow()
                utc_now = utc_now.replace(tzinfo=pytz.utc)
                
                # JWT handles expiration automatically, but we can add custom checks here
                # The token is already validated by AccessToken(raw_token)
                pass

            return (user, validated_token)
            
        except (InvalidToken, TokenError) as e:
            raise exceptions.AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Authentication failed: {str(e)}")
