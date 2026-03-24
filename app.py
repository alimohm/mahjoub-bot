import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from fpdf import FPDF
from datetime import datetime, timedelta

app = Flask(__name__)

# إعدادات محجوب أونلاين
API_KEY = "CWEMDRmhtq4e"
BASE_URL = "https://mahjoub-bot.onrender.com"

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(75, 0, 130) # بنفسجي ملكي
        self.cell(0, 10, 'MAHJOUB ONLINE', ln=True, align='C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Your Smart Market - Official Invoice', ln=True, align='C')
        self.ln(10)

def create_invoice(order_id, customer_name, phone, city, product_name, total):
    pdf = PDF()
    pdf.add_page()
    
    # معلومات الفاتورة
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Order ID: {order_id}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(5)
    
    # بيانات العميل
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "Customer Information", ln=True, fill=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 10, f"Name: {customer_name}", ln=True)
    pdf.cell(0, 10, f"Phone: {phone}", ln=True)
    pdf.cell(0, 10, f"Location: {city}", ln=True)
    pdf.ln(10)
    
    # تفاصيل المنتج
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(75, 0, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 10, "Product", 1, 0, 'C', True)
    pdf.cell(90, 10, "Total Price", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(100, 10, "Traditional Maawiz", 1) # يمكنك جعلها متغيرة لاحقاً
    pdf.cell(90, 10, f"{total} SAR", 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Total Amount: {total} SAR", ln=True, align='R')

    file_path = f"invoice_{order_id}.pdf"
    pdf.output(file_path)
    return file_path

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(os.getcwd(), filename)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        order = data.get('data', {})
        customer = order.get('salesLead', {})
        
        order_id = order.get('handel', '0000')
        first_name = customer.get('firstName', 'Customer')
        last_name = customer.get('lastName', '')
        full_name = f"{first_name} {last_name}"
        phone = str(customer.get('phone1', '')).replace('+', '').strip()
        city = customer.get('city', 'Yemen')
        total_price = order.get('totalPrice', 0)

        if phone:
            # 1. إنشاء الفاتورة الحقيقية بالبيانات
            invoice_file = create_invoice(order_id, full_name, phone, city, "Product", total_price)
            
            # 2. إرسال النص الكامل
            msg = f"✨ *محجوب أونلاين*\n\nعزيزي {first_name}، تم تأكيد طلبك رقم {order_id} بنجاح.\n\nتجد مرفقاً فاتورة الدفع الرسمية الخاصة بك بصيغة PDF.\nشكراً لاختيارك لنا!"
            requests.get(f"https://api.textmebot.com/send.php?recipient={phone}&apikey={API_KEY}&text={urllib.parse.quote(msg)}")
            
            # 3. إرسال ملف الـ PDF الحقيقي
            file_link = f"{BASE_URL}/download/{invoice_file}"
            requests.get(f"https://api.textmebot.com/send.php?recipient={phone}&apikey={API_KEY}&document={urllib.parse.quote(file_link)}")
            
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
