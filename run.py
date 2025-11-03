
import os
from app import create_app
from flask import send_from_directory

app = create_app()

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)