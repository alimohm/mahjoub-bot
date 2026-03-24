import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import re
from fpdf import FPDF

app = Flask(__name__)

# --- إعدادات محجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"
BASE_URL = "https://mahjoub-bot.onrender.com"

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

def get_real_text(val):
    txt = str(val).strip()
    if not txt or txt.lower() in ['none', 'null', '', 'false']: return None
    if len(txt) >= 20 and re.match(r'^[a-f0-9]+$', txt): return None
    return txt

# --- دالة صناعة قالب الفاتورة PDF برمجياً برقم طلب محدد ---
def create_invoice_pdf(order_id, customer_name, total, date_str):
    pdf = FPDF()
    pdf.add_page()
    
    # إعداد الخط والعنوان
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 15, txt="MAHJOUB ONLINE", ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="OFFICIAL INVOICE", ln=True, align='C')
    pdf.ln(10)
    
    # معلومات العميل والطلب
    pdf.set_font("Arial", '', 12)
    pdf.cell(100, 10, txt=f"Order ID: #{order_id}", ln=False)
    pdf.cell(100, 10, txt=f"Date: {date_str}", ln=True, align='R')
    pdf.cell(200, 10, txt=f"Customer Name: {customer_name}", ln=True)
    pdf.ln(5)
    
    # جدول الفاتورة
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, txt="Description", border=1, fill=True)
    pdf.cell(50, 10, txt="Total Amount", border=1, ln=True, fill=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(140, 15, txt=f"Purchases from Mahjoub Online Store", border=1)
    pdf.cell(50, 15, txt=f"{total} YER", border=1, ln=True, align='C')
    
    # التذييل
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Thank you for choosing our store!", ln=True, align='C')
    pdf.cell(200, 10, txt="Mahjoub Online | Your Smart Market", ln=True, align='C')
    
    # اسم الملف فريد لكل طلب لمنع التداخل
    file_path = f"invoice_{order_id}.pdf"
    pdf.output(file_path)
    return file_path

# --- رابط تحميل الفاتورة المتغير (يستقبل رقم الطلب من الرابط) ---
@app.route('/download/invoice_<order_id>.pdf')
def download_custom_invoice(order_id):
    # السيرفر يبحث عن الملف، إذا لم يكن موجوداً (بسبب إعادة تشغيل السيرفر مثلاً) يقوم بإنشاء واحد افتراضي
    file_name = f"invoice_{order_id}.pdf"
    if not os.path.exists(file_name):
        create_invoice_pdf(order_id, "Valued Customer", "---", datetime.now().strftime("%Y-%m-%d"))
    
    return send_from_directory(os.getcwd(), file_name)

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_auto_receipt_v38():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    try:
        raw_data = request.get_data(as_text=True)
        payload = smart_parse(raw_data)
        order = smart_parse(payload.get('data', payload))
        customer = smart_parse(order.get('salesLead', {}))
        
        event = payload.get('event', 'order.created')
        order_id = order.get('handel', '0000')
        phone = str(customer.get('phone1', '')).replace('+', '').replace(' ', '')
        tracking_link = f"https://mahjoub.online/customer/thank-you/{order_id}"
        
        # التوقيت اليمني
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p") 
        
        status_info = smart_parse(order.get('status', {}))
        status_title = status_info.get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"

        # إنشاء الفاتورة فور استلام الطلب وتخزينها باسم فريد
        customer_full_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}"
        total_price = order.get('priceWithShipping', 0)
        create_invoice_pdf(order_id, customer_full_name, total_price, yemen_time.strftime("%Y-%m-%d"))

        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        if event == "order.created":
            city = get_real_text(customer.get('cityName')) or "اليمن"
            # الرابط الآن يحتوي على رقم الطلب الفريد لكل عميل
            pdf_link = f"{BASE_URL}/download/invoice_{order_id}.pdf"
            
            msg = (
                "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
                f"🧾 *فاتورة رقم:* `{order_id}`\n"
                f"{divider}\n"
                f"👤 *العميل:* {customer_full_name}\n"
                f"📍 *الموقع:* {city}\n"
                f"{divider}\n"
                f"💵 *الإجمالي النهائي:* `{total_price}` ريال\n"
                f"{divider}\n"
                f"🚚 *الحالة:* 【 {status_title} 】\n"
                f"📝 *الدفع:* {pay_text}\n"
                f"{divider}\n"
                f"🕒 *توقيت الطلب:* `{full_time}`\n"
                f"📄 *تحميل فاتورتك الخاصة PDF:*\n{pdf_link}\n\n"
                f"{footer}"
            )
        else:
            msg = (
                "🔄 *إشعار نظام: تحديث الطلب*\n"
                f"{divider}\n"
                f"📦 *رقم المنتج:* `{order_id}`\n"
                f"🚚 *الحالة:* 【 {status_title} 】\n"
                f"📝 *الدفع:* {pay_text}\n"
                f"{divider}\n"
                f"🕒 *وقت التحديث:* `{full_time}`\n"
                f"🔗 *تتبع:* {tracking_link}\n\n"
                f"{footer}"
            )

        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
