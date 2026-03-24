import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
from fpdf import FPDF

app = Flask(__name__)

# --- الإعدادات الملكية لمحجوب أونلاين ---
ACCESS_TOKEN = "ضع_هنا_التوكن_الذي_ظهر_في_الصورة_السابقة"
GRAPHQL_URL = "https://api.qumra.sa/graphql" # أو الرابط الخاص بمتجرك
BASE_URL = "https://mahjoub-bot.onrender.com"

def get_order_details_from_api(order_id):
    query = """
    query GetOrder($id: ID!) {
      order(id: $id) {
        handel
        priceWithShipping
        totalAmount
        taxAmount
        shippingAmount
        items { title quantity price }
        salesLead { firstName lastName cityName district }
      }
    }
    """
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    response = requests.post(GRAPHQL_URL, json={'query': query, 'variables': {'id': order_id}}, headers=headers)
    return response.json().get('data', {}).get('order', {})

def create_detailed_pdf(order_data):
    order_id = order_data.get('handel', '0000')
    pdf = FPDF()
    pdf.add_page()
    
    # تنسيق الرأس (Header)
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(75, 0, 130) # اللون الأرجواني الملكي
    pdf.cell(200, 15, txt="MAHJOUB ONLINE", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt="Official Purchase Invoice", ln=True, align='C')
    pdf.ln(10)

    # جدول المنتجات
    pdf.set_fill_color(75, 0, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 10, " Product", 1, 0, 'C', True)
    pdf.cell(30, 10, "Qty", 1, 0, 'C', True)
    pdf.cell(35, 10, "Unit Price", 1, 0, 'C', True)
    pdf.cell(35, 10, "Total", 1, 1, 'C', True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 10)
    for item in order_data.get('items', []):
        pdf.cell(90, 10, f" {item['title'][:30]}", 1)
        pdf.cell(30, 10, str(item['quantity']), 1, 0, 'C')
        pdf.cell(35, 10, f"{item['price']}", 1, 0, 'C')
        pdf.cell(35, 10, f"{item['price'] * item['quantity']}", 1, 1, 'C')

    # ملخص الحساب (الضريبة والشحن والإجمالي)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(155, 8, "Subtotal:", 0, 0, 'R')
    pdf.cell(35, 8, f"{order_data.get('totalAmount', 0)} YER", 1, 1, 'C')
    pdf.cell(155, 8, "Tax Amount:", 0, 0, 'R')
    pdf.cell(35, 8, f"{order_data.get('taxAmount', 0)} YER", 1, 1, 'C')
    pdf.cell(155, 8, "Shipping:", 0, 0, 'R')
    pdf.cell(35, 8, f"{order_data.get('shippingAmount', 0)} YER", 1, 1, 'C')
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(155, 10, "GRAND TOTAL:", 0, 0, 'R')
    pdf.cell(35, 10, f"{order_data.get('priceWithShipping', 0)} YER", 1, 1, 'C', True)

    file_name = f"invoice_{order_id}.pdf"
    pdf.output(file_name)
    return file_name

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json
    # استخراج الـ ID الحقيقي للطلب من الـ Webhook لاستخدامه في الـ API
    raw_order_id = payload.get('data', {}).get('id') 
    
    # جلب البيانات المرتبة من Apollo/GraphQL
    full_data = get_order_details_from_api(raw_order_id)
    
    # صنع الفاتورة الـ PDF
    create_detailed_pdf(full_data)
    
    # إرسال الواتساب (بنفس الكود السابق)
    # ...
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
