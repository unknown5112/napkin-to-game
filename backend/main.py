import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS: Frontend ko backend se baat karne ki permission
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Render environment variables se saari keys uthayega
KEYS_ENV = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in KEYS_ENV.split(",") if k.strip()]

class GameRequest(BaseModel):
    image: str

@app.post("/generate-game")
async def generate_game(request: GameRequest):
    if not API_KEYS:
        raise HTTPException(status_code=500, detail="API keys backend mein configure nahi hain.")

    # Base64 string ko clean karna
    img_data = request.image
    if "," in img_data:
        img_data = img_data.split(",")[1]

    # GAME GENERATION PROMPT 🎮
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
            
            # Using flash model for speed and low cost
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content([
                prompt, 
                {"mime_type": "image/jpeg", "data": img_data}
            ])
            
            final_code = response.text.strip()
            if final_code.startswith("```html"):
                final_code = final_code.replace("```html", "", 1)
            if final_code.endswith("```"):
                final_code = final_code.rsplit("```", 1)[0].strip()

            return {"success": True, "code": final_code}

        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
                print(f"Key {index + 1} ki limit khatam. Switching to next key...")
                continue
            else:
                raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=429, detail="Saari API keys ki limit khatam ho chuki hai.")