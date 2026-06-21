from flask import Blueprint
from utils.request import Request

# 创建直接访问API蓝图，不带前缀
direct_api = Blueprint('direct_api', __name__)

request_instance = Request()

"""
直接访问API接口 - 无前缀版本
"""


@direct_api.route('/webcast/web/feed/follow/')
def get_live_feed_follow():
    """
    @desc: 获取直播关注feed
    @param: scene (默认值: aweme_pc_follow_top)
    @url: 实际访问路径: /webcast/web/feed/follow/ (无前缀)
    """
    from flask import request

    scene = request.args.get('scene')
    if not scene:
        # 如果没有提供scene参数，默认使用aweme_pc_follow_top
        scene = 'aweme_pc_follow_top'

    url = '/webcast/web/feed/follow/'
    params = {
        'scene': scene
    }
    from . import make_response
    return make_response(request_instance.getJSON(url, params))