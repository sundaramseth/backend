import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import time
from supabase import create_client
import json

SUPABASE_URL = "https://xqfdhuaihalkptpvlive.supabase.co"
SUPABASE_KEY = "sb_publishable_OJbjN67mLIMpRpQjzptNaQ_UAn1PxgY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]   

MODEL_NAME = "llama-3.1-8b-instant"  

def generate_stream(messages):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        stream=True  #IMPORTANT
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            yield json.dumps({"content": content}) + "\n"
            time.sleep(0.02)  # smooth typing


@app.post("/chat-stream")
async def chat_stream(data: dict):
    messages = data.get("messages", [])
    return StreamingResponse(generate_stream(messages), media_type="application/json")

@app.post("/save-chat")
async def save_chat(data: dict):
    user_id = data["user_id"]
    title = data["title"]

    res = supabase.table("chats").insert({
        "user_id": user_id,
        "title": title
    }).execute()

    return res.data

@app.post("/save-message")
async def save_message(data: dict):
    supabase.table("messages").insert({
        "chat_id": data["chat_id"],
        "role": data["role"],
        "content": data["content"]
    }).execute()

    return {"status": "ok"}

@app.get("/get-chats/{user_id}")
async def get_chats(user_id: str):
    res = supabase.table("chats").select("*").eq("user_id", user_id).execute()
    return res.data

@app.get("/get-messages/{chat_id}")
async def get_messages(chat_id: str):
    res = supabase.table("messages").select("*").eq("chat_id", chat_id).execute()
    return res.data