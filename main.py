import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from database import db, create_document, get_documents
from schemas import Competitionentry

app = FastAPI(title="Competition Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Competition API running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
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
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
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
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# ---------------- Competition Endpoints ----------------

class EntryResponse(BaseModel):
    success: bool
    id: Optional[str] = None
    message: str

@app.post("/api/competition/entry", response_model=EntryResponse)
async def create_entry(entry: Competitionentry):
    """Create a new competition entry"""
    if not entry.consent_terms:
        raise HTTPException(status_code=400, detail="You must accept the terms and conditions to enter.")

    try:
        inserted_id = create_document("competitionentry", entry)
        return EntryResponse(success=True, id=inserted_id, message="Entry received. Good luck!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit entry: {str(e)}")

@app.get("/api/competition/entries/count")
def entries_count():
    """Public stats: number of entries so far"""
    try:
        count = db["competitionentry"].count_documents({}) if db else 0
        return {"count": int(count)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch count: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
