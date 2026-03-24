import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- إعدادات حوكمة محجوب أونلاين ---
# الكود يقرأ المفتاح من Render تلقائياً لضمان السرية
MAHJOUB_KEY = os.environ.get("MAHJOUB_ONLINE_KEY")
GRAPHQL_URL = "https://mahjoub.online/admin/graphql"

def get_order_details(order_id):
    """جلب بيانات الطلب، الضريبة، والشحن من محجوب أونلاين"""
    query = """
    query GetOrder($id: ID!) {
      order(id: $id) {
        handel
        totalAmount
        taxAmount
        shippingAmount
        priceWithShipping
        items {
          title
          quantity
          price
        }
        salesLead {
          firstName
          lastName
          cityName
        }
      }
    }
    """
    headers = {
        "Authorization": f"Bearer {MAHJOUB_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(GRAPHQL_URL, json={'query': query, 'variables': {'id': order_id}}, headers=headers)
        return response.json().get('data', {}).get('order', {})
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    # استلام إشعار الطلب الجديد
    data = request.json
    order_id = data.get('data', {}).get('id')
    
    if order_id:
        # الربط مع النظام لجلب التفاصيل
        order_info = get_order_details(order_id)
        
        if order_info:
            # هنا النظام جاهز لإصدار الفاتورة المرتبة
            print(f"تم جلب بيانات الطلب رقم: {order_info['handel']}")
            # يمكنك هنا إضافة كود إرسال الواتساب
            
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
