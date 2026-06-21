import argparse
import os
import sys
from flask import Flask, request, jsonify
from api import api as api_blueprint
from api.direct_api import direct_api as direct_blueprint
from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(api_blueprint, url_prefix='/aweme/v1/web')
# 精选页面使用/aweme/v2/web
app.register_blueprint(api_blueprint, url_prefix='/aweme/v2/web', name='api_v2')
# 注册无前缀的直播API蓝图
app.register_blueprint(direct_blueprint)

CORS(app, origins='*', supports_credentials=True)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/api/config/cookie', methods=['POST'])
def set_cookie():
    """桌面版 Cookie 设置接口"""
    cookie_str = request.json.get('cookie', '')
    if not cookie_str:
        return jsonify({'ok': False, 'error': 'cookie is required'}), 400
    from utils.cookies import normalize_cookie, save_cookie, get_cookie_dict
    cookie = normalize_cookie(cookie_str)
    save_cookie(cookie)
    # 重新加载到全局 Request 实例
    if hasattr(app, 'request_instance'):
        app.request_instance.COOKIES = cookie
    return jsonify({'ok': True})


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({'ok': True})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=3010)
    args = parser.parse_args()
    app.run(host='127.0.0.1', port=args.port)