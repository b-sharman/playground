import asyncio
import json
import logging
from typing import Any, Optional
import socket
import sys
import websockets
import websockets.client
import websockets.server

import aioconsole

from client import Client
import constants


class Player:
    def __init__(self, state: Optional[dict[str, Any]] = None) -> None:
        if state is not None:
            self.update_state(state)

    def update_state(self, state: dict[str, Any]) -> None:
        """
        Assign this class's attributes to values corresponding to `state`.

        This essentially translates a dict of vars and values to attributes
        For instance,
            >>> p = Player()
            >>> p.update_state({"client_id": 0, "name": "foo"})
        should be more or less equivalent to
            >>> p = Player()
            >>> p.client_id = 0
            >>> p.name = "foo"
        """
        self.__dict__.update(state)


class ThisPlayer(Player):
    """The player that is being controlled by this computer."""

    def __init__(self, client: Client, state: Optional[dict[str, Any]] = None) -> None:
        super().__init__(state)
        self.client = client

    async def start(self) -> None:
        """Start everything the player needs to do during the game."""
        while True:
            await self.run()

    async def run(self) -> None:
        """Interface to send requests to the server."""
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
            await self.client.send_rq(rq)


class Game:
    def __init__(self) -> None:
        # TODO: allow creating a client before receiving a name
        name = input("Enter your name: ")
        self.client = Client(name, self)

        self.players: dict[int, Player] = {}
        self.player = ThisPlayer(self.client, {"name": name})

    async def initialize(self, ip) -> None:
        """Things that can't go in __init__ because they're coros"""
        await self.client.start(ip)

    async def handle_message(self, message: dict, tg: asyncio.TaskGroup) -> None:
        """Handle a JSON-loaded dict network message."""
        match message["type"]:
            case constants.Msg.APPROVE:
                self.players[message["id"]].update_state(message["state"])
                logger.log(
                    logging.DEBUG,
                    f"Player {message['id']} state updated with {message['state']}",
                )

            case constants.Msg.ID:
                self.players[message["id"]] = self.player

            case constants.Msg.START:
                print("Starting now!")
                for client_id, state in message["states"]:
                    self.players[client_id] = Player(state)
                # start listening for keyboard input
                tg.create_task(self.player.start())


async def main() -> None:
    print(sys.argv)
    game = Game()

    if len(sys.argv) < 1:
        logger.log(logging.ERROR, f"must specify an IP address")
        exit()

    # initialize the game, which currently equates to starting the client connection
    ip = sys.argv[-1]
    try:
        await game.initialize(ip)
    except (socket.gaierror, OSError):
        logger.log(logging.ERROR, f"invalid IP address {ip}")
        exit()


if __name__ == "__main__":
    logger = logging.getLogger("websockets")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())
