"""Broadcast mission chat events to WebSocket subscribers."""

from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_chat_message(mission_id, message_dict: dict) -> None:
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f"mission_{mission_id}",
        {
            "type": "chat.message",
            "message": {
                "type": "message",
                **message_dict,
            },
        },
    )
