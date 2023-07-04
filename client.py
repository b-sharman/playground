import asyncio
import json
import logging
from typing import Any, Optional
import websockets
import websockets.client
import websockets.server

import constants


class Client:
    def __init__(self, ws: websockets.server.WebSocketServer, name: str) -> None:
        self.ws = ws
        self.name = name

    async def greet(self) -> None:
        if self.name is None:
            raise NameError("cannot greet when player name has not been set")
        await self.ws.send({"type": constants.Msg.GREET, "name": self.name})

    async def send_rq(self, rq: constants.Rq) -> None:
        await self.ws.send({"type": constants.Msg.REQUEST, "rq": rq})
