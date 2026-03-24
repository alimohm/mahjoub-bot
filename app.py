import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# --- إعدادات المحرك الذكي لمحجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"
BASE_URL = "https://mahjoub-bot.onrender.com"

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

@app.route('/download/<filename>')
def serve_invoice(filename):
    # سيقدم الملف الثابت حالياً، ويمكنك لاحقاً ربطه بنظام توليد تلقائي
    return send_from_directory('.', filename)

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_dynamic_engine():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    
    try:
        # 1. سحب البيانات الخام من منصة قمرة
        payload = smart_parse(request.get_data(as_text=True))
        order = smart_parse(payload.get('data', payload))
        customer = smart_parse(order.get('salesLead', order.get('customer', {})))
        
        # 2. استخراج المعلومات الأساسية (المتغيرة لكل عميل)
        order_handle = str(order.get('handle') or "0000")
        cust_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip() or "عميلنا العزيز"
        address = f"{customer.get('cityName', 'اليمن')} - {customer.get('district', 'الشارع')}"
        
        # 3. تفاصيل المنتجات والأسعار (ديناميكية)
        items = order.get('items', [])
        product_details = ""
        total_qty = 0
        for item in items:
            name = item.get('product_name', 'منتج')
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            product_details += f"📦 *{name}* (×{qty}) - `{price}` ريال\n"
            total_qty += int(qty)

        tax = order.get('taxAmount', 0)
        final_total = order.get('total', order.get('priceWithShipping', 0))
        
        # 4. الحالة والوقت
        status = order.get('status_name') or "قيد الإنتظار"
        is_paid = order.get('isPaid', False)
        pay_status = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        time_str = yemen_time.strftime("%Y/%m/%d - %I:%M %p")

        # 5. بناء الرسالة بنفس التنسيق الذي طلبته تماماً
        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        msg = (
            "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
            f"🧾 *فاتورة طلب رقم:* `{order_handle}`\n"
            f"{divider}\n"
            f"👤 *العميل:* {cust_name}\n"
            f"📍 *موقع التوصيل:* {address}\n"
            f"{divider}\n"
            f"{product_details}"
            f"🔢 *عدد المنتجات:* {total_qty}\n"
            f"💰 *الضريبة:* `{tax}` ريال\n"
            f"💵 *الإجمالي النهائي:* `{final_total}` ريال\n"
            f"{divider}\n"
            f"🚚 *حالة المنتج:* 【 {status} 】\n"
            f"📝 *حالة الدفع:* {pay_status}\n"
            "⚠️ *يرجى تزويدنا بصورة القسيمة المالية (إيصال السداد) هنا لمتابعة تنفيذ طلبكم.*"
            f"\n{divider}\n"
            f"🕒 *توقيت الطلب:* `{time_str}`\n"
            f"🔗 *رابط التتبع:* https://mahjoub.online/customer/thank-you/{order_handle}\n\n"
            "📦 *مرفق أدناه فاتورة PDF إلكترونية لطلبكم:*\n"
            f"{BASE_URL}/download/test.pdf\n\n" # رابط الفاتورة من سيرفرك
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "*نظام محجوب أونلاين | سوقك الذكي*"
        )

        # 6. الإرسال للعميل
        phone = str(customer.get('phone1') or order.get('phone', '')).replace('+', '').replace(' ', '')
        if phone and not phone.startswith('967'): phone = '967' + phone

        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
