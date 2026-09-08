from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

@app.get("/")
def home():
    return {"status": "HandyPlus Bot is running!"}

@app.post("/whatsapp")
async def whatsapp_reply(Body: str = Form('')):
    incoming_msg = Body.strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg == '1':
        reply = (
            "🔧 *התקנות ותלייה*\n"
            "תליית טלוויזיות, מדפים, מראות, תמונות, וילונות ומסילות.\n\n"
            "אנא שלח/י תמונה של האזור המיועד לתלייה או פרט/י מה נדרש לתלות."
        )
    elif incoming_msg == '2':
        reply = (
            "🚰 *אינסטלציה*\n"
            "החלפת ברזים, סיפונים, תיקון נזילות ואיטום סיליקון.\n\n"
            "אנא צרף/י תמונה של הברז/האזור הדולף לתיאור מדויק."
        )
    elif incoming_msg == '3':
        reply = (
            "🔨 *הרכבות ותיקונים*\n"
            "הרכבת רהיטים, כיוון דלתות וצירים, תיקוני שפכטל וצבע.\n\n"
            "מה הרהיט או התיקון הנדרש? ניתן לצרף תמונה."
        )
    elif incoming_msg == '4':
        reply = (
            "💡 *חשמל ותאורה*\n"
            "החלפת שקעים ומתגים, התקנת גופי תאורה ומאווררי תקרה.\n\n"
            "פרט/י מה נדרש להתקין או לתקן."
        )
    else:
        reply = (
            "שלום! הגעתם ל-*הנדי פלוס* 🛠️\n"
            "*דיוק הנדסי בעבודות הבית*\n\n"
            "באיזה תחום מדובר?\n"
            "1️⃣ התקנות ותלייה (טלוויזיות, מדפים, וילונות)\n"
            "2️⃣ אינסטלציה (ברזים, נזילות, סיליקון)\n"
            "3️⃣ הרכבות ותיקונים (רהיטים, דלתות, שפכטל)\n"
            "4️⃣ חשמל ותאורה (גופי תאורה, שקעים)\n\n"
            "_השב/י עם המספר הרצוי או תאר/י את התקלה בצצירוף תמונה._"
        )

    msg.body(reply)
    return Response(content=str(resp), media_type="application/xml")
