import os
from flask import Flask, request, jsonify
import requests
import urllib.parse

app = Flask(__name__)

# جلب المفاتيح من Render
MAHJOUB_KEY = os.environ.get("MAHJOUB_ONLINE_KEY")
TEXTMEBOT_KEY = os.environ.get("TEXTMEBOT_KEY")
GRAPHQL_URL = "https://mahjoub.online/admin/graphql"

def get_order_data(order_id):
    query = """
    query GetOrder($id: ID!) {
      order(id: $id) {
        handle
        priceWithShipping
        salesLead { firstName phone1 }
      }
    }
    """
    headers = {"Authorization": f"Bearer {MAHJOUB_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(GRAPHQL_URL, json={'query': query, 'variables': {'id': order_id}}, headers=headers, timeout=12)
        return response.json().get('data', {}).get('order', {})
    except:
        return None

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_core_webhook():
    # هذا السطر يمنع الـ 404 عند الفحص البسيط
    if request.method in ['GET', 'HEAD']: return "SYSTEM_ACTIVE", 200
    
    try:
        payload = request.get_json()
        # سحب الـ ID من البيانات التي أرسلتها في الـ Payload
        order_internal_id = payload.get('data', {}).get('_id') 
        
        order = get_order_data(order_internal_id)
        
        if order and order.get('salesLead'):
            customer_name = order['salesLead']['firstName']
            phone = str(order['salesLead']['phone1']).replace('+', '').replace(' ', '')
            order_no = order['handle']
            total = order['priceWithShipping']
            
            msg = f"مرحباً {customer_name}، تم تحديث طلبك رقم {order_no} في محجوب أونلاين. الإجمالي: {total} ريال. شكراً لثقتكم."
            
            if phone and len(phone) > 5:
                api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_KEY}&text={urllib.parse.quote(msg)}"
                requests.get(api_url, timeout=10)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
