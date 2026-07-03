"""Real-time mission chat via Django Channels."""

from __future__ import annotations

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from api.keyword_flags import detect_violation
from api.models import ChatMessage, ContentReport, Mission, Participant


class MissionChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.mission_id = self.scope["url_route"]["kwargs"]["mission_id"]
        self.group_name = f"mission_{self.mission_id}"
        token = self.scope["query_string"].decode().split("token=")[-1].split("&")[0]
        self.participant = await self._auth_participant(token)
        if not self.participant:
            await self.close(code=4401)
            return

        allowed = await self._can_access_mission(self.participant.id, self.mission_id)
        if not allowed:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if payload.get("type") != "send_message":
            return

        text = (payload.get("text") or "").strip()
        if not text:
            return

        message = await self._create_message(self.mission_id, self.participant, text)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": message,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def _auth_participant(self, token: str) -> Participant | None:
        if not token:
            return None
        return Participant.objects.filter(session_token=token, is_seed_peer=False).first()

    @database_sync_to_async
    def _can_access_mission(self, participant_id, mission_id) -> bool:
        try:
            mission = Mission.objects.select_related("match").get(id=mission_id)
        except Mission.DoesNotExist:
            return False
        return participant_id in (mission.match.participant_id, mission.match.peer_id)

    @database_sync_to_async
    def _create_message(self, mission_id, participant: Participant, text: str) -> dict:
        mission = Mission.objects.select_related("match__peer", "match__participant").get(id=mission_id)
        mine = ChatMessage.objects.create(
            mission=mission,
            sender=participant,
            from_role="me",
            text=text,
        )

        flagged, reason = detect_violation(text)
        if flagged and reason:
            peer = (
                mission.match.peer
                if mission.match.participant_id == participant.id
                else mission.match.participant
            )
            ContentReport.objects.create(
                mission=mission,
                reporter=participant,
                reported=peer,
                reason=reason,
                excerpt=text[:280],
                auto_flagged=True,
            )

        return {
            "type": "message",
            "id": str(mine.id),
            "from_role": mine.from_role,
            "text": mine.text,
            "created_at": mine.created_at.isoformat(),
        }
