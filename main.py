import asyncio
from typing import List, Dict

import websockets.exceptions
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket
from httpx import AsyncClient, Response

from basic_auth import admin
from models import Lap, LapSource, Team, Count
from queue_manager import QueueManager
from settings import settings

app = FastAPI(
    title='Loxsi',
    description='Data proxy for the Telraam application',
    version="0.69.0",
)
templates = Jinja2Templates(directory='templates')
queue_manager = QueueManager()

active = "None"


async def fetch():
    async with AsyncClient() as client:
        async def _fetch(endpoint: str):
            response: Response = await client.get(f'http://127.0.0.1:8080/{endpoint}')
            return response.json()

        while True:
            try:
                laps: List[Dict] = await _fetch('lap')
                teams: List[Dict] = await _fetch('team')
                lap_sources: List[Dict] = await _fetch('lap-source')

                teams: Dict[int, Team] = {team['id']: Team(**team) for team in teams}
                lap_sources: Dict[int, LapSource] = {
                    lap_source['id']: LapSource(**lap_source) for lap_source in lap_sources
                }
                laps: List[Lap] = [
                    Lap(team=teams[lap['teamId']], lap_source=lap_sources[lap['lapSourceId']], **lap) for lap in laps
                ]

                counts: List[Dict] = [
                    Count(count=len([lap for lap in laps if lap.team == team]), team=team).dict() for team in
                    teams.values()
                ]

                await queue_manager.broadcast(counts)
            except Exception as e:
                print(e)

            await asyncio.sleep(1)


@app.on_event("startup")
async def startup():
    asyncio.get_event_loop().create_task(fetch())


@app.get('/api/active/source')
async def api(_=Depends(admin)):
    return {'name': active}


@app.get('/api/active/connections')
async def api(_=Depends(admin)):
    return {'count': await queue_manager.count()}


@app.post('/api/use/{name}')
async def api_post(name: str, _=Depends(admin)):
    global active
    print(name)
    active = name
    return {'ok': 1}


@app.get('/admin', response_class=HTMLResponse)
async def admin(request: Request, _=Depends(admin)):
    return templates.TemplateResponse('admin.html', {'request': request, 'sources': settings.sources, 'title': "Hoi"})


@app.websocket('/feed')
async def feed(websocket: WebSocket):
    await websocket.accept()
    queue = await queue_manager.add()
    try:
        while True:
            data: Dict = await queue.get()
            await websocket.send_json(data)
    except websockets.exceptions.ConnectionClosedOK:
        pass
    finally:
        await queue_manager.remove(queue)
