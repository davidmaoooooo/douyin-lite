from flask import Blueprint, jsonify

api = Blueprint('api', __name__)


def make_response(result):
    """
    统一处理接口返回
    result: getJSON 返回的元组 (data, status_code)
    """
    if isinstance(result, tuple) and len(result) == 2:
        data, status_code = result
        return jsonify(data), status_code
    # 兼容旧格式
    return jsonify(result) if result else jsonify({'error': 'No data'}), 404


from . import user, search, video, common_api, recommend, live_api