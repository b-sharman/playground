import asyncio
import json
import logging
from typing import Optional
import websockets
import websockets.client
import websockets.server

import aioconsole

import bbutils
import constants


class Client:
    def __init__(self, ws: websockets.server.WebSocketServer, name: str) -> None:
        self.ws = ws
        self.name = name

        self.client_id = None

        self.player = Player(self)

    async def run(self) -> None:
        await self.player.run()

    async def greet(self) -> None:
        await self.ws.send({"type": constants.Msg.GREET, "name": self.name})


class Player:
    def __init__(self, client: Client) -> None:
        self.client = client

        # assigned to constants.Rq.*
        self.state = None

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
        client = Client(ws=ws, name=input("Enter your name: "))
        async with asyncio.TaskGroup() as tg:
            tg.create_task(client.greet())
            tg.create_task(client.run())

            while True:
                # waits until data is received from the server
                message = json.loads(await ws.recv())
                match message["type"]:
                    case constants.Msg.APPROVE:
                        logger.log(
                            logging.DEBUG,
                            f"received approve of type {message['rq']} from client {message['id']}",
                        )
                        # Eventually, we will have a list of Players and will search
                        # through them. For now, we only do something if we are the
                        # player in question.
                        if message["id"] == client.client_id:
                            client.player.state = message["rq"]
                    case constants.Msg.ID:
                        client.client_id = message["id"]
                    case constants.Msg.START:
                        print("Starting now!")


if __name__ == "__main__":
    logger = logging.getLogger("websockets")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())
