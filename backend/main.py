import os
import base64
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KEYS_ENV = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in KEYS_ENV.split(",") if k.strip()]

class GameRequest(BaseModel):
    image: str

@app.post("/generate-game")
async def generate_game(request: GameRequest):
    if not API_KEYS:
        raise HTTPException(status_code=500, detail="API keys are not configured.")

    img_data = request.image
    if "," in img_data:
        img_data = img_data.split(",")[1]
        
    try:
        image_bytes = base64.b64decode(img_data)
    except Exception as e:
        print(f"🚨 Decode Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid image format.")

    # 🚀 THE ULTIMATE PROMPT: Smart UI, No Blank Screens, Ladder Fix, Camera Tracking
    prompt = """
    You are an elite Game Developer. Convert this hand-drawn sketch into a flawlessly playable 2D HTML5 game. 
    Follow this STRICT Universal Framework:
    1. ANTI-BLANK GUARANTEE: You MUST generate visible game objects, a clear player character, ground/platforms, and a contrasting background. Never output an empty or broken canvas.
    2. SMART DEVICE DETECTION & UI: Use JavaScript (e.g., `'ontouchstart' in window`) to detect the device type dynamically.
       - IF MOBILE/TABLET: Render large, visible on-screen touch controls (Left, Right, Up/Jump, Down) and bind touch events. The game can start immediately.
       - IF DESKTOP/PC: Completely HIDE all on-screen touch buttons. Instead, show a "How to Play" overlay screen at startup that maps out the keyboard controls (e.g., Arrow Keys to move, Space to jump). Include a clear "Start Game" button on this overlay that dismisses the screen and begins the game loop.
    3. GENRE & PHYSICS: Apply gravity for platformers, or 4-way top-down movement if the sketch implies a maze/RPG.
    4. LADDER/CLIMBING LOGIC (CRITICAL FIX): If ladders/stairs exist, implement a strict state machine. If the player intersects a ladder AND presses UP or DOWN, set `isClimbing = true`. While climbing, set gravity and Y-velocity to 0, and move Y manually based on input. Restore gravity when jumping or leaving the ladder.
    5. CAMERA TRACKING (PRO FEATURE): If the generated level is wider/taller than the canvas view, implement a dynamic camera system that keeps the player centered on the screen.
    6. Ensure ALL CSS and JavaScript are strictly inline within a single HTML file.
    7. Return ONLY the valid HTML code starting with <!DOCTYPE html>. Do NOT include markdown formatting like ```html.
    """

    for index, key in enumerate(API_KEYS):
        try:
            print(f"Trying API Key {index + 1}...")
            genai.configure(api_key=key)
            
            chosen_model = 'gemini-3.5-flash'
            
            model = genai.GenerativeModel(chosen_model)
            
            response = model.generate_content([
                prompt, 
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
            
            final_code = response.text.strip()
            
            if final_code.startswith("```html"):
                final_code = final_code.replace("```html", "", 1)
            if final_code.endswith("```"):
                final_code = final_code.rsplit("```", 1)[0].strip()

            return {"success": True, "code": final_code}

        except Exception as e:
            error_msg = str(e).lower()
            print(f"🚨 Key {index + 1} Error: {e}") 
            
            if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
                print(f"Key {index + 1} quota exhausted. Switching to next key...")
                continue
            else:
                raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=429, detail="All API keys have exhausted their quota.")