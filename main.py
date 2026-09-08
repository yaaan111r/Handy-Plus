import os
import google.generativeai as genai
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

# טעינת המפתח ממשתני הסביבה ב-Render
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# הגדרת חיבור ל-Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# הגדרת המודל וההנחיות (System Prompt) עבור "הנדי פלוס"
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "אתה עוזר וירטואלי חכם, אדיב ומקצועי עבור 'הנדי פלוס' - עסק לתיקונים, אינסטלציה וחשמל. "
        "תפקידך לענות ללקוחות ב-WhatsApp בערבית או בעברית (לפי שפת הפנייה של הלקוח), "
        "לספק מענה קצר, ברור וענייני, ולסייע בהבנת التקלה או באיסוף הפרטים (שם, כתובת ותיאור הבעיה)."
    )
)

@app.get("/")
def home():
    return {"status": "Handy Plus WhatsApp Bot is running!"}

@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...)):
    try:
        if not GEMINI_API_KEY:
            bot_reply = "שלום! הגעת להנדי פלוס. המערכת בשידרוג קל, נחזור אליך בהקדם."
        else:
            # פנייה למודל Gemini לקבלת תשובה חכמה
            response = model.generate_content(Body)
            bot_reply = response.text.strip()
            
    except Exception as e:
        print(f"Error generating AI response: {e}")
        bot_reply = "תודה שפנית להנדי פלוס! נציג יחזור אליך בהקדם."

    # החזרת התשובה בפורמט TwiML ל-WhatsApp
    twiml = MessagingResponse()
    twiml.message(bot_reply)
    
    return Response(content=str(twiml), media_type="application/xml")
