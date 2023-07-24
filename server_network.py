"""The part of the server that moves data around."""

import asyncio
from collections.abc import Coroutine
import json
import logging
import websockets
import websockets.server  # only for typing, is that bad?

import bbutils
import constants


class Client:
    """Server's representation of a network client."""

    def __init__(
        self,
        server: "Server",
        ws: websockets.server.WebSocketServer,
        tg: asyncio.TaskGroup,
    ) -> None:
        """Warning: only create Client instances within the tg context manager."""

        self.server = server
        self.ws = ws

        # assign this client a unique id
        self.client_id = self.server.get_next_id()

        # server.Client.state is mirrored by game.PlayerData.__dict__
        self.state: dict[str, Any] = {}

        # start listening to messages coming in from the client
        handler = tg.create_task(self.handler())

    async def initialize(self) -> None:
        """Code that should go in __init__ but needs to be awaited."""
        await self.ws.send({"type": constants.Msg.ID, "id": self.client_id})

    async def handler(self) -> None:
        """Listen for messages coming in from client ws."""
        async for json_message in self.ws:
            # convert JSON string to dict
            message = json.loads(json_message)

            match message["type"]:
                case constants.Msg.GREET:
                    # TODO: find some way to prevent name collision
                    #       (i.e., more than one player requesting the same name)
                    self.state["name"] = message["name"]
                    print(f"{message['name']} has joined.")

                case constants.Msg.REQUEST:
                    self.server.message_all(
                        {
                            "type": constants.Msg.APPROVE,
                            "id": self.client_id,
                            "state": {"rq": message["rq"]},
                        }
                    )


class Server:
    def __init__(self) -> None:
        try:
            self.ip = bbutils.get_local_ip()
        except RuntimeError as m:
            logging.error(m)
            exit()

        # has the game been started yet?
        self.game_running = False

        self.clients: set[Client] = set()

        # the id that will be assigned to the next client
        # can't do something as simple as len(self.clients) because a client might
        # disconnect and rejoin
        self.current_id = -1

    async def initialize(self, start_func: Coroutine) -> None:
        """Code that should go in __init__ but needs to be awaited."""
        async with websockets.serve(
            self.handle_new_connection,
            self.ip,
            constants.PORT,
            create_protocol=bbutils.BBServerProtocol,
            ping_interval=5,
            ping_timeout=10,
        ) as server:
            await asyncio.create_task(start_func())
            await asyncio.Future()  # run forever

    def get_next_id(self) -> int:
        self.current_id += 1
        return self.current_id

    async def handle_new_connection(self, ws: websockets.server.WebSocketServer) -> None:
        """Start server communications with ws and add ws to self.clients."""
        # prevent new clients from connecting if the game has already started
        if self.game_running:
            await ws.close()
            logging.info("rejected a player because the game has already started")
            return

        async with asyncio.TaskGroup() as tg:
            # add ws to the self.clients set and remove it upon disconnect
            client = Client(self, ws, tg)
            await client.initialize()
            self.clients.add(client)
            logging.debug(f"added player with id {client.client_id}")
            try:
                await client.ws.wait_closed()
            finally:
                self.clients.remove(client)
                logging.debug(f"removed player with id {client.client_id}")

    def message_all(self, message: bbutils.Message) -> None:
        """Serialize message to JSON and broadcast it to all members of self.clients."""
        # check for message validity - raises ValueError if not valid
        bbutils.is_message_valid(message)

        # turn the bbutils.Message into a JSON-formated str
        data = json.dumps(message)
        websockets.broadcast([c.ws for c in self.clients], data)
        logging.debug(f"broadcasted the following: {data}")

    def start_game(self):
        """
        Call this method when the game starts.

        It messages all clients with a START signal.
        """
        self.game_running = True
        self.message_all(
            {
                "type": constants.Msg.START,
                "states": [(c.client_id, c.state) for c in self.clients],
            }
        )
