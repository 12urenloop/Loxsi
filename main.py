import asyncio
from asyncio import Queue
from typing import List, Dict

import httpx
import websockets.exceptions
from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket
from httpx import AsyncClient, Response
from starlette.status import HTTP_409_CONFLICT, HTTP_502_BAD_GATEWAY, HTTP_202_ACCEPTED

from basic_auth import admin
from data_publisher import DataPublisher
from models import Lap, LapSource, Team, Count, Message
from settings import settings

app = FastAPI(
    title='Loxsi',
    description='Data proxy for the Telraam application',
    version="0.69.0",
)

templates = Jinja2Templates(directory='templates')

feed_publisher = DataPublisher()
admin_publisher = DataPublisher()


async def fetch():
    async with AsyncClient() as client:
        async def _fetch(endpoint: str):
            response: Response = await client.get(f'{settings.telraam.base_url}/{endpoint}')
            await admin_publisher.publish('telraam-health', 'good')
            return response.json()

        while True:
            try:
                laps: List[Dict] = await _fetch('lap')
                teams: List[Dict] = await _fetch('team')
                lap_sources: List[Dict] = await _fetch('lap-source')

                await admin_publisher.publish('lap-source', lap_sources)

                teams_by_id: Dict[int, Team] = {team['id']: Team(**team) for team in teams}
                lap_sources_by_id: Dict[int, LapSource] = {
                    lap_source['id']: LapSource(**lap_source) for lap_source in lap_sources
                }

                laps: List[Lap] = [
                    Lap(team=teams_by_id[lap['teamId']], lap_source=lap_sources_by_id[lap['lapSourceId']], **lap) for
                    lap in laps
                ]
                laps: List[Lap] = [lap for lap in laps if lap.lap_source.id == settings.source.id]

                counts: List[Dict] = [
                    Count(count=len([lap for lap in laps if lap.team == team]), team=team).dict() for team in
                    teams_by_id.values()
                ]

                await feed_publisher.publish('counts', counts)
            except httpx.ConnectError:
                await admin_publisher.publish('telraam-health', 'bad')
            except Exception as e:
                print(type(e))

            await asyncio.sleep(1)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup():
    asyncio.get_event_loop().create_task(fetch())
    await admin_publisher.publish('active-source', settings.source.dict())
    await feed_publisher.publish('message', settings.message)


@app.post('/api/use/{id}', dependencies=[Depends(admin)])
async def api_post(id: int):
    try:
        async with AsyncClient() as client:
            lap_sources: Response = await client.get(f'{settings.telraam.base_url}/lap-source')
            lap_sources_by_id: Dict[int, LapSource] = {
                ls.id: ls for ls in [LapSource(**ls) for ls in lap_sources.json()]
            }
            await admin_publisher.publish('telraam-health', 'good')
            if id in lap_sources_by_id:
                lap_source: LapSource = lap_sources_by_id[id]
                await admin_publisher.publish('active-source', lap_source.dict())
                settings.source.id = lap_source.id
                settings.source.name = lap_source.name
                settings.persist()
            else:
                raise HTTPException(status_code=HTTP_409_CONFLICT, detail='Invalid LapSource Id')
        return ['ok']
    except httpx.ConnectError:
        await admin_publisher.publish('telraam-health', 'bad')
        raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail='Can\'t reach data server')


@app.post("/api/message", status_code=HTTP_202_ACCEPTED, dependencies=[Depends(admin)])
async def post_message(message: Message):
    settings.message = message.message
    settings.persist()
    await feed_publisher.publish('message', message.message)


@app.get('/admin', response_class=HTMLResponse)
async def admin(request: Request, _=Depends(admin)):
    return templates.TemplateResponse('admin.html', {'request': request})


@app.websocket('/admin/feed')
async def admin_feed(websocket: WebSocket):
    await websocket.accept()
    queue: Queue = await admin_publisher.add()
    await admin_publisher.publish('active-connections', await admin_publisher.count() + await feed_publisher.count())
    try:
        while True:
            topic, data = await queue.get()
            await websocket.send_json({"topic": topic, "data": data})
    except websockets.exceptions.ConnectionClosedOK:
        pass
    finally:
        await admin_publisher.remove(queue)
        await admin_publisher.publish('active-connections',
                                      await admin_publisher.count() + await feed_publisher.count())


@app.websocket('/feed')
async def feed(websocket: WebSocket):
    await websocket.accept()
    queue = await feed_publisher.add()
    await admin_publisher.publish('active-connections', await admin_publisher.count() + await feed_publisher.count())
    print('Here First!')
    try:
        while True:
            print('Here!')
            topic, data = await queue.get()
            await websocket.send_json({'topic': topic, 'data': data})
    except websockets.exceptions.ConnectionClosedOK:
        pass
    finally:
        await feed_publisher.remove(queue)
        await admin_publisher.publish(
            'active-connections', await admin_publisher.count() + await feed_publisher.count()
        )
