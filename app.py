import os
import requests
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

ULTRAMSG_INSTANCE_ID = os.environ.get('ULTRAMSG_INSTANCE_ID')
ULTRAMSG_TOKEN = os.environ.get('ULTRAMSG_TOKEN')

@app.route('/send-invoice', methods=['POST'])
def send_invoice():
    try:
        data = request.json or {}
        logging.info(f"Received payload from Odoo: {data}")
        
        # استخراج رقم الهاتف المباشر من الحقل الجديد x_studio_phone أو أي حقل هاتف محتمل
        phone = (
            data.get('x_studio_phone') or 
            data.get('mobile') or 
            data.get('phone') 
        )
        
        # إذا قُدم رقم هاتف محدد داخل partner_id كقاموس
        if not phone and isinstance(data.get('partner_id'), dict):
            phone = data['partner_id'].get('mobile') or data['partner_id'].get('phone')

        # استخراج حالة الإنتاج/الطلب
        status = (
            data.get('x_studio_selection_field_951_1j26vhvop') or 
            data.get('Production_Status') or 
            'غير محدد'
        )
        
        order_name = data.get('name', 'الطلب')

        # تخصيص نص الرسالة بناءً على الحالة
        if status == 'في التحضير':
            message = f"مرحباً، طلبك رقم {order_name} أصبح الآن قيد التحضير!"
        elif status == 'جاهز للتوصيل':
            message = f"مرحباً، طلبك رقم {order_name} جاهز للتوصيل الآن!"
        elif status == 'تم تسليمه للتوصيل':
            message = f"مرحباً، طلبك رقم {order_name} أصبح الآن مع شركة التوصيل!"
        else:
            message = f"مرحباً، تم تحديث حالة طلبك رقم {order_name} إلى: {status}"

        if not phone:
            logging.error("No phone number found in payload.")
            return jsonify({
                "status": "error", 
                "message": "No phone number provided in payload",
                "received_data": data
            }), 400

        # تنظيف رقم الهاتف وإرساله لـ UltraMsg
        clean_phone = str(phone).strip().replace(" ", "").replace("-", "").replace("+", "")

        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
        payload = {
            "token": ULTRAMSG_TOKEN,
            "to": clean_phone,
            "body": message
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(url, data=payload, headers=headers)
        res_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
        
        logging.info(f"UltraMsg Response: {res_data}")
        return jsonify({"status": "success", "ultramsg_response": res_data}), response.status_code

    except Exception as e:
        logging.error(f"Error executing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
