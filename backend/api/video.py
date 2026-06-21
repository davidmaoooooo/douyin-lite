from . import api, make_response
from flask import request
from utils.request import Request

request_instance = Request()  # 创建 Request 类的实例
"""
@desc: 获取视频详细信息
@url: /aweme/v1/web/aweme/detail
@param: aweme_id
"""


@api.route('/aweme/detail/')
def get_detail():
    aweme_id = request.args.get('aweme_id')
    if not aweme_id:
        return {'error': 'Missing aweme_id parameter'}, 400
    params = {"aweme_id": aweme_id}
    url = '/aweme/v1/web/aweme/detail/'
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取相关视频
@url：/aweme/related
@param: aweme_id
@param: count
@param: filterGids 第一次可以不传值，第二次传入 第一次请求的aweme_id ;
示例：filterGids: 7380308118061780287,7386945509082025225,
7386952050208247080,7379532523379903795,7379995831534947618,7360577857900350746,7391047134314908982,
7391866100910247207,7405446866906729782
@param： refresh_index  第一次：1
"""


@api.route('/aweme/related/')
def get_related():
    aweme_id = request.args.get('aweme_id')
    count = request.args.get('count')
    filter_gids = request.args.get('filterGids')
    refresh_index = request.args.get('refresh_index')
    if not aweme_id:
        return {'error': 'Missing aweme_id parameter'}, 400
    params = {"aweme_id": aweme_id, "count": count, "filterGids": filter_gids,
              "awemePcRecRawData": '{"is_client":false}', "sub_channel_id": 0, "Seo-Flag": 0,
              "refresh_index": refresh_index
              }
    url = '/aweme/v1/web/aweme/related/'
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取视频评论
@url: /aweme/v1/web/comment/list/
@param: cursor 0 第二次请求为上一个请求的请求count；第一次为0 5 第二次为5 20 第三次为25 25依次递增
@param: count 5
"""


@api.route('/comment/list/')
def get_comment_list():
    aweme_id = request.args.get('aweme_id')
    cursor = request.args.get('cursor')
    count = request.args.get('count')
    params = {
        "aweme_id": aweme_id,
        "cursor": cursor,
        "count": count
    }
    url = '/aweme/v1/web/comment/list/'
    return make_response(request_instance.getJSON(url, params))


"""
@desc： 展开更多评论
@url： /aweme/v1/web/comment/list/reply/
@param: item_id 视频id
@param：comment_id 评论id
@param：cursor 0 3 13
@param： count 3 10 10
"""


@api.route('/comment/list/reply/')
def get_reply_list():
    item_id = request.args.get('item_id')  # 视频id
    comment_id = request.args.get('comment_id')
    cursor = request.args.get('cursor')
    count = request.args.get('count')
    params = {
        "item_id": item_id,
        "comment_id": comment_id,
        "cursor": cursor,
        "count": count
    }
    url = '/aweme/v1/web/comment/list/reply/'
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取首页瀑布流视频
@url: /aweme/v2/web/module/feed/
@param: count 数量
@param: tag_id 标签id "300205-游戏","300206-二次元",  "300209-音乐" "300215-影视"，"300204-美食",300213 知识
    300214 小剧场  300216 生活  "300207-体育",300221 旅行 300217 亲子 300220 动物 300219 三农 300218 汽车 300222 美妆穿搭

"""


@api.route('/module/feed/')
def get_module_feed():
    count = request.args.get('count', '20')
    refresh_index = request.args.get('refresh_index', '1')
    tag_id = request.args.get('tag_id', '')
    presented_ids = request.args.get('presented_ids', '')
    filter_gids = request.args.get('filter_gids', '')
    is_active_tab = request.args.get('is_active_tab', 'false')
    active_id = request.args.get('active_id', '')
    params = {
        'module_id': '3003101',
        'count': count,
        'filterGids': filter_gids,
        'presented_ids': presented_ids,
        'refresh_index': refresh_index,
        'refer_id': '',
        'refer_type': '10',
        'pull_type': '2',
        'awemePcRecRawData': '{"is_xigua_user":0,"danmaku_switch_status":1,"is_client":false}',
        'Seo-Flag': '0',
        'install_time': str(int(__import__('time').time()) - 86400),
        'tag_id': tag_id,
        'active_id': active_id,
        'is_active_tab': is_active_tab,
        'use_lite_type': '0',
        'xigua_user': '0',
        'pc_libra_divert': 'Windows',
        'support_h265': '0',
        'support_dash': '0',
    }
    url = '/aweme/v2/web/module/feed/'
    return make_response(request_instance.getJSON(url, params))


'''
@desc: 获取推荐页feed
@url: /aweme/v1/web/tab/feed/
'''


@api.route('/web/tab/feed/')
def get_tab_feed():
    count = request.args.get('count')
    refresh_index = request.args.get('refresh_index')
    params = {"count": count,
              'video_type_select': '1',
              "aweme_pc_rec_raw_data": '{"is_client":false,"ff_danmaku_status":1,"danmaku_switch_status":1,'
                                       '"is_auto_play":0,"is_full_screen":0,"is_full_webscreen":0,"is_mute":0,'
                                       '"is_speed":1,"is_visible":1,"related_recommend":1}',
              "refresh_index": refresh_index
              }
    url = '/aweme/v1/web/tab/feed/'
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 用户点赞
@url: /aweme/v1/web/commit/item/digg/
@param: aweme_id 视频id 必须
@param: type 点赞类型 1 点赞 0 取消
@param： item_type 暂未知道含义 默认为0
"""


@api.route('/commit/item/digg/')
def post_digg():
    aweme_id = request.args.get('aweme_id')
    digg_type = request.args.get('type')
    item_type = request.args.get('item_type')

    url = '/aweme/v1/web/commit/item/digg/'
    params = {

    }
    data = {
        'aweme_id': aweme_id,
        'type': digg_type,
        'item_type': item_type
    }
    return make_response(request_instance.getJSON(url, params, data, live=None, web2=1))
