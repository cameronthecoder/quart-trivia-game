from quart import Quart, render_template, websocket, request, redirect, abort, url_for, jsonify, copy_current_websocket_context
from functools import wraps, partial
from game import Game
import json
import asyncio
import random
app = Quart(__name__)

games = set()


def get_game(id: int) -> Game:
    global games
    for game in games:
        if game.id == id:
            return game
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
    return jsonify([game.to_json() for game in games if not game.private])


@app.route('/game/<int:id>/')
async def game(id):
    current_game = get_game(id)
    if not current_game:
        abort(404)
    if current_game.status == "in_progress":
        return redirect(url_for('index'))
    return await render_template('game.html', game=current_game)


@app.websocket('/game/<int:id>/')
async def ws_v2(id):
    global games
    current_game = get_game(id)
    if not current_game:
        abort(404)
    ws = websocket._get_current_object()
    try:
        while True:
            data = await websocket.receive()
            json_data = json.loads(data)

            if json_data["type"] == "connect":  # Client connected
                username = json_data["username"]
                player = current_game.add_player(username, ws)
                await current_game.send_game_state()
                await current_game.send_join_event(ws, player.username)
            elif json_data["type"] == "start":
                if current_game.player_count > 1 and current_game.status == "waiting" and current_game.get_player(ws).host:
                    await current_game.start()
                    questions = current_game.questions
                    await asyncio.sleep(3)

                    @copy_current_websocket_context
                    async def background_task():
                        for question in questions['results']:
                            # Send question to all players as a question event and allow 30 seconds
                            # for each player to answer.
                            await current_game.send_question(question)
                            await asyncio.sleep(30)
                        current_game.status = "finished"
                        await current_game.send_game_state()
                    asyncio.ensure_future(background_task())
            elif json_data["type"] == "answer":
                player = current_game.get_player(ws)
                if json_data["choice"] == current_game.current_question["correct_answer"]:
                    player.add_point()
                    await player.send_choice_response("correct")
                else:
                    await player.send_choice_response("not_correct", current_game.current_question["correct_answer"])
                app.logger.debug(
                    f'Player {player.username} now has {player.points} points.')

    except asyncio.CancelledError:
        player = current_game.get_player(ws)
        app.logger.debug(
            f'Player {player.username} disconnected from Game (ID: {current_game.id})')
        current_game.remove_player(ws)
        if player.host and current_game.player_count != 0:
            current_game.assign_new_host()
            await current_game.send_host_notification()
            app.logger.debug(
                f'Game (ID {current_game.id}) switched hosts to {current_game.host.username}')
        await current_game.send_game_state()
        await current_game.send_leave_event(player.username)
        if current_game.player_count == 0:
            games.remove(current_game)
            app.logger.debug(
                f'Game (ID: {current_game.id}) removed from memory.')


if __name__ == "__main__":
    app.run(debug=True)
