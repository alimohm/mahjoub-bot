import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
from fpdf import FPDF

app = Flask(__name__)

# الإعدادات الأساسية
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"
BASE_URL = "https://mahjoub-bot.onrender.com"

def create_invoice_pdf(order_id, customer_name, total, date_str):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="MAHJOUB ONLINE INVOICE", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Order ID: #{order_id}", ln=True)
        pdf.cell(200, 10, txt=f"Customer: {customer_name}", ln=True)
        pdf.cell(200, 10, txt=f"Total: {total} YER", ln=True)
        pdf.cell(200, 10, txt=f"Date: {date_str}", ln=True)
        file_path = f"invoice_{order_id}.pdf"
        pdf.output(file_path)
        return file_path
    except:
        return None

@app.route('/download/invoice_<order_id>.pdf')
def download_custom_invoice(order_id):
    file_name = f"invoice_{order_id}.pdf"
    if not os.path.exists(file_name):
        create_invoice_pdf(order_id, "Customer", "---", datetime.now().strftime("%Y-%m-%d"))
    return send_from_directory(os.getcwd(), file_name)

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def webhook():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    try:
        data = request.json
        order = data.get('data', {})
        customer = order.get('salesLead', {})
        order_id = order.get('handel', '0000')
        phone = str(customer.get('phone1', '')).replace('+', '').replace(' ', '')
        
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        cust_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}"
        total_p = order.get('priceWithShipping', 0)
        
        # إنشاء الفاتورة
        create_invoice_pdf(order_id, cust_name, total_p, yemen_time.strftime("%Y-%m-%d"))

        if phone:
            pdf_link = f"{BASE_URL}/download/invoice_{order_id}.pdf"
            msg = f"✨ *تم استلام طلبك بنجاح* ✨\n\n🧾 رقم الفاتورة: `{order_id}`\n👤 العميل: {cust_name}\n💵 الإجمالي: `{total_p}` ريال\n\n📄 لتحميل فاتورتك PDF:\n{pdf_link}"
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "success"}), 200
    except:
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
