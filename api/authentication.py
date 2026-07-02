from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from api.models import Participant


class SessionTokenAuthentication(BaseAuthentication):
    header_name = "HTTP_X_SESSION_TOKEN"

    def authenticate(self, request):
        token = request.META.get("HTTP_X_SESSION_TOKEN")
        if not token:
            return None
        try:
            participant = Participant.objects.get(session_token=token)
        except Participant.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid session token") from exc
        return (participant, token)
