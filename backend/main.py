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

    prompt = """
    You are an expert game developer. Convert this hand-drawn sketch into a fully functional, playable 2D web game using HTML, CSS, and JavaScript. 
    1. Use the HTML5 <canvas> element or standard DOM elements.
    2. Add basic physics, collision detection, and keyboard/mouse controls based on what the sketch implies (e.g., platformer, shooter, pong).
    3. Make it colorful and engaging.
    4. Ensure ALL CSS and JavaScript are inline within a single HTML file.
    5. Return ONLY the valid HTML code starting with <!DOCTYPE html>. Do NOT include markdown formatting like ```html.
    """

    for index, key in enumerate(API_KEYS):
        try:
            print(f"Trying API Key {index + 1}...")
            genai.configure(api_key=key)
            
            # Bhai tere kehne par direct 3.5-flash set kar diya hai
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