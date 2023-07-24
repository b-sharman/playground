"""The part of the server that handles game-specific logic."""

import asyncio
import logging

import aioconsole

import constants
import server_network


class Server:
    def __init__(self) -> None:
        self.server = server_network.Server()

    async def initialize(self) -> None:
        """Code that should go in __init__ but needs to be awaited."""
        await self.server.initialize(self.listen_for_start)

    async def listen_for_start(self) -> None:
        """Start the game upon receiving proper user input."""
        print(f"Type '{constants.SERVER_START_KEYWORD}' at any time to start the game.")

        output = None
        while output != constants.SERVER_START_KEYWORD:
            output = await aioconsole.ainput()
            # how many players have not submitted their names yet?
            nameless_count = ["name" in c.state for c in self.server.clients].count(False)
            if nameless_count > 0:
                # cannot start until all players have submitted names
                print(
                    f"Cannot start; {nameless_count} {'players have' if nameless_count > 1 else 'player has'} not submitted their name"
                )
                # do not exit the while loop
                output = None

        # broadcast a START message to the clients
        self.server.start_game()


async def main() -> None:
    server = Server()
    await server.initialize()


if __name__ == "__main__":
    logger = logging.getLogger("websockets")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())
