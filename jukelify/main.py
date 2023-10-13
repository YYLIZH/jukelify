from fastapi import FastAPI, HTTPException, Request
from linebot.exceptions import InvalidSignatureError

from jukelify.line import handler

app = FastAPI()


@app.get("/")
async def root(request: Request):
    return "Welcome to jukelify"


@app.get("/webhook")
async def checkWebhook(request: Request):
    return {"webhook": "OK"}


@app.post("/webhook")
async def jukelify(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Missing Parameters")
    return "OK"
