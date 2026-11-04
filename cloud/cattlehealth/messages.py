"""Farmer-facing alert text. Translations should be reviewed by native speakers before launch."""
# -*- coding: utf-8 -*-

LANGS = ("en", "hi", "mr", "gu", "ta")

MESSAGES = {
    "en": {
        "fever": "🌡️ {cow}: fever {temp}°C (normal ~{base}°C). Call your vet today and check the udder for mastitis.",
        "hypothermia": "❄️ {cow}: low temperature {temp}°C. Possible milk fever — call the vet now.",
        "rumination": "🌿 {cow}: rumination low — {mins} min in 24 h (usual {usual}). Check feed, water and for illness.",
        "heat": "💕 {cow} is in heat (activity {ratio}× normal). Best insemination window: next 12 hours.",
        "low_battery": "🔋 {cow}: tag battery low ({mv} mV). Replace within 2 weeks.",
        "tamper": "⚠️ {cow}: collar strap open or tag removed.",
        "offline": "📡 {cow}: no signal for {hours} h. Check the collar and the gateway.",
        "summary": "🐄 {farm}: {n} cows · {ok} healthy · {alerts} need attention.",
    },
    "hi": {
        "fever": "🌡️ {cow}: बुखार {temp}°C (सामान्य ~{base}°C)। आज ही पशु चिकित्सक को बुलाएँ और थन में थनैला की जाँच करें।",
        "hypothermia": "❄️ {cow}: तापमान कम {temp}°C। मिल्क फीवर हो सकता है — तुरंत पशु चिकित्सक को बुलाएँ।",
        "rumination": "🌿 {cow}: जुगाली कम — 24 घंटे में {mins} मिनट (सामान्य {usual})। चारा, पानी और बीमारी की जाँच करें।",
        "heat": "💕 {cow} गर्मी (हीट) में है (गतिविधि सामान्य से {ratio}× अधिक)। गर्भाधान का सबसे अच्छा समय: अगले 12 घंटे।",
        "low_battery": "🔋 {cow}: टैग की बैटरी कम ({mv} mV)। 2 सप्ताह में बदलें।",
        "tamper": "⚠️ {cow}: पट्टा खुला है या टैग हटाया गया है।",
        "offline": "📡 {cow}: {hours} घंटे से कोई सिग्नल नहीं। पट्टा और गेटवे जाँचें।",
        "summary": "🐄 {farm}: {n} पशु · {ok} स्वस्थ · {alerts} पर ध्यान दें।",
    },
    "mr": {
        "fever": "🌡️ {cow}: ताप {temp}°C (सामान्य ~{base}°C). आजच पशुवैद्यांना बोलवा आणि कासेत स्तनदाह तपासा.",
        "hypothermia": "❄️ {cow}: तापमान कमी {temp}°C. मिल्क फीवर असू शकतो — लगेच पशुवैद्यांना बोलवा.",
        "rumination": "🌿 {cow}: रवंथ कमी — 24 तासांत {mins} मिनिटे (सामान्य {usual}). चारा, पाणी व आजार तपासा.",
        "heat": "💕 {cow} माजावर आहे (हालचाल सामान्यपेक्षा {ratio}× जास्त). रेतनासाठी योग्य वेळ: पुढील 12 तास.",
        "low_battery": "🔋 {cow}: टॅगची बॅटरी कमी ({mv} mV). 2 आठवड्यांत बदला.",
        "tamper": "⚠️ {cow}: पट्टा उघडा आहे किंवा टॅग काढला आहे.",
        "offline": "📡 {cow}: {hours} तासांपासून सिग्नल नाही. पट्टा व गेटवे तपासा.",
        "summary": "🐄 {farm}: {n} जनावरे · {ok} निरोगी · {alerts} कडे लक्ष द्या.",
    },
    "gu": {
        "fever": "🌡️ {cow}: તાવ {temp}°C (સામાન્ય ~{base}°C). આજે જ પશુ ડૉક્ટરને બોલાવો અને આંચળમાં મસ્ટાઇટિસ તપાસો.",
        "hypothermia": "❄️ {cow}: તાપમાન ઓછું {temp}°C. મિલ્ક ફીવર હોઈ શકે — તરત પશુ ડૉક્ટરને બોલાવો.",
        "rumination": "🌿 {cow}: વાગોળવું ઓછું — 24 કલાકમાં {mins} મિનિટ (સામાન્ય {usual}). ચારો, પાણી અને બીમારી તપાસો.",
        "heat": "💕 {cow} ગરમીમાં છે (હલનચલન સામાન્ય કરતાં {ratio}× વધુ). બીજદાન માટે શ્રેષ્ઠ સમય: આગામી 12 કલાક.",
        "low_battery": "🔋 {cow}: ટૅગની બૅટરી ઓછી ({mv} mV). 2 અઠવાડિયામાં બદલો.",
        "tamper": "⚠️ {cow}: પટ્ટો ખુલ્લો છે અથવા ટૅગ કાઢી નાખ્યો છે.",
        "offline": "📡 {cow}: {hours} કલાકથી સિગ્નલ નથી. પટ્ટો અને ગેટવે તપાસો.",
        "summary": "🐄 {farm}: {n} પશુ · {ok} સ્વસ્થ · {alerts} પર ધ્યાન આપો.",
    },
    "ta": {
        "fever": "🌡️ {cow}: காய்ச்சல் {temp}°C (இயல்பு ~{base}°C). இன்றே கால்நடை மருத்துவரை அழைத்து மடிவீக்கம் உள்ளதா பார்க்கவும்.",
        "hypothermia": "❄️ {cow}: வெப்பநிலை குறைவு {temp}°C. பால் காய்ச்சலாக இருக்கலாம் — உடனே மருத்துவரை அழைக்கவும்.",
        "rumination": "🌿 {cow}: அசைபோடுதல் குறைவு — 24 மணி நேரத்தில் {mins} நிமிடம் (வழக்கம் {usual}). தீவனம், தண்ணீர், நோய் உள்ளதா பார்க்கவும்.",
        "heat": "💕 {cow} சினைப்பருவத்தில் உள்ளது (இயக்கம் இயல்பை விட {ratio}× அதிகம்). கருவூட்டலுக்கு சிறந்த நேரம்: அடுத்த 12 மணி நேரம்.",
        "low_battery": "🔋 {cow}: டேக் பேட்டரி குறைவு ({mv} mV). 2 வாரங்களுக்குள் மாற்றவும்.",
        "tamper": "⚠️ {cow}: பட்டை திறந்துள்ளது அல்லது டேக் அகற்றப்பட்டது.",
        "offline": "📡 {cow}: {hours} மணி நேரமாக சிக்னல் இல்லை. பட்டை மற்றும் கேட்வேயைச் சரிபார்க்கவும்.",
        "summary": "🐄 {farm}: {n} மாடுகள் · {ok} நலம் · {alerts} கவனிக்க வேண்டும்.",
    },
}


def render(kind: str, lang: str = "en", **params) -> str:
    table = MESSAGES.get(lang) or MESSAGES["en"]
    tpl = table.get(kind) or MESSAGES["en"][kind]
    try:
        return tpl.format(**params)
    except KeyError:
        return MESSAGES["en"][kind].format(**params)
