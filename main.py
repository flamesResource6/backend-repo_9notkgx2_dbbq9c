import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import db, create_document, get_documents
from schemas import Earlyaccess, Contact

app = FastAPI(title="ROME API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "ROME backend running"}

class EarlyAccessRequest(BaseModel):
    email: EmailStr
    source: Optional[str] = None
    ref: Optional[str] = None

@app.post("/api/early-access")
def signup_early_access(payload: EarlyAccessRequest):
    try:
        existing = list(db["earlyaccess"].find({"email": payload.email}).limit(1)) if db else []
        if existing:
            return {"status": "ok", "message": "Already signed up", "email": payload.email}

        doc = Earlyaccess(email=payload.email, source=payload.source, ref=payload.ref)
        inserted_id = create_document("earlyaccess", doc)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats():
    try:
        total = db["earlyaccess"].count_documents({}) if db else 0
        cap = 10000
        left = max(cap - total, 0)
        return {"total_opted_in": total, "spots_left": left, "cap": cap}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ContactRequest(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    subject: Optional[str] = None
    message: str
    source: Optional[str] = None

@app.post("/api/contact")
def submit_contact(payload: ContactRequest):
    try:
        doc = Contact(**payload.model_dump())
        inserted_id = create_document("contact", doc)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
def avatar_chat(req: ChatRequest):
    try:
        user_msg = req.message.strip()
        if not user_msg:
            return {"reply": "Say something and I’ll respond!"}
        # Simple rule-based friendly bot reply
        lower = user_msg.lower()
        if any(k in lower for k in ["privacy", "data", "secure", "safety"]):
            reply = (
                "In ROME, privacy comes first. We minimize data collection, encrypt what we must, "
                "and give you clear controls over visibility. Ask me anything about how it works."
            )
        elif any(k in lower for k in ["hello", "hi", "hey"]):
            reply = "Hey! I’m your lobby companion. Want to explore mini‑games or learn about our mission?"
        elif any(k in lower for k in ["game", "play", "minigame"]):
            reply = "Let’s play! Try the Click Sprint or Whack‑a‑Dot in the mini‑games section."
        else:
            reply = f"You said: ‘{user_msg}’. I’m here to help you explore ROME."
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
