from .hub import MonitorHub
from .menu import InMemoryMenu
from .service import OrderingService
from .store import InMemoryStore

hub = MonitorHub()
store = InMemoryStore()
menu = InMemoryMenu()  # TODO: replace with teammate's PostgreSQL MenuProvider
service = OrderingService(menu, store, hub)


def get_service() -> OrderingService:
    return service
