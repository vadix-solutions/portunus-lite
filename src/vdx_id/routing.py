from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import web_interface.routing as web_interface_routing

application = ProtocolTypeRouter(
    {
        # (http->django views is added by default)
        "websocket": AuthMiddlewareStack(
            URLRouter(web_interface_routing.websocket_urlpatterns)
        )
    }
)
