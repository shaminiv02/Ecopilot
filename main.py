from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI()

# Allow the Chrome Extension to talk to this local server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your extension's ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
# Run this in terminal first: export GEMINI_API_KEY="your_actual_key"
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

class UserContext(BaseModel):
    platform: str # e.g., "Uber", "Amazon", "Zomato"
    action_details: str # e.g., "Ride from T-Nagar to Adyar"

def calculate_score(sustainability, cost, convenience):
    """Calculates the EcoScore out of 100"""
    return round((sustainability * 0.5) + (cost * 0.3) + (convenience * 0.2))

@app.post("/analyze")
async def analyze_decision(context: UserContext):
    # Prompting the LLM to generate the intelligent response
    prompt = f"""
    The user is currently on {context.platform} and is about to do this: {context.action_details}.
    Provide a real-time, sustainable alternative that balances convenience.
    
    Return EXACTLY in this format (no markdown, no extra text):
    Alternative: [Your suggested alternative]
    CO2_Saved_kg: [number]
    Time_Impact_mins: [number, use negative for faster, positive for slower]
    Nudge: [One persuasive, encouraging sentence]
    Sustainability_Metric: [A number from 1 to 100 rating the original action's eco-friendliness]
    """
    
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        return {"status": "error", "message": f"AI API call failed: {str(e)}"}

    # Extract text from common response shapes. Different client versions
    # may provide `text`, `candidates`, or other wrappers — handle them.
    text = ""
    if hasattr(response, "text") and isinstance(response.text, str):
        text = response.text
    elif hasattr(response, "candidates") and getattr(response, "candidates"):
        first = response.candidates[0]
        text = getattr(first, "content", None) or getattr(first, "text", "") or str(first)
    else:
        # Fallback to stringifying the whole response
        try:
            text = str(response)
        except Exception:
            text = ""

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    try:
        # Robust parsing: use partition to avoid fragile splits and accept slight key variations
        data = {}
        for line in lines:
            if ':' in line:
                key, _, val = line.partition(':')
                data[key.strip()] = val.strip().strip('"')

        def to_float(key, default=None):
            v = data.get(key)
            if v is None or v == "":
                return default
            try:
                return float(v)
            except Exception:
                return default

        alternative = data.get('Alternative') or data.get('alternative')
        co2 = to_float('CO2_Saved_kg') or to_float('CO2_Saved') or 0.0
        time_impact = to_float('Time_Impact_mins') or to_float('Time_Impact') or 0.0
        nudge = data.get('Nudge') or data.get('nudge') or ""
        sustainability_metric = to_float('Sustainability_Metric') or to_float('Sustainability') or 50.0

        # Normalize inputs and compute eco score
        sustainability = max(0, min(100, sustainability_metric))
        cost = 80
        convenience = max(0, min(100, 100 - abs(time_impact)))

        eco_score = calculate_score(
            sustainability=sustainability,
            cost=cost,
            convenience=convenience
        )

        return {
            "status": "success",
            "alternative": alternative,
            "co2_saved": round(co2, 3),
            "time_impact": time_impact,
            "nudge": nudge,
            "eco_score": eco_score,
            "raw_text": text
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse AI response: {str(e)}", "response_text": text}