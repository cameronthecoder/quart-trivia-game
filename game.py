import aiohttp, json, random
from quart.asgi import Websocket

def generate_random_id():
    range_start = 10**(4-1)
    range_end = (10**4)-1
    return random.randint(range_start, range_end)

class Player:
    def __init__(self, username, socket: Websocket, host = False):
        self.username = username
        self.socket = socket
        self.host = host
        self.points = 0

    async def send_choice_response(self, result, correct_answer = None):
        if correct_answer:
            await self.socket.send(json.dumps({
                "event":{
                    "type": "choice_response",
                    "result": "not_correct",
                    "correct_answer": correct_answer
                }
            }))
        else:
            await self.socket.send(json.dumps({
                "event": {
                    "type": "choice_response",
                    "result": "correct"
                }
            }))

    def add_point(self):
        self.points += 1


class Game:
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
        self.id = generate_random_id()
        self.category = category
        self.amount = amount
        self.max_playes = 10
        self.current_question = None
        self.difficulty = difficulty
        self.current_question_id = 0
        self.questions = None
        self.status = "waiting"
        self.private = private or False
        self.players = set()

    async def send_join_event(self, socket, username):
        for player in self.players:
            if player.socket != socket:
                await player.socket.send(json.dumps({
                    "event": {
                        "type": "player_connected",
                        "username": username
                    }
                }))
    
    async def send_leave_event(self, username):
        await self.broadcast(json.dumps({
            "event": {
                "type": "player_left",
                "username": username
            }
        }))
    
    # TODO: send host notification

    async def send_host_notification(self):
        for player in self.players:
            if player.host:
                await player.socket.send(json.dumps({
                    "event": {
                        "type": "new_host"
                    }
                }))

    async def start(self):
        await self.broadcast(json.dumps({
            "event": {
                "type": "start"
            }
        }))
        self.status = "in_progress"

    def add_player(self, username, socket: Websocket):
        """Add a player to the game.

        Args:
            username (str): The username of the player
            socket (Websocket): The player's WebSocket connection.
        """
        host = True if self.player_count == 0 else False
        player = Player(username, socket, host)
        self.players.add(player)
        return player

    def assign_new_host(self):
        random_sample_list = random.sample(self.players, 1)
        new_host = self.get_player(random_sample_list[0].socket)
        new_host.host = True
        return new_host
        
    def get_player_by_username(self, username) -> Player:
        for player in self.players:
            if player.username == username:
                return player

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
                "clients_connected": str(self.player_count),
                "status": self.status,
                "players": self.player_scores
            }}
        ))

    async def send_question(self, question):
        self.current_question = question
        self.current_question_id += 1
        choices = []
        for incorrect_answer in question["incorrect_answers"]: 
            choices.append(incorrect_answer)
        choices.append(question["correct_answer"])
        random.shuffle(choices)
        await self.broadcast(json.dumps({
            "event": {
                "type": "question",
                "question": {
                    "question": question["question"],
                    "total_questions": self.amount,
                    "current_question_id": self.current_question_id,
                    "choices": choices
                }
            }
        }))

    @property
    def host(self) -> Player:
        for player in self.players:
            if player.host:
                return player
        return None

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
