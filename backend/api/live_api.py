from . import api, make_response
from utils.request import Request
from flask import request

"""
直播相关API接口
"""

request_instance = Request()


@api.route('/webcast/room/info_by_scene/')
def get_live_info_by_scene():
    """
    @desc: 通过房间id获取获取直播的推流
    @param: room_id
    @url: 实际访问路径: /aweme/v1/web/webcast/room/info_by_scene/ (通过蓝图前缀)
    """
    room_id = request.args.get('room_id')
    if not room_id:
        return {'error': 'Missing room_id parameter'}, 400
    url = '/webcast/room/info_by_scene/'
    params = {
        'room_id': room_id,
        'live_id': '1',
        'scene': 'aweme_video_feed_pc',
        'region': 'cn'
    }
    return make_response(request_instance.getJSON(url, params, live=1))

