from fastapi import FastAPI, Request
from telegram import Update
from .bot import create_application

app = FastAPI()

application = create_application()

@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.start()

@app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.shutdown()

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    # Convert Telegram's JSON into a python-telegram-bot Update
    update = Update.de_json(data, application.bot)

    await application.process_update(update)

    return {"ok": True}