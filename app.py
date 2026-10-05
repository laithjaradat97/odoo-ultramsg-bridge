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
        ULTRAMSG_INSTANCE_ID = (os.environ.get('ULTRAMSG_INSTANCE_ID') or '').strip()
        ULTRAMSG_TOKEN = (os.environ.get('ULTRAMSG_TOKEN') or '').strip()

        data = request.json or {}
        logging.info(f"Received payload from Odoo: {data}")
        
        # استخراج رقم الهاتف
        phone_raw = (
            data.get('x_studio_phone') or 
            data.get('mobile') or 
            data.get('phone') or 
            data.get('x_studio_customer_phone')
        )
        
        if not phone_raw and isinstance(data.get('partner_id'), dict):
            phone_raw = data['partner_id'].get('mobile') or data['partner_id'].get('phone')

        # استخراج حالة الطلب
        status = (
            data.get('x_studio_selection_field_951_1j26vhvop') or 
            data.get('Production_Status') or 
            'غير محدد'
        )
        
        order_name = data.get('name', 'الطلب')

        # 1. نص الرسالة الرئيسي حسب الحالة
        if status == 'في التحضير':
            body_text = f"مرحباً، طلبك رقم {order_name} قيد التحضير!"
        elif status == 'جاهز للتوصيل':
            body_text = f"مرحباً، طلبك رقم {order_name} جاهز الآن للتوصيل أو الاستلام من المعرض!"
        elif status == 'تم تسليمه للتوصيل':
            body_text = f"مرحباً، طلبك رقم {order_name} أصبح الآن مع شركة التوصيل!"
        else:
            body_text = f"مرحباً، تم تحديث حالة طلبك رقم {order_name} إلى: {status}"

        # 2. النص اللاحق (الخاتمة / الإضافة)
        footer = "\n\nهذا الرقم مخصص للنشرات والرد الآلي، للطلب والاستفسار يرجى التواصل معنا على واتساب: 0780110417"

        # دمج النص الرئيسي مع النص اللاحق
        message = body_text + footer

        if not phone_raw:
            logging.error("No phone number found in payload.")
            return jsonify({
                "status": "error", 
                "message": "No phone number provided in payload",
                "received_data": data
            }), 400

        # تنظيف رقم الهاتف
        clean_phone = re.sub(r'\D', '', str(phone_raw))

        # إرسال إلى UltraMsg
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
        payload = {
            "token": ULTRAMSG_TOKEN,
            "to": clean_phone,
            "body": message
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
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
