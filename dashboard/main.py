# main.py
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from typing import List, Optional

# Initialize FastAPI
import os, sys
#sys.path.insert(0, os.path.abspath("./"))

for p in sys.path:
    print(p)

app = FastAPI()
app.mount("/static", StaticFiles(directory="./dashboard/static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database setup
def get_db():
    with sqlite3.connect('db/downloads.db') as conn:
        conn.row_factory = sqlite3.Row
        yield conn

# Create tables on startup
@app.on_event("startup")
def startup():
    with sqlite3.connect('db/downloads.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_url TEXT NOT NULL,
                channel_type TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# Pydantic models
class ChannelCreate(BaseModel):
    channel_url: str
    channel_type: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("add_channel.html", {"request": request})

@app.get("/downloads", response_class=HTMLResponse)
async def show_downloads(
    request: Request,
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        downloads = db.execute('''
            SELECT id, video_url, audio_file_path, 
                   transcript_file_path, download_time 
            FROM content_downloads 
            ORDER BY download_time DESC
        ''').fetchall()
        
        return templates.TemplateResponse("downloads.html", {
            "request": request,
            "downloads": [dict(row) for row in downloads]
        })
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/channels")
async def create_channel(
    channel: ChannelCreate,
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        db.execute('''
            INSERT INTO channels (channel_url, channel_type)
            VALUES (?, ?)
        ''', (channel.channel_url, channel.channel_type))
        db.commit()
        return RedirectResponse(url="/", status_code=303)
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Channel already exists")
    except sqlite3.Error as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)