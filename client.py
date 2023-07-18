import asyncio
import json
import websockets

import bbutils
import constants


class Client:
    def __init__(self, name: str, game: "game.Game") -> None:
        self.name = name
        self.game = game

    async def greet(self) -> None:
        """
        Send a GREET message to the server.

        This type of message informs the server of the player name.
        """
        if self.name is None:
            raise NameError("cannot greet when player name has not been set")
        await self.ws.send({"type": constants.Msg.GREET, "name": self.name})

    async def send_rq(self, rq: constants.Rq) -> None:
        """Send an rq-type message to the server."""
        await self.ws.send({"type": constants.Msg.REQUEST, "rq": rq})

    async def start(self, ip: str) -> None:
        """Attempt to connect to the server and listen for new messages."""
        async with websockets.connect(
            f"ws://{ip}:{constants.PORT}", create_protocol=bbutils.BBClientProtocol
        ) as self.ws:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.greet())

                while True:
                    # waits until data is received from the server
                    message = json.loads(await self.ws.recv())
                    await self.game.handle_message(message, tg)
