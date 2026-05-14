from lcu import push
from pathlib import Path
from lcu_driver import Connector
from lcu_driver.connection import Connection
from lcu_driver.events.responses import WebsocketEventResponse

auto_accept = False


def register(connector: Connector):
    @connector.ws.register(
        "/lol-matchmaking/v1/search", event_types=("CREATE", "UPDATE")
    )
    async def on_queue(conn: Connection, event: WebsocketEventResponse):
        push(
            f'<b id="queue_timer" hx-swap-oob="true"> Time: {event.data["timeInQueue"]}s (est. {int(event.data["estimatedQueueTime"])}s)</b>'
        )

    @connector.ws.register("/lol-matchmaking/v1/search", event_types=("DELETE",))
    async def on_queue_exit(conn: Connection, event: WebsocketEventResponse):
        push('<b id="queue_timer" hx-swap-oob="true">Not in queue</b>')

    @connector.ws.register("/lol-matchmaking/v1/ready-check", event_types=("UPDATE",))
    async def on_queue_pop(conn: Connection, event: WebsocketEventResponse):
        if event.data["playerResponse"] != "None" or not auto_accept:
            return

        await conn.request("POST", "/lol-matchmaking/v1/ready-check/accept")


def toggle_autoaccept():
    global auto_accept
    auto_accept = not auto_accept


def switch_screen():
    push(open(Path("src/lobby/index.html"), encoding="utf-8").read())
    if auto_accept:
        push(
            '<input hx-post="/lobby/queue/toggle" hx-swap-oob="true" hx-swap="none" type="checkbox" id="auto-accept-switch" checked>'
        )
