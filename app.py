import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
import json

app = Flask(__name__)

# --- إعدادات محجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"
BASE_URL = "https://mahjoub-bot.onrender.com" 

# وظيفة تقديم الملفات (تأكد أن المسار صحيح)
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(os.getcwd(), filename, as_attachment=True)

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def webhook_handler():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    
    try:
        data = request.json
        order = data.get('data', data)
        customer = order.get('salesLead', {})
        phone = str(customer.get('phone1', '')).replace('+', '').replace(' ', '')
        
        if phone:
            # 1. إرسال رسالة نصية لتأكيد الاتصال
            msg = "✅ تم استلام طلبك من محجوب أونلاين. جاري إرسال الفاتورة PDF..."
            requests.get(f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}")

            # 2. إرسال الملف
            # نستخدم رابطاً مباشراً وقوياً
            pdf_name = "test.pdf" 
            file_url = f"{BASE_URL}/download/{pdf_name}"
            
            # الرابط الخاص بإرسال الملفات في TextMeBot
            whatsapp_file_api = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&document={urllib.parse.quote(file_url)}"
            
            # تنفيذ الطلب ومراقبة النتيجة
            res = requests.get(whatsapp_file_api, timeout=15)
            print(f"TextMeBot Response: {res.text}") # سيظهر لك في سجلات Render سبب الفشل إن وجد

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
