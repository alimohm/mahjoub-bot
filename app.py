import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# --- إعدادات نظام محجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"

# ملاحظة: استبدل الرابط أدناه برابط تطبيقك الفعلي في Render (مثلاً mahjoub-bot.onrender.com)
BASE_URL = "https://mahjoub-bot.onrender.com" 

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

# --- 1. وظيفة تقديم الفاتورة PDF للعميل ---
# هذا المسار يسمح للرابط المرسل في الواتساب بفتح ملف الـ PDF الموجود في سيرفرك
@app.route('/download/<filename>')
def serve_invoice(filename):
    # يبحث عن الملف في المجلد الرئيسي (Root) حيث يوجد ملف test.pdf
    return send_from_directory('.', filename)

# --- 2. نظام الويب هوك (Webhook) لمعالجة الطلبات ---
@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_operations_v52_final():
    # استجابة سريعة لاختبارات السيرفر
    if request.method in ['GET', 'HEAD']: 
        return "OK", 200
    
    try:
        # استقبال بيانات الطلب من "قمرة"
        payload = smart_parse(request.get_data(as_text=True))
        order = smart_parse(payload.get('data', payload))
        customer = smart_parse(order.get('salesLead', {}))
        
        # استخراج رقم الطلب المتغير (مثلاً 1000000930)
        order_handle = str(order.get('handle') or order.get('handel') or "0000")
        
        # تنسيق رقم الهاتف (إضافة مفتاح اليمن 967)
        phone = str(customer.get('phone1') or order.get('phone', '')).replace('+', '').replace(' ', '')
        if phone and not phone.startswith('967'): 
            phone = '967' + phone

        # --- الروابط المرسلة للعميل ---
        # رابط تتبع الحالة (نظام قمرة)
        tracking_link = f"https://mahjoub.online/customer/thank-you/{order_handle}"
        
        # رابط تحميل الفاتورة المباشر (سيرفر Render الخاص بك)
        invoice_link = f"{BASE_URL}/download/test.pdf"

        # توقيت اليمن المحلي (GMT+3)
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p")

        # تنسيق الرسالة الملكي
        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        msg = (
            "✨ *إشعار نظام: تم استلام طلبكم بنجاح* ✨\n\n"
            f"🧾 *فاتورة رقم:* `{order_handle}`\n"
            f"{divider}\n"
            f"👤 *العميل:* {customer.get('firstName', '')} {customer.get('lastName', '')}\n"
            f"💵 *الإجمالي النهائي:* `{order.get('priceWithShipping', 0)}` ريال\n"
            f"{divider}\n"
            f"🔗 *رابط تتبع حالة الشحن:* \n{tracking_link}\n\n"
            f"📄 *رابط تحميل فاتورة PDF المباشر:* \n{invoice_link}\n\n"
            f"🕒 `{full_time}`\n\n"
            f"{footer}"
        )

        # الإرسال عبر API TextMeBot
        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        # العودة بحالة نجاح حتى لا يكرر نظام قمرة الإرسال عند الخطأ البسيط
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    # البورت 10000 هو بورت Render الافتراضي
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
