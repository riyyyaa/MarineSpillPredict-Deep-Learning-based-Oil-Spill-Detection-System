from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import base64
import os

from pydantic import BaseModel
from database import db
from auth import jwt_auth
from utils import prediction, email

app = FastAPI(title="Oil Spill Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BACKEND_DIR, '..', 'static')
TEMPLATES_DIR = os.path.join(BACKEND_DIR, '..', 'templates')

# Ensure directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Serve frontend
@app.get("/")
def serve_frontend():
    index_path = os.path.join(TEMPLATES_DIR, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Frontend not found"}

# --- Pydantic Schemas ---
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class HistoryResponse(BaseModel):
    id: int
    image_name: str
    oil_percentage: float
    confidence_score: float
    model_used: str
    created_at: str

class FAQResponse(BaseModel):
    id: int
    question: str
    answer: str

# --- Dependencies ---
def get_current_user(token: str = Depends(jwt_auth.oauth2_scheme), session: Session = Depends(db.get_db)):
    payload = jwt_auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = payload.get("sub")
    user = session.query(db.User).filter(db.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# --- Routes ---

@app.post("/register", response_model=Token)
def register(user: UserCreate, session: Session = Depends(db.get_db)):
    db_user = session.query(db.User).filter(db.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = jwt_auth.get_password_hash(user.password)
    new_user = db.User(name=user.name, email=user.email, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    access_token = jwt_auth.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(user: UserLogin, session: Session = Depends(db.get_db)):
    db_user = session.query(db.User).filter(db.User.email == user.email).first()
    if not db_user or not jwt_auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = jwt_auth.create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def read_users_me(current_user: db.User = Depends(get_current_user)):
    return {"name": current_user.name, "email": current_user.email}

@app.post("/predict")
async def predict_spill(
    file: UploadFile = File(...),
    model: str = Form("DeepLab"),
    current_user: db.User = Depends(get_current_user),
    session: Session = Depends(db.get_db)
):
    try:
        content = await file.read()
        result = prediction.process_image(content, model_name=model)
        # prediction.process_image may return (mask_bytes, oil_pct, conf) or
        # (mask_bytes, oil_pct, conf, message)
        if isinstance(result, tuple) and len(result) == 4:
            mask_bytes, oil_pct, conf, custom_message = result
        else:
            mask_bytes, oil_pct, conf = result
            custom_message = None
        
        # Save History
        history_entry = db.History(
            user_id=current_user.id,
            image_name=file.filename,
            oil_percentage=oil_pct,
            confidence_score=conf,
            model_used=model
        )
        session.add(history_entry)
        session.commit()
        
        # Trigger Email if oil detected > threshold (e.g., 5%)
        if oil_pct > 5.0:
            email.send_spill_alert(current_user.email, oil_pct, conf)
            
        base64_mask = base64.b64encode(mask_bytes).decode('utf-8')
        
        return {
            "mask": f"data:image/png;base64,{base64_mask}",
            "oil_percentage": round(oil_pct, 2),
            "confidence": round(conf, 2),
            "model": model,
            "message": custom_message if custom_message is not None else ("Spill detected and email sent!" if oil_pct > 5.0 else "No significant spill detected.")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", response_model=List[HistoryResponse])
def get_history(current_user: db.User = Depends(get_current_user), session: Session = Depends(db.get_db)):
    records = session.query(db.History).filter(db.History.user_id == current_user.id).order_by(db.History.created_at.desc()).all()
    
    return [
        HistoryResponse(
            id=r.id,
            image_name=r.image_name,
            oil_percentage=r.oil_percentage,
            confidence_score=r.confidence_score,
            model_used=r.model_used,
            created_at=r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ) for r in records
    ]

@app.get("/faqs", response_model=List[FAQResponse])
def get_faqs(session: Session = Depends(db.get_db)):
    records = session.query(db.FAQ).order_by(db.FAQ.id).all()
    return [
        FAQResponse(
            id=r.id,
            question=r.question,
            answer=r.answer
        ) for r in records
    ]

@app.on_event("startup")
def seed_faqs():
    session = db.SessionLocal()
    try:
        if session.query(db.FAQ).count() == 0:
            seed = [
                {"question": "What is an oil spill?", "answer": "An oil spill is the release of oil into oceans, rivers, or coastal areas causing environmental pollution."},
                {"question": "Why is oil spill detection important?", "answer": "It helps protect marine life, water quality, and coastal ecosystems from pollution damage."},
                {"question": "What causes oil spills?", "answer": "Oil spills can occur due to tanker accidents, pipeline leaks, drilling issues, or industrial activities."},
                {"question": "How does this monitoring system work?", "answer": "The system analyzes uploaded images and generates detection results with alert notifications."},
                {"question": "What happens after spill detection?", "answer": "The system displays alerts and supports emergency response workflow."},
                {"question": "What is marine pollution?", "answer": "Marine pollution is contamination of oceans and water bodies caused by harmful substances."},
                {"question": "How do oil spills affect marine animals?", "answer": "Oil spills can harm fish, birds, turtles, and other marine organisms by contaminating water and food sources."},
                {"question": "What is coastal protection?", "answer": "Coastal protection includes measures taken to protect shorelines and marine environments from pollution and damage."},
                {"question": "What are emergency response systems?", "answer": "Emergency response systems help authorities react quickly during environmental or marine incidents."},
                {"question": "What technologies are used in this project?", "answer": "This project uses Flask, React, image monitoring workflow, and email alert systems."},
                {"question": "What is marine engineering?", "answer": "Marine engineering involves the design and maintenance of ships, marine systems, and ocean-related technologies."},
                {"question": "Why is ocean monitoring necessary?", "answer": "Ocean monitoring helps identify pollution, environmental changes, and marine safety risks."},
                {"question": "How can oil spills be prevented?", "answer": "Oil spills can be reduced through proper maintenance, monitoring systems, and safety regulations."},
                {"question": "What is environmental protection?", "answer": "Environmental protection focuses on preserving natural ecosystems and reducing pollution."},
                {"question": "How does the alert system help users?", "answer": "The alert system provides quick notifications to improve awareness and support timely response actions."}
            ]
            for f in seed:
                session.add(db.FAQ(question=f["question"], answer=f["answer"]))
            session.commit()
    finally:
        session.close()
