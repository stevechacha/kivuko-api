from django.urls import re_path

from api.consumers import MissionChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/missions/(?P<mission_id>[0-9a-f-]+)/chat/$", MissionChatConsumer.as_asgi()),
]
