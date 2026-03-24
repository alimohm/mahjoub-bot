import os
from flask import Flask, request, jsonify
import requests
import urllib.parse
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# --- إعدادات الحوكمة: MAHJOUB_ONLINE_CORE_OPERATIONS ---
# تأكد من تسمية المفتاح في Render بهذا الاسم: MAHJOUB_ONLINE_KEY
MAHJOUB_API_KEY = os.environ.get("MAHJOUB_ONLINE_KEY") 
TEXTMEBOT_API_KEY = os.environ.get("TEXTMEBOT_KEY", "CWEMDRmhtq4e")
GRAPHQL_URL = "https://mahjoub.online/admin/graphql"

def fetch_core_operations_data(order_id):
    """الاستعلام المركزي لنظام MAHJOUB_ONLINE_CORE_OPERATIONS"""
    query = """
    query GetOrder($id: ID!) {
      order(id: $id) {
        handel
        taxAmount
        shippingAmount
        priceWithShipping
        items { title quantity }
        salesLead { firstName lastName phone1 cityName }
      }
    }
    """
    headers = {
        "Authorization": f"Bearer {MAHJOUB_API_KEY}",
        "Content-Type": "application/json",
        "X-System-Source": "MAHJOUB_ONLINE_CORE_OPERATIONS"
    }
    try:
        response = requests.post(GRAPHQL_URL, json={'query': query, 'variables': {'id': order_id}}, headers=headers, timeout=12)
        return response.json().get('data', {}).get('order', {})
    except:
        return None

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def core_operations_webhook():
    if request.method in ['GET', 'HEAD']: return "MAHJOUB_CORE_ACTIVE", 200
    try:
        payload = request.get_json()
        event = payload.get('event', 'order.updated')
        order_internal_id = payload.get('data', {}).get('id')

        # جلب البيانات عبر محرك العمليات المركزي
        order = fetch_core_operations_data(order_internal_id)
        if not order: return jsonify({"status": "auth_or_data_error"}), 200

        customer = order.get('salesLead', {})
        phone = str(customer.get('phone1', '')).replace('+', '').replace(' ', '')
        
        # ضبط التوقيت (اليمن GMT+3)
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        time_str = yemen_time.strftime("%Y/%m/%d - %I:%M %p")
        
        # تجهيز قائمة المنتجات
        items_text = "\n".join([f"• {item['title']} (x{item['quantity']})" for item in order.get('items', [])])

        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | إدارة العمليات المركزية*"

        # نص الرسالة الرسمي
        msg = (
            f"🔄 *إشعار من MAHJOUB_ONLINE_CORE*\n\n"
            f"🧾 *رقم الطلب:* `{order.get('handel')}`\n"
            f"{divider}\n"
            f"👤 *العميل:* {customer.get('firstName', '')} {customer.get('lastName', '')}\n"
            f"📍 *المدينة:* {customer.get('cityName', 'اليمن')}\n"
            f"{divider}\n"
            f"📦 *المحتويات:*\n{items_text}\n"
            f"{divider}\n"
            f"💰 *الضريبة:* `{order.get('taxAmount', 0)}` ر.ي\n"
            f"🚚 *الشحن:* `{order.get('shippingAmount', 0)}` ر.ي\n"
            f"💵 *الإجمالي:* *{order.get('priceWithShipping', 0)} ريال*\n"
            f"{divider}\n"
            f"🕒 *الوقت:* `{time_str}`\n\n"
            f"{footer}"
        )

        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "core_success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
