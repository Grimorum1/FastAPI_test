from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from fastapi.responses import JSONResponse




messages: dict[int, str] = {}
# храним события
events: dict[int, asyncio.Event] = {}


class Message(BaseModel):
    message_id: int
    message: str



app = FastAPI()


@app.post("/send")
async def send_message(message: Message):
    if message.message_id in messages:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": "Сообщение с таким id уже существует"}
        )

    messages[message.message_id] = message.message
    if message.message_id in events:
        events[message.message_id].set()

    return {"status": "ok"}


@app.get("/get/{message_id}")
async def get_message(message_id: int):
    if message_id in messages:
        return {"message_id": message_id, "message": messages[message_id]}

    # Создаем событие для этого message_id, если его еще нет
    if message_id not in events:
        events[message_id] = asyncio.Event()

    try:
        # Ждем появления сообщения или таймаута
        await asyncio.wait_for(events[message_id].wait(), timeout=60)
    except asyncio.TimeoutError:
        del events[message_id]
        raise HTTPException(status_code=404, detail="Сообщение не найдено ")

    # Проверяем, появилось ли сообщение после пробуждения
    if message_id in messages:
        return {"message_id": message_id, "message": messages[message_id]}
    else:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")