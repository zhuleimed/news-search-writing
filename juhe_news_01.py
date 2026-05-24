import requests

# 923-新闻列表查询 - 代码参考（根据实际业务情况修改）

# 基本参数配置
apiUrl = 'http://v.juhe.cn/toutiao/index'  # 接口请求URL
apiKey = 'd64199aad6bd1d32e17551834d07a58c'  # 在个人中心->我的数据,接口名称上方查看

def main(type):
    # 接口请求入参配置
    if type == 'top':
        pages = 3
    else:
        pages = 1

    news_list = []
    for page in range(pages):
        requestParams = {
            'key': apiKey,
            'type': type,
            'page': page,
            'page_size': '',
            'is_filter': '',
        }

        # 发起接口网络请求
        response = requests.get(apiUrl, params=requestParams)

        # 解析响应结果
        if response.status_code == 200:
            responseResult = response.json()
            # 网络请求成功。可依据业务逻辑和接口文档说明自行处理。
            context = responseResult['result']['data']

            for i in context:
                new_dict = {}
                new_dict['title'] = i['title']
                new_dict['url'] = i['url']
                news_list.append(new_dict)

        else:
            # 网络异常等因素，解析结果异常。可依据业务逻辑自行处理。
            print('请求异常')

    return news_list

if __name__ == '__main__':
    type = 'tiyu'
    main(type)