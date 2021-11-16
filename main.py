import asyncio
import json

import aiohttp
import websockets
import websockets.exceptions

new_data: asyncio.Event = asyncio.Event()
data = None


async def _get_data(client, endpoint):
    async with client.request('GET', f'http://10.1.0.200:8080/{endpoint}') as request:
        return await request.json()


async def get_laps(client):
    return await _get_data(client, 'lap')


async def get_lap_sources(client):
    return await _get_data(client, 'lap-source')


async def get_teams(client):
    return await _get_data(client, 'team')


async def fetch(interval: int):
    global data
    async with aiohttp.ClientSession() as client:
        while True:
            laps, lap_sources, teams = await asyncio.gather(
                get_laps(client), get_lap_sources(client), get_teams(client)
            )

            team_count = {
                team['name']: sum([lap['teamId'] == team['id'] for lap in laps]) for team in teams
            }

            data = team_count

            new_data.set()
            new_data.clear()
            await asyncio.sleep(interval)


async def push(websocket):
    try:
        if data:
            await websocket.send(json.dumps(data))
        while True:
            await new_data.wait()
            await websocket.send(json.dumps(data))
    except websockets.exceptions.ConnectionClosedOK:
        pass


async def serve():
    print("Started websocket server.")
    async with websockets.serve(push, "localhost", 8081):
        await asyncio.Future()


async def main():
    asyncio.create_task(serve())
    asyncio.create_task(fetch(5))

    await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
