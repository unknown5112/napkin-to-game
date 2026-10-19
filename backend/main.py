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

    # 🚀 ULTIMATE UNIVERSAL GAME ENGINE PROMPT
    prompt = """
    You are an elite Game Developer and AI Game Engine. Your task is to deeply analyze this hand-drawn sketch, dynamically determine its genre, and build a flawless, fully playable 2D HTML5 game. 

    Follow this Universal Game Framework STRICTLY:
    1. GENRE & PHYSICS ANALYSIS: First, look at the layout. 
       - If it's a side-scroller/platformer (like Mario): Apply gravity, ground collision, and jumping mechanics.
       - If it's a top-down game (like Pac-Man, RPG, or Maze): Disable gravity, allow free 4-way movement (up/down/left/right), and set wall collisions.
       - If it's a space/shooter or racing game: Apply constant forward momentum, projectile mechanics, or steering logic.
    2. SMART OBJECT RECOGNITION: Identify ALL drawn elements and make them fully INTERACTIVE.
       - Platforms/Walls: Solid collisions.
       - Stairs/Ladders/Vines: If present, disable gravity when overlapping and allow vertical climbing.
       - Hazards (Spikes, Lava, Monsters): Cause 'Game Over' on touch.
       - Collectibles (Coins, Gems, Stars): Increase score and disappear on touch.
       - Goals (Doors, Flags, Trophies): Trigger 'You Win' screen.
    3. ADAPTIVE MOBILE CONTROLS (CRITICAL): You MUST build intuitive on-screen touch buttons or a virtual joystick that matches the genre. For platformers: Left, Right, Jump, Climb. For top-down: 4-way D-Pad. Bind touch events (touchstart, touchend) to these visible buttons. Keyboard keys (arrows/WASD) must also work as a fallback.
    4. GAME LOOP & UI: Include a proper game loop, score counter, Win/Loss states, and a 'Restart' button. Make the visuals colorful and adapt the canvas to fit beautifully on mobile screens.
    5. Ensure ALL CSS and JavaScript are strictly inline within a single HTML file.
    6. Return ONLY the valid HTML code starting with <!DOCTYPE html>. Do NOT include markdown formatting like ```html.
    """

    for index, key in enumerate(API_KEYS):
        try:
            print(f"Trying API Key {index + 1}...")
            genai.configure(api_key=key)
            
            chosen_model = 'gemini-3.5-flash'
            print(f"🚀 Humne select kiya: {chosen_model}")
            
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