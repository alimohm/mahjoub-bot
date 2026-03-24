import os
from flask import Flask, request, jsonify
import requests
import urllib.parse
from datetime import datetime, timedelta

app = Flask(__name__)

# --- إعدادات نظام العمليات المركزية (الأحرف الصغيرة) ---
# تأكد أن الأسماء في Render مطابقة تماماً لهذه الكلمات
MAHJOUB_KEY = os.environ.get("MAHJOUB_ONLINE_KEY")
TEXTMEBOT_KEY = os.environ.get("TEXTMEBOT_KEY")
GRAPHQL_URL = "https://mahjoub.online/admin/graphql"

def get_order_data(order_id):
    """سحب بيانات الفاتورة من محرك قمرة"""
    query = """
    query GetOrder($id: ID!) {
      order(id: $id) {
        handel
        priceWithShipping
        salesLead { firstName phone1 }
      }
    }
    """
    headers = {
        "Authorization": f"Bearer {MAHJOUB_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(GRAPHQL_URL, json={'query': query, 'variables': {'id': order_id}}, headers=headers, timeout=12)
        return response.json().get('data', {}).get('order', {})
    except:
        return None

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_core_webhook():
    if request.method in ['GET', 'HEAD']: return "CORE_OPERATIONS_ACTIVE", 200
    
    try:
        payload = request.get_json()
        order_internal_id = payload.get('data', {}).get('id')
        
        # تنفيذ السحب الذكي
        order = get_order_data(order_internal_id)
        
        if order:
            customer_name = order['salesLead']['firstName']
            # تنظيف رقم الهاتف لضمان الإرسال
            phone = str(order['salesLead']['phone1']).replace('+', '').replace(' ', '')
            order_no = order['handel']
            total = order['priceWithShipping']
            
            # نص الرسالة الرسمي
            msg = f"مرحباً {customer_name}، تم تحديث طلبك رقم {order_no} في محجوب أونلاين. الإجمالي: {total} ريال. شكراً لثقتكم."
            
            # محرك إرسال واتساب
            if phone and len(phone) > 5:
                api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_KEY}&text={urllib.parse.quote(msg)}"
                requests.get(api_url, timeout=10)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    # بورت 10000 هو الافتراضي لـ Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
