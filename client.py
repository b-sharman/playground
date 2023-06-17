import asyncio
import json
import logging
from typing import Any, Optional
import websockets
import websockets.client
import websockets.server

import aioconsole

import bbutils
import constants


class Client:
    def __init__(self, ws: websockets.server.WebSocketServer) -> None:
        self.ws = ws

        self.client_id: int = None
        self.player = ThisPlayer(self)

    async def run(self) -> None:
        await self.player.run()

    async def greet(self) -> None:
        if not hasattr(self.player, "name"):
            raise NameError("cannot greet when player.name has not been set")
        await self.ws.send({"type": constants.Msg.GREET, "name": self.player.name})


class Player:
    def __init__(self, state: Optional[dict[str, Any]]=None) -> None:
        if state is not None:
            self.update_state(state)

    def update_state(self, state: dict[str, Any]) -> None:
        # This essentially translates a dict of vars and values to attributes
        # For instance,
        #     >>> p = Player()
        #     >>> p.update_state({"client_id": 0, "name": "foo"})
        # should be more or less equivalent to
        #     >>> p = Player()
        #     >>> p.client_id = 0
        #     >>> p.name = "foo"
        self.__dict__.update(state)


class ThisPlayer(Player):
    """The player that is being controlled by this computer."""

    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

    async def run(self) -> None:
        """Interface to send requests to the server."""
        while True:
            # for now it is OK to just hardcode these
            data = await aioconsole.ainput("Enter 'up', 'down', or 'shoot': ")
            match data:
                case "up":
                    rq = constants.Rq.UP
                case "down":
                    rq = constants.Rq.DOWN
                case "shoot":
                    rq = constants.Rq.SHOOT
                case _:
                    print("That's not a valid command.")
                    rq = None
            if rq is not None:
                await self.client.ws.send({"type": constants.Msg.REQUEST, "rq": rq})


async def main() -> None:
    async with websockets.connect(
        f"ws://localhost:{constants.PORT}", create_protocol=bbutils.BBClientProtocol
    ) as ws:
        players: dict[int, Player] = {}
        client = Client(ws=ws)
        client.player.name = input("Enter your name: ")

        async with asyncio.TaskGroup() as tg:
            tg.create_task(client.greet())

            while True:
                # waits until data is received from the server
                message = json.loads(await ws.recv())
                match message["type"]:
                    case constants.Msg.APPROVE:
                        players[message["id"]].update_state(message["state"])
                        print(f"Player {message['id']} state updated with {message['state']}")
                    case constants.Msg.ID:
                        client.client_id = message["id"]
                        players[message["id"]] = client.player
                    case constants.Msg.START:
                        print("Starting now!")
                        for client_id, state in message["states"]:
                            players[client_id] = Player(state)
                        # start listening for keyboard input
                        tg.create_task(client.run())


if __name__ == "__main__":
    logger = logging.getLogger("websockets")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())
