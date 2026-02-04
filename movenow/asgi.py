import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import booking.routing
import core.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movenow.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            booking.routing.websocket_urlpatterns +
            core.routing.websocket_urlpatterns
        )
    ),
})