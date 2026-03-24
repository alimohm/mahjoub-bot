import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# --- إعدادات الربط المباشر لمتجر محجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"
# المفتاح الذي وفرته أنت في الصور (image_1aee82.png)
QOMRA_API_TOKEN = "qmr_076ddc4c4cc944ce8830495f32a79291"
GRAPHQL_URL = "https://mahjoub.online/admin/graphql"
BASE_URL = "https://mahjoub-bot.onrender.com"

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

def fetch_real_order_data(order_id):
    """الاستعلام المباشر لسحب الأسماء المتغيرة والإجمالي الحقيقي"""
    query = """
    query {
      node(id: "%s") {
        ... on Order {
          handle
          total
          taxAmount
          items {
            product_name
            quantity
            price
          }
        }
      }
    }
    """ % order_id
    headers = {"Authorization": f"Bearer {QOMRA_API_TOKEN}", "Content-Type": "application/json"}
    try:
        response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers, timeout=12)
        return response.json().get('data', {}).get('node', {})
    except:
        return {}

@app.route('/download/<filename>')
def serve_invoice(filename):
    return send_from_directory('.', filename)

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_ultimate_v58():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    
    try:
        payload = smart_parse(request.get_data(as_text=True))
        order_webhook = smart_parse(payload.get('data', payload))
        raw_id = order_webhook.get('id') # المعرف الداخلي للاستعلام

        # 1. جلب البيانات "الحية" والأسماء المتغيرة من الـ API
        api_data = fetch_real_order_data(raw_id)
        
        # 2. تحديد البيانات النهائية (الأولوية للـ API ثم الويب هوك كبديل)
        order_handle = api_data.get('handle') or order_webhook.get('handle') or "0000"
        final_total = api_data.get('total') or order_webhook.get('total') or 0
        tax = api_data.get('taxAmount') or order_webhook.get('taxAmount') or 0
        
        # 3. بناء قائمة المنتجات المتغيرة
        items = api_data.get('items') or order_webhook.get('items', [])
        product_summary = ""
        total_qty = 0
        for item in items:
            p_name = item.get('product_name') or "منتج متوفر"
            p_qty = int(item.get('quantity', 1))
            product_summary += f"📦 *{p_name}* (×{p_qty}) - `{item.get('price', 0)}` ريال\n"
            total_qty += p_qty

        # 4. بيانات العميل والموقع
        customer = smart_parse(order_webhook.get('salesLead', order_webhook.get('customer', {})))
        cust_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip() or "عميلنا العزيز"
        country = customer.get('countryName') or "اليمن"
        city = customer.get('cityName') or "الخوخة"
        full_address = f"{country} - {city}"

        # توقيت اليمن GMT+3
        y_time = datetime.utcnow() + timedelta(hours=3)
        time_display = y_time.strftime("%Y/%m/%d - %I:%M %p")

        # 5. بناء الرسالة الملكية
        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        msg = (
            "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
            f"🧾 *فاتورة طلب رقم:* `{order_handle}`\n"
            f"{divider}\n"
            f"👤 *العميل:* {cust_name}\n"
            f"📍 *موقع التوصيل:* {full_address}\n"
            f"{divider}\n"
            f"{product_summary}"
            f"🔢 *عدد المنتجات:* {total_qty}\n"
            f"💰 *الضريبة:* `{tax}` ريال\n"
            f"💵 *الإجمالي النهائي:* `{final_total}` ريال\n"
            f"{divider}\n"
            f"🚚 *حالة المنتج:* 【 قيد الإنتظار 】\n"
            f"📝 *حالة الدفع:* ❌ *غير مدفوع*\n"
            "⚠️ *يرجى تزويدنا بصورة القسيمة المالية (إيصال السداد) هنا لمتابعة تنفيذ طلبكم.*"
            f"\n{divider}\n"
            f"🕒 *توقيت الطلب:* `{time_display}`\n"
            f"🔗 *رابط التتبع:* https://mahjoub.online/customer/thank-you/{order_handle}\n\n"
            "📦 *مرفق أدناه فاتورة PDF إلكترونية لطلبكم:*\n"
            f"{BASE_URL}/download/test.pdf\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "*نظام محجوب أونلاين | سوقك الذكي*"
        )

        # 6. إرسال الواتساب
        phone = str(customer.get('phone1') or order_webhook.get('phone', '')).replace('+', '').replace(' ', '')
        if phone and not phone.startswith('967'): phone = '967' + phone

        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
