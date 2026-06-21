from utils.request import Request
from . import api, make_response
from flask import request

request_instance = Request()  # 创建 Request 类的实例
'''
@desc: 获取用户个人的信息
@url: '/aweme/v1/web/user/profile/self/'
'''


@api.route('/user/profile/self/')
def get_user_info_self():
    url = '/aweme/v1/web/user/profile/self/'
    params = {}
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取其他用户信息
@url: /aweme/v1/web/user/profile/other/
"""


@api.route('/user/profile/other/')
def get_user_info():
    sec_user_id = request.args.get('sec_user_id')
    url = '/aweme/v1/web/user/profile/other/'
    params = {
        'sec_user_id': sec_user_id,
        'source': 'channel_pc_web',
        'publish_video_strategy_type': '2',
        'personal_center_strategy': '1'
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取用户作品列表
@url：/aweme/v1/web/aweme/post/
@param: forward_end_cursor 上一个接口的max_cursor
@param: sec_user_id 用户id
@param: max_cursor 游标
@param: count 每页数量
@param: locate_item_id 视频id
@param: need_time_list 是否需要时间列表 0 | 1
@param: locate_query 是否定位 默认 false
"""


@api.route('/aweme/post/')
def get_user_post():
    sec_user_id = request.args.get('sec_user_id')
    count = request.args.get('count')
    max_cursor = request.args.get('max_cursor')
    locate_item_id = request.args.get('locate_item_id')
    need_time_list = request.args.get('need_time_list')
    locate_query = request.args.get('locate_query')
    forward_anchor_cursor = request.args.get('forward_anchor_cursor')
    forward_end_cursor = request.args.get('forward_end_cursor')
    locate_item_cursor = request.args.get('locate_item_cursor')
    url = '/aweme/v1/web/aweme/post/'
    params = {
        'sec_user_id': sec_user_id,
        'count': count,
        'max_cursor': max_cursor,
        'locate_item_id': locate_item_id,
        'locate_query': locate_query,
        'forward_anchor_cursor': forward_anchor_cursor,
        'show_live_replay_strategy': '1',
        'need_time_list': need_time_list,
        'locate_item_cursor': locate_item_cursor,
        'time_list_query': '0',
        'publish_video_strategy_type': '2'
    }
    if forward_end_cursor:
        params["forward_end_cursor"] = forward_end_cursor
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取用户私密作品列表
@url: /aweme/v1/web/private/aweme/
@param: min_cursor 游标
@param: max_cursor 游标
@param: count 每页数量
"""


@api.route('/private/aweme/')
def get_user_private_post():
    min_cursor = request.args.get('min_cursor')
    max_cursor = request.args.get('max_cursor')
    count = request.args.get('count')
    url = '/aweme/v1/web/private/aweme/'
    params = {
        'min_cursor': min_cursor,
        'max_cursor': max_cursor,
        'count': count,
        'pc_client_type': '1'
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取用户作品列表当前的视频列表
@url: /aweme/v1/web/locate/post/
@param: sec_user_id 用户id
@param: max_cursor 游标
@param: count 每页数量
@param: locate_item_id 视频id
@param: locate_item_cursor 定位项游标
@param: locate_query 是否定位 默认 true
"""


@api.route('/locate/post/')
def get_user_post_locate():
    sec_user_id = request.args.get('sec_user_id')
    count = request.args.get('count', '10')
    max_cursor = request.args.get('max_cursor', '0')
    locate_item_id = request.args.get('locate_item_id')
    locate_item_cursor = request.args.get('locate_item_cursor')
    locate_query = request.args.get('locate_query', 'true')
    url = '/aweme/v1/web/locate/post/'
    params = {
        'sec_user_id': sec_user_id,
        'max_cursor': max_cursor,
        'locate_item_id': locate_item_id,
        'locate_item_cursor': locate_item_cursor,
        'locate_query': locate_query,
        'count': count,
        'publish_video_strategy_type': '2',
        'pc_libra_divert': 'Windows',
        'support_h265': '0',
        'support_dash': '0',
    }
    return make_response(request_instance.getJSON(url, params, data=None, live=None, web2=1))


"""
@desc: 获取用户喜欢的列表
@url: /aweme/v1/web/aweme/favorite/
"""


@api.route('/aweme/favorite/')
def get_user_favorite():
    sec_user_id = request.args.get('sec_user_id')
    count = request.args.get('count', '18')
    min_cursor = request.args.get('min_cursor', '0')
    max_cursor = request.args.get('max_cursor', '0')
    url = '/aweme/v1/web/aweme/favorite/'
    params = {
        'sec_user_id': sec_user_id,
        'count': count,
        'max_cursor': max_cursor,
        'min_cursor': min_cursor,
        'whale_cut_token': '',
        'cut_version': '1',
        'publish_video_strategy_type': '2',
    }
    return make_response(request_instance.getJSON(url, params, data=None, live=None, web2=1))


