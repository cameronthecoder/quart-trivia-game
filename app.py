from quart import Quart, render_template, websocket, request, redirect, abort, url_for, jsonify, copy_current_websocket_context
from functools import wraps, partial
from game import Game
import json, asyncio, random
app = Quart(__name__)

games = set()


def get_game(id):
    global games
    for game in games:
        if game.id == id: return game
    return None


@app.route('/', methods=['GET', 'POST'])
async def index():
    categories = Game.categories
    if request.method == "POST":
        global games
        form = await request.form
        questions = form.get('number_of_questions')
        difficulty = form.get('difficulty')
        category = form.get('category')
        is_private = form.get('private') or False
        g = Game(category, questions, difficulty, is_private)
        await g.generate_questions()
        games.add(g)
        app.logger.debug(f'Created game (ID: {g.id})')
        return redirect(url_for('game', id=g.id))
    return await render_template('index.html', categories=categories)


@app.route('/api/games/')
async def games_json():
    global games
    json_list = []
    for game in games: 
        if not game.private:
            json_list.append(game.to_json())
    return jsonify(json_list)


@app.route('/game/<int:id>/')
async def game(id):
    current_game = get_game(id)
    if not current_game: abort(404)
    if current_game.status == "in_progress": return redirect(url_for('index'))
    return await render_template('game.html', game=current_game)


@app.websocket('/game/<int:id>/')
async def ws_v2(id):
    global games
    current_game = get_game(id)
    if not current_game: abort(404)
    try:
        while True:
            data = await websocket.receive()
            json_data = json.loads(data)

            if json_data["type"] == "connect": # Client connected
                current_game.add_player(json_data["username"], websocket._get_current_object())
                await current_game.send_game_state()
            elif json_data["type"] == "start":
                app.logger.debug('started')
                if current_game.player_count > 1 and current_game.status == "waiting":
                    await current_game.broadcast(json.dumps({
                        "event": {
                            "type": "start"
                        }
                    }))
                    current_game.status = "in_progress"
                    questions = current_game.questions
                    await asyncio.sleep(3)

                    @copy_current_websocket_context
                    async def background_task():
                        current_question_id = 0
                        for question in questions['results']:
                            # Send question to all players as a question event and allow 30 seconds
                            # for each player to answer.
                            current_game.current_question = question
                            current_question_id += 1
                            choices = []
                            for incorrect_answer in question["incorrect_answers"]: choices.append(incorrect_answer)
                            choices.append(question["correct_answer"])
                            random.shuffle(choices)
                            await current_game.broadcast(json.dumps({
                                "event": {
                                    "type": "question",
                                    "question": {
                                        "question": question["question"],
                                        "total_questions": current_game.amount,
                                        "current_question_id": current_question_id,
                                        "choices": choices
                                    }
                                }
                            }))
                            await asyncio.sleep(30)
                        current_game.status = "finished"
                        print(current_game.status)
                        await current_game.send_game_state()
                        print(current_game.player_scores)
                    asyncio.ensure_future(background_task())
            elif json_data["type"] == "answer":
                player = current_game.get_player(websocket._get_current_object())
                if json_data["choice"] == current_game.current_question["correct_answer"]:
                    player.add_point()
                    await player.socket.send(json.dumps({"event": {"type": "choice_response", "result": "correct"}}))
                else:
                    await player.socket.send(json.dumps({"event": {"type": "choice_response", "result": "not_correct", "correct_answer": current_game.current_question["correct_answer"]}}))
                app.logger.debug(f'Player {player.username} now has {player.points} points.')
    except asyncio.CancelledError:
        app.logger.debug(f'Client disconnected from game (ID: {current_game.id})')
        current_game.remove_player(websocket._get_current_object())
        await current_game.send_game_state()
        if current_game.player_count == 0:
            games.remove(current_game)
            app.logger.debug(f'Game (ID: {current_game.id}) removed from memory.')
            
        
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")