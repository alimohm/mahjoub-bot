from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- إعدادات البوت من TextMeBot ---
# الـ API Key الخاص بك (تأكد من بقائه كما هو)
TEXTME_BOT_KEY = "CWEMDRmhtq4e" 

def send_whatsapp(phone, message):
    """دالة لإرسال الرسالة عبر واجهة TextMeBot"""
    url = "https://api.textmebot.com/send.php"
    params = {
        "recipient": phone,
        "apikey": TEXTME_BOT_KEY,
        "text": message
    }
    try:
        response = requests.get(url, params=params)
        print(f"TextMeBot Response: {response.text}")
        return response.status_code
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")
        return 500

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # استخراج نوع الحدث (نبحث عن الكلمة المفتاحية لتجنب مشاكل التسمية في قمرة)
    event = data.get('event', '').lower()
    order_data = data.get('data', {})
    
    # استخراج بيانات العميل (الاسم والهاتف)
    lead = order_data.get('salesLead', {})
    raw_phone = lead.get('phone1', '') or lead.get('phone2', '')
    phone = raw_phone.replace('+', '').strip()
    
    name = lead.get('firstName', 'عميلنا العزيز')
    order_no = order_data.get('handel', 'غير معروف')
    total = order_data.get('priceWithShipping', 0) or order_data.get('totalPriceWithTax', 0)
    status_title = order_data.get('status', {}).get('title', 'قيد المعالجة')

    # 1. حالة إنشاء طلب جديد (Welcome & Invoice)
    if "created" in event or "placed" in event:
        msg = (
            f"مرحباً {name} 👋\n"
            f"شكراً لطلبك من *محجوب أونلاين* 🛍️\n\n"
            f"📦 *تفاصيل الطلب:*\n"
            f"رقم الطلب: #{order_no}\n"
            f"الإجمالي: {total} ريال\n"
            f"الحالة: {status_title}\n\n"
            f"سيتم إشعارك فور تحديث حالة طلبك. شكراً لثقتك بنا! ✨"
        )
        send_whatsapp(phone, msg)
        
    # 2. حالة تحديث الطلب من الإدارة (Order Update)
    elif "updated" in event:
        msg = (
            f"عزيزي {name} 👋\n"
            f"تم تحديث حالة طلبك رقم #{order_no} في *سوقك الذكي*\n\n"
            f"🚚 *الحالة الجديدة:* {status_title}\n\n"
            f"نشكرك لتسوقك معنا!"
        )
        send_whatsapp(phone, msg)

    return jsonify({"status": "success", "message": "Webhook received"}), 200

# تشغيل السيرفر
if __name__ == '__main__':
    # Render يتطلب التشغيل على Port 5000 أو المنفذ الذي يحدده النظام
    app.run(host='0.0.0.0', port=5000)
