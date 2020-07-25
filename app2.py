from quart import Quart, render_template, websocket
from functools import partial, wraps
import asyncio


app = Quart(__name__)


connected_websockets = set()

def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global connected_websockets
        connected_websockets.add(websocket._get_current_object())
        try:
            return await func(*args, **kwargs)
        finally:
            connected_websockets.remove(websocket._get_current_object())
    return wrapper

async def broadcast(message):
    for websock in connected_websockets:
        await websock.send(message)


@app.route('/')
async def index():
    return await render_template('index2.html')

@app.websocket('/ws')
@collect_websocket
async def ws():
    try:
        while True:
            data = await websocket.receive()
            await broadcast(f'you sent: {data}')
            await websocket.send('this should be sent only the client that sent it!')
    except asyncio.CancelledError:
        print('Client disconnected')



if __name__ == '__main__':
    app.run(port=5000)
