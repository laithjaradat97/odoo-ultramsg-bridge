import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# جلب البيانات السرية من متغيرات البيئة في Render
ULTRAMSG_INSTANCE_ID = os.environ.get('ULTRAMSG_INSTANCE_ID')
ULTRAMSG_TOKEN = os.environ.get('ULTRAMSG_TOKEN')

@app.route('/send-invoice', methods=['POST'])
def send_invoice():
    try:
        data = request.json or {}
        
        # استخراج الهواتف والحقول من أودو
        phone = data.get('mobile') or data.get('phone') or data.get('partner_id', {}).get('phone')
        status = data.get('x_studio_selection_field_951_1j26vhvop')
        order_name = data.get('name', 'الطلب')

        # تحديد نص الرسالة حسب الحالة
        if status == 'في التحضير':
            message = f"مرحباً، طلبك رقم {order_name} أصبح الآن قيد التحضير!"
        elif status == 'جاهز للتوصيل':
            message = f"مرحباً، طلبك رقم {order_name} جاهز للتوصيل الآن!"
        elif status == 'تم تسليمه للتوصيل':
            message = f"مرحباً، طلبك رقم {order_name} أصبح الآن مع شركة التوصيل!"
        else:
            message = f"مرحباً، تم تحديث حالة طلبك رقم {order_name} إلى: {status}"

        if not phone:
            return jsonify({"error": "No phone number found", "received_data": data}), 400

        # إرسال الرسالة إلى UltraMsg
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
        payload = {
            "token": ULTRAMSG_TOKEN,
            "to": str(phone).strip(),
            "body": message
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(url, data=payload, headers=headers)
        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
