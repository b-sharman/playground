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


class PlayerData:
    """Class that updates its __dict__ from data coming over the network."""
    def __init__(self, state: Optional[dict[str, Any]] = None) -> None:
        if state is not None:
            self.update_state(state)

    def update_state(self, state: dict[str, Any]) -> None:
        """
        Assign this class's attributes to values corresponding to `state`.

        This essentially translates a dict of vars and values to attributes
        For instance,
            >>> p = PlayerData()
            >>> p.update_state({"client_id": 0, "name": "foo"})
        should be more or less equivalent to
            >>> p = PlayerData()
            >>> p.client_id = 0
            >>> p.name = "foo"
        """
        self.__dict__.update(state)


class PlayerInputHandler:
    """The player being controlled by this computer."""

    def __init__(self, client: Client) -> None:
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
        self.client = Client(self)

        self.players: dict[int, PlayerData] = {}

        self.input_handler = PlayerInputHandler(self.client)
        # id of the player playing on this computer
        # assigned upon receiving an ID message
        self.player_id = None

    async def assign_name(self) -> None:
        name = await aioconsole.ainput("Enter your name: ")
        await self.client.greet(name)

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
                    f"PlayerData {message['id']} state updated with {message['state']}",
                )

            case constants.Msg.ID:
                self.player_id = message["id"]

            case constants.Msg.START:
                print("Starting now!")
                for client_id, state in message["states"]:
                    self.players[client_id] = PlayerData(state)
                # start listening for keyboard input
                tg.create_task(self.input_handler.start())


async def main() -> None:
    game = Game()

    if len(sys.argv) < 2:
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
