from . import api, make_response
from utils.request import Request
from flask import request

request_instance = Request()  # 创建 Request 类的实例

'''
@desc: 底部栏推荐词
@url: aweme/v1/web/seo/inner/link/
'''


@api.route('/seo/inner/link/')
def get_seo_link():
    url = '/aweme/v1/web/seo/inner/link/'
    params = {
        'channel': 'channel_pc_web'
    }
    return make_response(request_instance.getJSON(url, params))


'''
@desc: 获取表情列表
@url： '/aweme/v1/web/emoji/list'
'''


@api.route('/emoji/list/')
def get_emoji_list():
    url = '/aweme/v1/web/emoji/list'
    params = {
        'channel': 'channel_pc_web'
    }
    return make_response(request_instance.getJSON(url, params))


'''
@desc: 自定义的表情或者收藏的
@url: /aweme/v1/web/im/resources/emoticon/trending
'''


@api.route('/im/resources/emoticon/trending')
def get_emoticon_list():
    url = '/aweme/v1/web/im/resources/emoticon/trending'
    cursor = request.args.get('cursor')
    count = request.args.get('count')
    params = {
        'cursor': cursor,
        'count': count
    }
    return make_response(request_instance.getJSON(url, params))


'''
@desc: 搜索框热搜列表
@url: /aweme/v1/web/hot/search/list/
'''


@api.route('hot/search/list/')
def get_hot_list():
    url = '/aweme/v1/web/hot/search/list/'
    params = {
    }
    return make_response(request_instance.getJSON(url, params))


'''
@desc: 精选页标签
@url： /aweme/v1/web/home/channel/setting/
'''


@api.route('/home/channel/setting/')
def get_channel_setting():
    url = '/aweme/v1/web/home/channel/setting/'
    params = {
        'channel': 'channel_pc_web'
    }
    return make_response(request_instance.getJSON(url, params))
