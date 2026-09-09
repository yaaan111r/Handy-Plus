import os
import traceback
import requests
from google import genai
from google.genai import types
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

@app.get("/ping")
def ping():
    return "ok"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

chat_sessions = {}

PRICE_LIST = """
מחירים לעבודה בלבד (ללא חומרים):
אינסטלציה:
- פתיחת סתימה קלה בכיור/אמבטיה/מקלחון: 180-300 ₪
- פתיחת סתימה מורכבת/צנרת ראשית: 450-700 ₪
- החלפת סיפון: 250-400 ₪
- החלפת ברז (פרח/נשלף/קיר): 280-450 ₪
- תיקון/החלפת מנגנון ניאגרה גלויה: 180-350 ₪
- תיקון/החלפת מנגנון ניאגרה סמויה: 250-380 ₪
- החלפת גומיות/אטמים: 180-250 ₪
- תיקון נזילה גלויה: 180-350 ₪
- החלפת ראש דוש/צינור: 180-280 ₪
- החלפת/התקנת ברז ניל: 180-280 ₪

חשמל ותאורה:
- התקנת גוף תאורה צמוד תקרה/קיר: 230-400 ₪
- התקנת נברשת מורכבת: 280-480 ₪
- התקנת מאוורר תקרה: 250-380 ₪
- החלפת מפסק לתריס חשמלי: 300-450 ₪

הנדימן ותלייה:
- תליית טלוויזיה: 180-280 ₪
- תליית מדפים/זרוע מיקרוגל: 180-250 ₪
- תליית תמונות/מראות: 150-280 ₪
- תליית וילון: 150-280 ₪
- אביזרי אמבטיה: 150-280 ₪

הרכבת רהיטים:
- ארון 2 דלתות: 350-550 ₪ | ארון 3-4 דלתות/הזזה: 450-750 ₪
- שידה/קומודה/שולחן/כוורת: 280-550 ₪
- מיטה: 350-650 ₪
- כיוון צירים/מסילות: 120-250 ₪

דלתות:
- כיוון דלת/החלפת ידית: 180-250 ₪

איננו מבצעים: החלפת אסלות/מונובלוק, נקודות מים חדשות, תיקון מזגנים.
"""

SYSTEM_PROMPT = f"""
אתה בוט וואטסאפ מהיר, ממוקד וקצר של 'הנדי פלוס'.
מטרתך: לאסוף פרטים במינימום הודעות ולתת הצעת מחיר.

חוקי ברזל נוקשים:
1. הודעה קצרה בלבד! מקסימום 1-2 משפטים.
2. תברך "שלום" רק בהודעה הראשונה בשיחה. לאחר מכן - אל תגיד "שלום" יותר לעולם, אלא אם אמרו שלום כלפייך!
3. **ניתוח תמונות ואישור מהמשתמש:**
   - ברגע שמתקבלת תמונה, נתח אותה מיד.
   - שאל את הלקוח בדיוק בנוסח הבא: "אני רואה בתמונה [תיאור הבעיה]. האם נדרש לבצע [תיאור השירות המבוקש המדויק מהמחירון]?"
4. **זרימת השיחה:**
   - אם המשתמש מאשר (תשובה חיובית כמו "כן", "נכון", "בדיוק"): התקדם מיד לשלב של שאלת כתובת מדויקת ודחיפות.
   - אם המשתמש משיב בשלילה (או אומר שלא לזה התכוון): פנה בצורה נעימה ובקש ממנו לחדד מה הטיפול הדרוש.
5. **עבודות שאיננו מבצעים** (כמו תיקון מזגן, החלפת אסלה, נקודת מים): ענה מיד: "אנחנו לא מבצעים עבודה זו, לבירורים ניתן לחייג 055-9821845".
6. **מתן הצעת מחיר:** לאחר אישור השירות והגדרת הכתובת/הדחיפות - תן מחיר משוער מהמחירון (עבודה בלבד) + הפניה למספר 055-9821845.

מחירון:
{PRICE_LIST}
"""

def get_or_create_chat(user_id: str):
    if user_id not in chat_sessions:
        chat_sessions[user_id] = client.chats.create(
            model='gemini-3.1-flash-lite',
            config={'system_instruction': SYSTEM_PROMPT}
        )
    return chat_sessions[user_id]

def fetch_image_from_twilio(media_url: str) -> bytes | None:
    try:
        auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None
        res = requests.get(media_url, auth=auth, timeout=10)
        if res.status_code == 200:
            return res.content
    except Exception as e:
        print(f"Failed to download image from Twilio: {e}")
    return None

@app.get("/")
def home():
    return {"status": "Handy Plus Fast Bot is running!"}

@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(default=""),
    Body: str = Form(default=""),
    NumMedia: int = Form(default=0),
    MediaUrl0: str = Form(default=""),
    ContentType0: str = Form(default="")
):
    twiml = MessagingResponse()
    user_msg = Body.strip() if Body else ""
    user_id = From.strip() if From else "default_user"

    if not client:
        twiml.message("שלום! ליצירת קשר עם הנדי פלוס חייג: 055-9821845")
        return Response(content=str(twiml), media_type="application/xml")

    contents = []

    if NumMedia > 0 and MediaUrl0:
        image_bytes = fetch_image_from_twilio(MediaUrl0)
        if image_bytes:
            mime_type = ContentType0 if ContentType0 else "image/jpeg"
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
            contents.append(image_part)

    if user_msg:
        contents.append(user_msg)

    if not contents:
        twiml.message("שלום! הגעת להנדי פלוס. במה נוכל לעזור?")
        return Response(content=str(twiml), media_type="application/xml")

    bot_reply = None
    payload = contents if len(contents) > 1 else contents[0]

    try:
        chat = get_or_create_chat(user_id)
        response = chat.send_message(payload)
        if response and response.text:
            bot_reply = response.text.strip()
    except Exception as e:
        print(f"Chat Session error for {user_id}, resetting session: {e}")
        try:
            chat_sessions[user_id] = client.chats.create(
                model='gemini-3.1-flash-lite',
                config={'system_instruction': SYSTEM_PROMPT}
            )
            response = chat_sessions[user_id].send_message(payload)
            if response and response.text:
                bot_reply = response.text.strip()
        except Exception as inner_e:
            print(f"Critical Gemini API Error: {inner_e}")
            traceback.print_exc()

    if not bot_reply:
        bot_reply = "במה נוכל לעזור בתחום התיקונים? לפרטים נוספים ניתן גם לחייג 055-9821845."

    twiml.message(bot_reply)
    return Response(content=str(twiml), media_type="application/xml")
