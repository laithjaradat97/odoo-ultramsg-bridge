import os
import requests
import logging
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route('/send-invoice', methods=['POST'])
def send_invoice():
    try:
        # قراءة وتنظيف متناغم لمتغيرات البيئة لحذف أي مسافات مخفية
        ULTRAMSG_INSTANCE_ID = (os.environ.get('ULTRAMSG_INSTANCE_ID') or '').strip()
        ULTRAMSG_TOKEN = (os.environ.get('ULTRAMSG_TOKEN') or '').strip()

        data = request.json or {}
        logging.info(f"Received payload from Odoo: {data}")
        
        # استخراج رقم الهاتف المباشر
        phone_raw = (
            data.get('x_studio_phone') or 
            data.get('mobile') or 
            data.get('phone') or 
            data.get('x_studio_customer_phone')
        )
        
        if not phone_raw and isinstance(data.get('partner_id'), dict):
            phone_raw = data['partner_id'].get('mobile') or data['partner_id'].get('phone')

        # استخراج حالة الإنتاج/الطلب
        status = (
            data.get('x_studio_selection_field_951_1j26vhvop') or 
            data.get('Production_Status') or 
            'غير محدد'
        )
        
        order_name = data.get('name', 'الطلب')

        # نص الرسالة حسب الحالة
        if status == 'في التحضير':
            message = f"مرحباً، طلبك رقم {order_name} قيد التحضير!"
        elif status == 'جاهز للتوصيل':
            message = f"مرحباً، طلبك رقم {order_name} جاهز للتوصيل أو الاستلام من المعرض الآن!"
        elif status == 'تم تسليمه للتوصيل':
            message = f"مرحباً، طلبك رقم {order_name} أصبح الآن مع شركة التوصيل!"
        else:
            message = f"مرحباً، تم تحديث حالة طلبك رقم {order_name} إلى: {status}"

        if not phone_raw:
            logging.error("No phone number found in payload.")
            return jsonify({
                "status": "error", 
                "message": "No phone number provided in payload",
                "received_data": data
            }), 400

        # تنظيف رقم الهاتف بانتظام لإبقاء الأرقام فقط بدون + أو مسافات
        clean_phone = re.sub(r'\D', '', str(phone_raw))

        # إرسال الطلب لـ UltraMsg
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
        payload = {
            "token": ULTRAMSG_TOKEN,
            "to": clean_phone,
            "body": message
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
        logging.info(f"Sending to UltraMsg URL: {url} with phone: {clean_phone}")
        
        response = requests.post(url, data=payload, headers=headers)
        
        try:
            res_data = response.json()
        except Exception:
            res_data = response.text

        logging.info(f"UltraMsg Response: {res_data}")
        return jsonify({"status": "success", "ultramsg_response": res_data}), response.status_code

    except Exception as e:
        logging.error(f"Error executing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
