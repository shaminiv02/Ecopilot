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
    
    response = model.generate_content(prompt)
    lines = response.text.strip().split('\n')
    
    try:
        # Parsing the LLM output
        data = {line.split(': ')[0]: line.split(': ')[1] for line in lines if ': ' in line}
        
        # Calculate a mock score based on the parsed data
        eco_score = calculate_score(
            sustainability=float(data.get('Sustainability_Metric', 50)),
            cost=80, # Hardcoded for MVP
            convenience=100 - abs(float(data.get('Time_Impact_mins', 0))) # Simple convenience metric
        )

        return {
            "status": "success",
            "alternative": data.get("Alternative"),
            "co2_saved": data.get("CO2_Saved_kg"),
            "time_impact": data.get("Time_Impact_mins"),
            "nudge": data.get("Nudge"),
            "eco_score": eco_score
        }
    except Exception as e:
        return {"status": "error", "message": "Failed to parse AI response. Try again."}