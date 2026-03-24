import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
from fpdf import FPDF

app = Flask(__name__)

# إعدادات الروابط
BASE_URL = "https://mahjoub-bot.onrender.com"
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"

class InvoicePDF(FPDF):
    def header(self):
        # إضافة شعار محجوب أونلاين (يجب أن يكون الملف موجوداً في السيرفر)
        # self.image('logo.png', 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.set_text_color(75, 0, 130) # البنفسجي الملكي
        self.cell(0, 10, 'MAHJOUB ONLINE', ln=True, align='C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Your Smart Market - Luxury Choice', ln=True, align='C')
        self.ln(10)

def generate_invoice(order_id, customer_info, product_info, totals):
    pdf = InvoicePDF()
    pdf.add_page()
    
    # قسم بيانات العميل والإيداع (مربعات ملونة كما في تصميمك)
    pdf.set_fill_color(252, 250, 255)
    pdf.rect(10, 40, 90, 40, 'F') # مربع بيانات العميل
    pdf.rect(110, 40, 90, 40, 'F') # مربع بيانات الإيداع
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_xy(10, 42)
    pdf.cell(90, 10, f"Customer: {customer_info['name']}", ln=False)
    pdf.set_xy(110, 42)
    pdf.cell(90, 10, f"Deposit: Ahmed Al-Haddad", ln=True)
    
    # جدول المنتجات
    pdf.ln(30)
    pdf.set_fill_color(75, 0, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 10, 'Product', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Qty', 1, 0, 'C', True)
    pdf.cell(60, 10, 'Total', 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 10, product_info['name'], 1)
    pdf.cell(30, 10, str(product_info['qty']), 1, 0, 'C')
    pdf.cell(60, 10, f"{product_info['price']} SAR", 1, 1, 'C')
    
    # الإجمالي النهائي باللون الذهبي/البنفسجي
    pdf.ln(10)
    pdf.set_fill_color(15, 0, 26)
    pdf.set_text_color(212, 175, 55) # لون ذهبي
    pdf.cell(190, 15, f"GRAND TOTAL: {totals['grand_total']} SAR", 0, 1, 'C', True)

    filename = f"invoice_{order_id}.pdf"
    pdf.output(filename)
    return filename

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    order = data.get('data', {})
    customer = order.get('salesLead', {})
    
    order_id = order.get('handel', '0000')
    phone = str(customer.get('phone1', '')).replace('+', '')
    
    # استخراج البيانات للفاتورة
    customer_info = {'name': f"{customer.get('firstName', '')} {customer.get('lastName', '')}"}
    product_info = {'name': 'Traditional Maawiz', 'qty': 1, 'price': order.get('totalPrice', 0)}
    totals = {'grand_total': order.get('totalPrice', 0)}

    # 1. إنشاء الفاتورة فوراً
    pdf_filename = generate_invoice(order_id, customer_info, product_info, totals)
    
    # 2. إرسال ملف الـ PDF للواتساب
    pdf_url = f"{BASE_URL}/download/{pdf_filename}"
    whatsapp_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&document={urllib.parse.quote(pdf_url)}"
    
    # إرسال الطلب في الخلفية لتجنب الـ Timeout في قمرة
    try:
        requests.get(whatsapp_url, timeout=5)
    except:
        pass

    return jsonify({"status": "success"}), 200

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(os.getcwd(), filename)
