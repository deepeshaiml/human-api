from __future__ import annotations

import os
from dataclasses import dataclass

import jwt
import msal
from jwt import PyJWKClient


class IdentityConfigurationError(RuntimeError):
    pass


class TokenRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class EntraSettings:
    tenant_id: str
    client_id: str
    client_secret: str
    api_scope: str = "HumanAPI.User"

    @classmethod
    def from_env(cls) -> EntraSettings:
        values = [os.getenv("ENTRA_TENANT_ID"), os.getenv("ENTRA_CLIENT_ID"),
                  os.getenv("ENTRA_CLIENT_SECRET")]
        if not all(values):
            raise IdentityConfigurationError("Entra OIDC is not configured.")
        return cls(values[0], values[1], values[2],
                   os.getenv("ENTRA_API_SCOPE", "HumanAPI.User"))  # type: ignore[arg-type]


class EntraTokenValidator:
    """Validate an Entra access token before resolving the directory object to an app user."""

    def __init__(self, settings: EntraSettings):
        self.settings = settings
        self.issuer = f"https://login.microsoftonline.com/{settings.tenant_id}/v2.0"
        self.jwks = PyJWKClient(
            f"https://login.microsoftonline.com/{settings.tenant_id}/discovery/v2.0/keys",
            cache_jwk_set=True, lifespan=3600,
        )

    def validate(self, access_token: str) -> dict:
        try:
            key = self.jwks.get_signing_key_from_jwt(access_token)
            claims = jwt.decode(
                access_token, key.key, algorithms=["RS256"], audience=self.settings.client_id,
                issuer=self.issuer, options={"require": ["exp", "iat", "iss", "aud", "tid", "oid"]},
            )
        except Exception as exc:
            raise TokenRejected("The Entra access token could not be validated.") from exc
        if claims.get("tid") != self.settings.tenant_id:
            raise TokenRejected("The access token belongs to a different tenant.")
        scopes = set(str(claims.get("scp", "")).split())
        if self.settings.api_scope not in scopes:
            raise TokenRejected("The access token does not contain the Human API scope.")
        return claims


class GraphOnBehalfOfTokenProvider:
    """Request short-lived delegated Graph tokens; no token or cache is written to disk."""

    def __init__(self, settings: EntraSettings):
        self.settings = settings

    def acquire(self, validated_user_assertion: str, scopes: list[str]) -> str:
        client = msal.ConfidentialClientApplication(
            self.settings.client_id,
            authority=f"https://login.microsoftonline.com/{self.settings.tenant_id}",
            client_credential=self.settings.client_secret,
        )
        result = client.acquire_token_on_behalf_of(
            user_assertion=validated_user_assertion, scopes=scopes,
        )
        token = result.get("access_token")
        if not token:
            # Do not include the provider's response: it may contain identity or request details.
            raise TokenRejected("Microsoft Graph delegated access could not be acquired.")
        return token
