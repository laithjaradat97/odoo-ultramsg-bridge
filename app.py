import os
import requests
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

# إعداد السجلات لمعرفة البيانات القادمة بالضبط
logging.basicConfig(level=logging.INFO)

ULTRAMSG_INSTANCE_ID = os.environ.get('ULTRAMSG_INSTANCE_ID')
ULTRAMSG_TOKEN = os.environ.get('ULTRAMSG_TOKEN')

@app.route('/send-invoice', methods=['POST'])
def send_invoice():
    try:
        data = request.json or {}
        logging.info(f"Received payload from Odoo: {data}")
        
        # استخراج الهاتف بطريقة آمنة
        phone = None
        if isinstance(data.get('partner_id'), dict):
            phone = data['partner_id'].get('mobile') or data['partner_id'].get('phone')
        
        if not phone:
            phone = data.get('mobile') or data.get('phone') or data.get('x_studio_phone') or data.get('partner_phone')

        # استخراج حالة الطلب بطريقة آمنة
        status = (
            data.get('Production_Status') or 
            data.get('x_studio_selection_field_951_1j26vhvop') or 
            'غير محدد'
        )
        
        order_name = data.get('name', 'الطلب')

        # تخصيص نص الرسالة حسب الحالة
        if status == 'في التحضير':
            message = f"مرحباً، طلبك رقم {order_name} أصبح الآن قيد التحضير!"
        elif status == 'جاهز للتوصيل':
            message = f"مرحباً، طلبك رقم {order_name} جاهز للتوصيل الآن!"
        elif status == 'تم تسليمه للتوصيل':
            message = f"مرحباً، طلبك رقم {order_name} أصبح الآن مع شركة التوصيل!"
        else:
            message = f"مرحباً، تم تحديث حالة طلبك رقم {order_name} إلى: {status}"

        if not phone:
            logging.error("No phone number found in data.")
            return jsonify({
                "status": "error", 
                "message": "No phone number provided in payload",
                "received_data": data
            }), 400

        # تجهيز وإرسال الطلب لـ UltraMsg
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
        payload = {
            "token": ULTRAMSG_TOKEN,
            "to": str(phone).strip(),
            "body": message
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(url, data=payload, headers=headers)
        res_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
        
        logging.info(f"UltraMsg Response: {res_data}")
        return jsonify({"status": "success", "ultramsg_response": res_data}), response.status_code

    except Exception as e:
        logging.error(f"Error executing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 200 # إرجاع 200 لتفادي كسر الـ Webhook

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
