import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer

logger = logging.getLogger("vdx_id.%s" % __name__)


_CHANNEL_LAYER = None


def get_channel():
    global _CHANNEL_LAYER
    if _CHANNEL_LAYER is None:
        _CHANNEL_LAYER = get_channel_layer()
    return _CHANNEL_LAYER


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    channel_layer_name = "notifications"

    async def connect(self):
        # if self.scope["user"].is_anonymous:
        #     self.close()
        #     return

        await self.channel_layer.group_add(
            self.channel_layer_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.channel_layer_name, self.channel_name
        )

    # Must correspond to the 'type' of the channel message
    async def task_update(self, event):
        await self.send_json(event)

    async def agent_task_update(self, event):
        await self.send_json(event)

    async def notification(self, event):
        await self.send_json(event)

    async def map_update(self, event):
        await self.send_json(event)
