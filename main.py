import os
import traceback
from google import genai
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()
@app.get("/ping")
def ping():
    return "ok"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# זיכרון שיחות בזיכרון השרת
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
3. **אם הלקוח מבקש עבודה שאיננו מבצעים** (כמו תיקון מזגן, החלפת אסלה): ענה מיד: "אנחנו לא מבצעים עבודה זו, לבירורים ניתן לחייג 055-9821845".
4. **איסור חזרה על שאלות:** אם הלקוח לא שלח תמונה או מיקום, התקדם מיד לשלב הבא!
5. זרימה:
   - שלב 1: שאל על תיאור התקלה כולל בקשה לתמונה שמתארת את המצב - פנה בצורה נעימה וחברית.
   - שלב 2: שאל לגבי כתובת מדויקת ודחיפות במיידי או גמיש.
   - שלב 3: תן מחיר משוער מהמחירון (עבודה בלבד) + הפניה למספר 055-9821845.

מחירון:
{PRICE_LIST}
"""

def get_or_create_chat(user_id: str):
    """יוצר או משחזר סשן צ'אט בטוח"""
    if user_id not in chat_sessions:
        chat_sessions[user_id] = client.chats.create(
            model='gemini-3.1-flash-lite',
            config={'system_instruction': SYSTEM_PROMPT}
        )
    return chat_sessions[user_id]

@app.get("/")
def home():
    return {"status": "Handy Plus Fast Bot is running!"}

@app.post("/whatsapp")
async def whatsapp_webhook(From: str = Form(default=""), Body: str = Form(default="")):
    twiml = MessagingResponse()
    user_msg = Body.strip() if Body else ""
    user_id = From.strip() if From else "default_user"

    if not user_msg:
        twiml.message("שלום! הגעת להנדי פלוס. במה נוכל לעזור?")
        return Response(content=str(twiml), media_type="application/xml")

    if not client:
        twiml.message("שלום! ליצירת קשר עם הנדי פלוס חייג: 055-9821845")
        return Response(content=str(twiml), media_type="application/xml")

    bot_reply = None

    # ניסיון ראשון לשלוח הודעה דרך הסשן הקיים
    try:
        chat = get_or_create_chat(user_id)
        response = chat.send_message(user_msg)
        if response and response.text:
            bot_reply = response.text.strip()
    except Exception as e:
        print(f"Chat Session error for {user_id}, resetting session: {e}")
        # אם הסשן נשבר, מאפסים אותו ומנסים שוב
        try:
            chat_sessions[user_id] = client.chats.create(
                model='gemini-3.1-flash-lite',
                config={'system_instruction': SYSTEM_PROMPT}
            )
            response = chat_sessions[user_id].send_message(user_msg)
            if response and response.text:
                bot_reply = response.text.strip()
        except Exception as inner_e:
            print(f"Critical Gemini API Error: {inner_e}")
            traceback.print_exc()

    # אם גם אחרי האיפוס Gemini לא החזיר תשובה
    if not bot_reply:
        bot_reply = "במה נוכל לעזור בתחום התיקונים? לפרטים נוספים ניתן גם לחייג 055-9821845."

    twiml.message(bot_reply)
    return Response(content=str(twiml), media_type="application/xml")
