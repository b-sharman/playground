import asyncio
import json
import logging
from typing import Optional
import websockets
import websockets.client  # only for typing, is that bad?

import aioconsole

import constants


class Player:
    def __init__(self, name: str, player_id: Optional[int] = None) -> None:
        self.name = name
        self.player_id = player_id

        # TODO: remove this until implemented
        self.pos = [0, 0]

    async def command_entry(
        self, ws: websockets.client.WebSocketClientProtocol
    ) -> None:
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
                await ws.send(
                    json.dumps(
                        {
                            "type": constants.Msg.REQUEST,
                            "rq": rq,
                        }
                    )
                )

    async def greet(self, ws: websockets.client.WebSocketClientProtocol) -> None:
        await ws.send(json.dumps({"type": constants.Msg.GREET, "name": self.name}))


async def main() -> None:
    player = Player(name=input("Enter your name: "))
    async with websockets.connect(f"ws://localhost:{constants.PORT}") as ws:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(player.greet(ws))
            tg.create_task(player.command_entry(ws))

            while True:
                # waits until data is received from the server
                message = json.loads(await ws.recv())
                match message["type"]:
                    case constants.Msg.APPROVE:
                        logger.log(
                            logging.DEBUG,
                            f"received approve of type {message['rq']} from player {message['id']}",
                        )
                    case constants.Msg.START:
                        print("Starting now!")


if __name__ == "__main__":
    logger = logging.getLogger("websockets")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())
