from quart import Quart, websocket, render_template
import asyncio

app = Quart(__name__)

sockets = set()

@app.route('/')
async def index():
    return await render_template('test.html')

@app.websocket('/')
async def ws():
    try:
        while True:
            await websocket.accept()
    except asyncio.CancelledError:
        app.logger.debug('Client disconnected.')

if __name__ == "__main__":
    app.run(debug=True)