"""
@desc: 获取用户收藏视频列表
@url： /aweme/v1/web/aweme/listcollection/
"""


@api.route('/aweme/listcollection/')
def get_list_collection():
    count = request.args.get('count')
    cursor = request.args.get('cursor')

    url = '/aweme/v1/web/aweme/listcollection/'
    params = {}
    data = {
        'count': count,
        'cursor': cursor
    }
    return make_response(request_instance.getJSON(url, params, data))


"""
@desc: 获取音乐详情
@url: /aweme/v1/web/music/detail/
@param: music_id 7028149283996125966
@param: scene 1
"""


@api.route('/music/detail/')
def get_music_detail():
    music_id = request.args.get('music_id')
    scene = request.args.get('scene')
    url = '/aweme/v1/web/music/detail/'
    params = {
        'music_id': music_id,
        'scene': scene
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 收藏的音乐
@url: /aweme/v1/web/music/listcollection/
@param: cursor 0
@param: count 18
"""


@api.route('/music/listcollection/')
def get_list_collection_music():
    count = request.args.get('count')
    cursor = request.args.get('cursor')

    url = '/aweme/v1/web/music/listcollection/'
    params = {
        'count': count,
        'cursor': cursor
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 收藏夹
@url: /aweme/v1/web/collects/list/
@param: cursor 0
@param: count 18
"""


@api.route('/collects/list/')
def get_list_collects():
    count = request.args.get('count')
    cursor = request.args.get('cursor')

    url = '/aweme/v1/web/collects/list/'
    params = {
        'count': count,
        'cursor': cursor
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 收藏夹视频信息
@url: /aweme/v1/web/collects/video/list/
@param: cursor 0
@param: count 18
"""


@api.route('/collects/video/list/')
def get_list_collects_video():
    collects_id = request.args.get('collects_id')
    count = request.args.get('count')
    cursor = request.args.get('cursor')

    url = '/aweme/v1/web/collects/video/list/'
    params = {
        'collects_id': collects_id,
        'count': count,
        'cursor': cursor
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 收藏的合集
@url: /aweme/v1/web/mix/listcollection/
"""


@api.route('/mix/listcollection/')
def get_list_collection_mix():
    count = request.args.get('count')
    cursor = request.args.get('cursor')

    url = '/aweme/v1/web/mix/listcollection/'
    params = {
        'count': count,
        'cursor': cursor
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 收藏的短剧
@url: /aweme/v1/web/series/collections
"""


@api.route('/series/collections/')
def get_list_collection_series():
    count = request.args.get('count')
    cursor = request.args.get('cursor')

    url = '/aweme/v1/web/series/collections'
    params = {
        'count': count,
        'cursor': cursor
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 用户创建的合集
@url: /aweme/v1/web/mix/list/
@param: sec_user_id 用户sec_id
@param: count 数量
@param：cursor 游标
"""


@api.route('/mix/list/')
def get_mix_list():
    sec_user_id = request.args.get('sec_user_id')
    count = request.args.get('count')
    cursor = request.args.get('cursor')
    list_scene = request.args.get('list_scene')

    url = '/aweme/v1/web/mix/list/'
    params = {
        'sec_user_id': sec_user_id,
        'count': count,
        'cursor': cursor,
        'req_from': 'channel_pc_web',
        'list_scene': list_scene
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 合集详情
@url: /aweme/v1/web/mix/detail/
@param: mix_id
"""


@api.route('/mix/detail/')
def get_mix_detail():
    mix_id = request.args.get('mix_id')
    url = '/aweme/v1/web/mix/detail/'
    params = {
        'mix_id': mix_id
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 合集的详细列表
@url: /aweme/v1/web/mix/aweme/
"""


@api.route('/mix/aweme/')
def get_mix_list_detail():
    mix_id = request.args.get('mix_id')
    count = request.args.get('count')
    cursor = request.args.get('cursor')

    url = '/aweme/v1/web/mix/aweme/'
    params = {
        'mix_id': mix_id,
        'count': count,
        'cursor': cursor,
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取用户查看用户列表
@url: /aweme/v1/web/view/user/visited/list/
@param: count 数量 默认 20
@param: cursor 游标 初始为空
"""


@api.route('/view/user/visited/list/')
def get_view_user_visited_list():
    count = request.args.get('count')
    cursor = request.args.get('cursor')
    url = '/aweme/v1/web/view/user/visited/list/'
    params = {}
    data = {
        'count': count,
        'cursor': cursor
    }
    return make_response(request_instance.getJSON(url, params, data))


"""
@desc: 获取用户观看历史列表
@url: /aweme/v1/web/history/read/
@param: status  观看进度  不限-1 未看完 0  已看完 1
@param: directory 视频时长 不限：0 小于1分钟：1 1-3分钟：2 3-10分钟：3 10分钟以上：4
@param: category 视频分类  不限：0 二次元：1 音乐：2 体育：3 电影：4 游戏：5
"""


@api.route('/history/read/')
def get_history_read():
    count = request.args.get('count')
    max_cursor = request.args.get('max_cursor')
    directory = request.args.get('directory')
    category = request.args.get('category')
    status = request.args.get('status')

    url = '/aweme/v1/web/history/read/'
    params = {
        'count': count,
        'max_cursor': max_cursor,
        'directory': directory,
        'category': category,
        'status': status
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc:获取用户的观看的影视综记录
@url: /aweme/v1/web/lvideo/query/history/
"""


@api.route('/lvideo/query/history/')
def get_lvideo_history_read():
    count = request.args.get('count')
    cursor = request.args.get('cursor')

    url = '/aweme/v1/web/lvideo/query/history/'
    params = {
        'count': count,
        'cursor': cursor
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取用户观看的直播记录
@url:/webcast/feed/
"""


@api.route('/webcast/feed/')
def get_webcast_history_read():
    max_time = request.args.get('max_time')

    url = '/webcast/feed/'
    params = {
        'max_time': max_time,
        'live_id': 1,
        'source_key': 'drawer_hot_live_history',
        'need_map': 1
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 上传历史记录
@url: /aweme/v1/web/history/write/
@param: aweme_id
@param: author_id(不是sec_id)
@method: post
"""

"""
@desc: 获取用户关系列表
@url：/aweme/v1/web/im/spotlight/relation/
"""


@api.route('/im/spotlight/relation/')
def get_relation():
    count = request.args.get('count')
    min_time = request.args.get('min_time')
    max_time = request.args.get('max_time')  # 当前的时间戳
    url = '/aweme/v1/web/im/spotlight/relation/'
    params = {
        'count': count,
        'max_time': max_time,
        'min_time': min_time,
        'need_remove_share_panel': 'true',
        'need_sorted_info': 'true',
        'with_fstatus': '1'
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取用户关注列表
@url: /aweme/v1/web/user/following/list/
@param: source_type 1最近关注 3最早关注 4 综合排序
"""


@api.route('/user/following/list/')
def get_user_following():
    user_id = request.args.get('user_id')
    sec_user_id = request.args.get('sec_user_id')
    count = request.args.get('count')
    source_type = request.args.get('source_type')
    offset = request.args.get('offset')
    min_time = request.args.get('min_time')
    max_time = request.args.get('max_time')
    is_top = request.args.get('is_top')
    url = '/aweme/v1/web/user/following/list/'
    params = {
        'user_id': user_id,
        'sec_user_id': sec_user_id,
        'count': count,
        'offset': offset,
        'max_time': max_time,
        'min_time': min_time,
        'source_type': source_type,
        'gps_access': '0',
        'address_book_access': '0',
        'is_top': is_top,
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取粉丝列表
@url: /aweme/v1/web/user/follower/list/
"""


@api.route('/user/follower/list/')
def get_user_follower():
    user_id = request.args.get('user_id')
    sec_user_id = request.args.get('sec_user_id')
    count = request.args.get('count')
    source_type = request.args.get('source_type')
    offset = request.args.get('offset')
    min_time = request.args.get('min_time')
    max_time = request.args.get('max_time')
    url = '/aweme/v1/web/user/follower/list/'
    params = {
        'user_id': user_id,
        'sec_user_id': sec_user_id,
        'count': count,
        'offset': offset,
        'max_time': max_time,
        'min_time': min_time,
        'source_type': source_type,
        'gps_access': '0',
        'address_book_access': '0',
        'is_top': '1',
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 用户主页搜索
@url: /aweme/v1/web/home/search/item/
@param: search_channel= aweme_favorite_video | aweme_collect_video | aweme_viewed_video | aweme_personal_home_video
"""


@api.route('/home/search/item/')
def get_search_item():
    search_channel = request.args.get('search_channel')
    search_source = request.args.get('search_source')
    search_scene = request.args.get('search_scene')
    sort_type = request.args.get('sort_type')
    keyword = request.args.get('keyword')
    from_user = request.args.get('from_user')
    count = request.args.get('count')
    offset = request.args.get('offset')
    publish_time = request.args.get('publish_time')
    is_filter_search = request.args.get('is_filter_search')
    query_correct_type = request.args.get('query_correct_type')
    enable_history = request.args.get('enable_history')
    url = '/aweme/v1/web/home/search/item/'
    params = {
        'search_channel': search_channel,
        'search_source': search_source,
        'from_user': from_user,
        'count': count,
        'offset': offset,
        'search_scene': search_scene,
        'sort_type': sort_type,
        'publish_time': publish_time,
        'is_filter_search': is_filter_search,
        'query_correct_type': query_correct_type,
        'keyword': keyword,
        'enable_history': enable_history,
        'search_id': ''
    }
    return make_response(request_instance.getJSON(url, params))


'''
@desc: 查询当前用户的短剧列表
@url: /aweme/v1/web/series/list/
@url2: /aweme/v1/web/activity/pull/carnival/  暂时不知道做什么的
@method: get
@param: sec_user_id
@param: cursor 0
@param: count 10
@param: req_from channel_pc_web
'''


@api.route('/series/list/')
def get_series_list():
    sec_user_id = request.args.get('sec_user_id')
    cursor = request.args.get('cursor')
    count = request.args.get('count')
    url = '/aweme/v1/web/series/list/'
    params = {
        'sec_user_id': sec_user_id,
        'cursor': cursor,
        'count': count,
        'req_from': 'channel_pc_web'
    }
    return make_response(request_instance.getJSON(url, params))


'''
@desc: 添加收藏
@url: /aweme/v1/web/aweme/collect/
@method: post
@data： action: 1
@data： aweme_id: 7422146115929247036
@data： aweme_type: 0
'''

'''
@desc: 添加收藏到特定的收藏夹
@url: /aweme/v1/web/collects/video/move/
@method: post
@params： collects_name: 草
@params： item_ids: 7422146115929247036
@params：item_type: 2
@params： move_collects_list: 7417883349374637865
@params：to_collects_id: 7417883349374637865
'''

'''
@desc: 用户关注的人的视频
@url: /aweme/v1/web/follow/feed/
@param: cursor  开始为0 下一次为接口返回的cursor
@param： level 1
@param： count 默认20
@param： pull_type 18
@param: refresh_type 18
@param: aweme_ids 默认为空
@param: room_ids 默认为空
'''


@api.route('/follow/feed/')
def get_follow_feed():
    cursor = request.args.get('cursor')
    level = request.args.get('level')
    count = request.args.get('count')
    pull_type = request.args.get('pull_type')
    refresh_type = request.args.get('refresh_type')
    aweme_ids = request.args.get('aweme_ids')
    room_ids = request.args.get('room_ids')
    url = '/aweme/v1/web/user/follower/list/'
    params = {
        'cursor': cursor,
        'level': level,
        'count': count,
        'pull_type': pull_type,
        'refresh_type': refresh_type,
        'aweme_ids': aweme_ids,
        'room_ids': room_ids,
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 稍后再看记录
@url: /aweme/v1/web/watchlater/list/
@param: offset 0
@param: list_type 0
@param: operate_type 0
"""


@api.route('/watchlater/list/')
def get_watchlater_list():
    offset = request.args.get('offset')
    list_type = request.args.get('list_type')
    operate_type = request.args.get('operate_type')
    url = '/aweme/v1/web/watchlater/list/'
    params = {
        'offset': offset,
        'list_type': list_type,
        'operate_type': operate_type,
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: at列表
@url: /aweme/v1/web/familiar/atlist/
@param: cursor 20
@param: count 20
@param: scene 2
@param: group_id 7586334306945207609
"""


@api.route('/familiar/atlist/')
def get_familiar_atlist():
    count = request.args.get('count')
    cursor = request.args.get('cursor')
    scene = request.args.get('scene')
    group_id = request.args.get('group_id')
    url = '/aweme/v1/web/familiar/atlist/'
    params = {
        'cursor': cursor,
        'count': count,
        'scene': scene,
        'group_id': group_id,
        'need_page': 'true'
    }
    return make_response(request_instance.getJSON(url, params))


"""
@desc: 获取qrcode
@url: /aweme/v1/web/fancy/qrcode/info/
@param: app_name aweme

post 参数
@param: schema_type 4
@param: object_id  75389470922 用户短id
@param  qrcode_type 1  二维码类型
"""


@api.route('/fancy/qrcode/info/')
def get_fancy_qrcode_info():
    app_name = request.args.get('app_name')
    object_id = request.args.get('object_id')
    schema_type = request.args.get('schema_type')
    qrcode_type = request.args.get('qrcode_type')
    url = '/aweme/v1/web/fancy/qrcode/info/'
    params = {
        'app_name': app_name,
    }
    data = {
        'app_name': app_name,
        'schema_type': schema_type,
        'object_id': object_id,
        'qrcode_type': qrcode_type
    }
    return make_response(request_instance.getJSON(url, params, data))
