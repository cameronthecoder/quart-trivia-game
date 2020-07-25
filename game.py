import aiohttp, json
from quart.asgi import Websocket


class Player:
    def __init__(self, username, socket: Websocket):
        self.username = username
        self.socket = socket
        self.points = 0

    def add_point(self):
        self.points += 1


class Game:
    id = 0
    categories = { 
            # To add a category, go to https://opentdb.com/api_config.php and inspect the select category field
            # and you should see all of the categories with their corresponding ID.
            18: "Computer Science",
            9: "General Knowledge",
            23: "History",
            27: "Animals",
            17: "Science & Nature"
    }

    def __init__(self, category, amount, difficulty, private=None):
        self.id = Game.id
        Game.id += 1
        self.category = category
        self.amount = amount
        self.max_playes = 10
        self.current_question = None
        self.difficulty = difficulty
        self.questions = None
        self.status = "waiting"
        self.private = private or False
        self.players = set()

    def add_player(self, username, socket):
        """Add a player to the game.

        Args:
            username (str): The username of the player
            socket (Websocket): The player's WebSocket connection.
        """
        self.players.add(Player(username, socket))

    def to_json(self):
        return {
            "id": self.id,
            "category": self.categories.get(int(self.category), None),
            "amount": self.amount,
            "difficulty": self.difficulty,
            "status": self.status,
            "private": self.private,
            "players": self.player_count
        }

    async def send_game_state(self):
        await self.broadcast(json.dumps({
            "event": {
                "type": "info", 
                "clientsConnected": str(self.player_count),
                "status": self.status,
                "players": self.player_scores
            }}
        ))

    @property
    def player_scores(self):
        players_score = []
        for player in self.players:
            players_score.append({"username": player.username, "points": player.points})
        return players_score

    def remove_player(self, socket):
        """Remove a player from the game.
        Note: This does not actually terminate their WebSocket connection.

        Args:
            socket ([type]): [description]
        """
        for player in self.players:
            if player.socket == socket:
                self.players.remove(player)
                break

    def get_player(self, socket) -> Player:
        for player in self.players:
            if player.socket == socket:
                return player

    async def broadcast(self, message):
        """Broadcast a message to all connected players.

        Args:
            message (str): The message that all players will recieve.
        """
        for player in self.players:
            await player.socket.send(message)
    
    async def generate_questions(self):
        # TODO: ADD CUSTOM OPTION FOR JSON FILE
        """Generate trivia questions based on the data provided when the class was instantiated."""
        url = "https://opentdb.com/api.php"
        params = {"amount": self.amount, "category": self.category, "difficulty": self.difficulty}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                self.questions = await resp.json()

    @property
    def player_count(self): return len(self.players)
