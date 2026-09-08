import os
from google import genai
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

# התחברות ל-Gemini API באמצעות ה-SDK החדש
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

@app.get("/")
def home():
    return {"status": "Handy Plus WhatsApp Bot is running!"}

@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...)):
    try:
        if not client:
            bot_reply = "שלום! הגעת להנדי פלוס. המערכת בשידרוג קל, נחזור אליך בהקדם."
        else:
            # קריאה למודל ה-Flash העדכני ביותר
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=Body,
                config={
                    'system_instruction': (
                        "אתה עוזר וירטואלי חכם, אדיב ומקצועי עבור 'הנדי פלוס' - עסק לתיקונים, אינסטלציה וחשמל. "
                        "תפקידך לענות ללקוחות ב-WhatsApp בצורה קצרה, ברורה ועניינית, לספק מידע על השירותים, "
                        "ולסייע באיסוף פרטים מלקוחות (שם, כתובת, תיאור התקלה וזמינות)."
                    )
                }
            )
            bot_reply = response.text.strip()
            
    except Exception as e:
        print(f"Error generating AI response: {e}")
        bot_reply = "תודה שפנית להנדי פלוס! נציג יחזור אליך בהקדם."

    twiml = MessagingResponse()
    twiml.message(bot_reply)
    
    return Response(content=str(twiml), media_type="application/xml")
