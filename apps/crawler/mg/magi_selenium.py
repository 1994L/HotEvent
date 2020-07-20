import os
import time
import json
import random
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# settings
BASE_PATH = os.path.dirname(os.path.dirname(__file__))
HTML_BASE_PATH = os.path.join(BASE_PATH, 'mg/htmls/magi')
JSON_BASE_PATH = os.path.join(BASE_PATH, 'mg/json/magi')

msg = {'status': 1, 'message': 'success', 'html_path': '', 'data': {}}

# 保存网页
def save_html(p, data):
    f = open(p, 'w', encoding='utf-8')
    f.write(data)
    f.close()
    print('{}保存完成!'.format(p))
    return 1


# 读取网页
def read_html(p):
    with open(p, 'r', encoding='utf-8') as f:
        html = f.read()
    return html


# 请求网页
def run_selenium(driver, kwd):
    driver.get('https://magi.com/')
    # wait seconds 等待页面加载
    driver.implicitly_wait(2)

    # 处理名称输入方法/速度
    if len(kwd) < 1:
        msg['status'] = 0
        msg['message'] = 'kwd is empty'
        print(msg)
        return (msg)
    elif 0 < len(kwd) < 5:
        kwd_1 = kwd[:1]
        kwd_2 = kwd[1:]
    else:
        kwd_1 = kwd.split(' ')[0]
        kwd_2 = kwd.replace(kwd_1, '')

    driver.find_element_by_id('search-input').send_keys(kwd_1)
    time.sleep(random.random())
    driver.find_element_by_id('search-input').send_keys(kwd_2)
    driver.find_element_by_id("search-submit").click()
    # 模拟enter键操作回车按钮
    driver.find_element_by_id("search-submit").send_keys(Keys.ENTER)

    # 随机滚动
    if random.randint(1, 3) < 2:
        js1 = "document.documentElement.scrollTop={}".format(random.randint(120, 400))
        driver.execute_script(js1)

    html_name = kwd.replace(' ', '_').replace(':', '_').replace('.', '_').replace('·', '_') + '.html'

    try:
        driver.find_element_by_xpath('//div[@class="card"]')
    except:
        msg['status'] = 0
        msg['message'] = '{} - response not find "//div[@class="card"]" '.format(kwd)
        print(msg)
        driver.close()  # 退出当前页面
        driver.quit()  # 退出浏览器
        return msg
    else:
        # html_path = r'/home/yyq/code/COVID_19/World/codes/number/htmls/163/{}'.format(html_name)
        html_data = driver.page_source
        driver.close()  # 退出当前页面
        driver.quit()  # 退出浏览器
        msg['html_path'] = html_data
        return msg


# 解析网页
def parse_page(html, kwd):
    html = etree.HTML(html)
    # 1. 上边的实体列表(一般一个,也可能多个)
    fact_item_list = []
    fact_div_list = html.xpath('//div[@class="card" and (@data-type="fact" or @data-subtype="entity")]')
    for fact_div in fact_div_list:
        # 1.1 每个小个3模块为一组
        fact_name = fact_div.xpath('./header/div/h2/text()')        # 迈凯伦
        fact_class = fact_div.xpath('./header/div/span/text()')     # 实体
        fact_scores = fact_div.xpath('./header/svg/text/text()')    # 100
        # 1.1.1 描述模块
        description_item_list = []
        description_div_list = fact_div.xpath('./div/section[@data-scope="description"]/div/div[@data-span="cell"]')
        for description_div in description_div_list:
            description_subject = description_div.xpath('./article/dl/dd[@data-field="subject"]/text()')    # 迈凯伦
            description_class = description_div.xpath('./article/dl/dd[@data-field="predicate"]/text()')    # 描述
            description_name = description_div.xpath('./article/dl/dd[@data-field="object"]/text()')    # F1历史上最成功的车队
            description_scores = description_div.xpath('./article/dl/@data-confidence') # 23

            # 1.1.1.1 每一条描述下的信息
            description_learning_item_list = []
            description_learning_li_list = description_div.xpath('./article/div[@data-collapse="collapsed"]/ul/li')
            for description_learning_li in description_learning_li_list:
                description_group_list_learning_from = description_learning_li.xpath('./@title')
                description_group_list = []
                group_li_list = description_learning_li.xpath('./ol/li')
                for group_li in group_li_list:
                    description_learning_news_title = group_li.xpath('./a/h5/text()')
                    description_learning_news_href = group_li.xpath('./a/@href')
                    description_learning_news_cite = group_li.xpath('./a/div/cite/text()')
                    description_learning_news_time = group_li.xpath('./a/div/time/text()')

                    description_learning_news_item = {}
                    description_learning_news_item['description_learning_news_title'] = description_learning_news_title[0] if description_learning_news_title else ''
                    description_learning_news_item['description_learning_news_href'] = description_learning_news_href[0] if description_learning_news_href else ''
                    description_learning_news_item['description_learning_news_cite'] = description_learning_news_cite[0] if description_learning_news_cite else ''
                    description_learning_news_item['description_learning_news_time'] = description_learning_news_time[0] if description_learning_news_time else ''
                    description_group_list.append(description_learning_news_item)

                group_item = {}
                group_item['group_list_learning_from'] = description_group_list_learning_from[0] if description_group_list_learning_from else ''
                group_item['group_list'] = description_group_list

                description_learning_item_list.append(group_item)

            description_item = {}
            description_item['description_subject'] = description_subject[0] if description_subject else ''
            description_item['description_class'] = description_class[0] if description_class else ''
            description_item['description_name'] = description_name[0] if description_name else ''
            description_item['description_scores'] = description_scores[0] if description_scores else ''
            description_item['description_learning_item_list'] = description_learning_item_list
            description_item_list.append(description_item)

        # 1.1.2 属性模块
        property_item_list = []
        property_div_list = fact_div.xpath('./div/section[@data-scope="property"]/div/div[@data-span="cell"]')
        for property_div in property_div_list:
            property_subject = property_div.xpath('./article/dl/dd[@data-field="subject"]/text()')    # 迈凯伦
            property_class = '属性'    # 属性
            property_key = property_div.xpath('./article/dl/dd[@data-field="predicate"]/text()')    # 创始人
            property_word = property_div.xpath('./article/dl/dd[@data-field="object"]/text()')    # 布鲁斯·迈凯伦
            property_scores = property_div.xpath('./article/dl/@data-confidence') # 96

            # 1.1.1.1 每一条描述下的信息
            property_learning_item_list = []
            property_learning_li_list = property_div.xpath('./article/div[@data-collapse="collapsed"]/ul/li')
            for property_learning_li in property_learning_li_list:
                property_group_list_learning_from = property_learning_li.xpath('./@title')
                property_group_list = []
                group_li_list = property_learning_li.xpath('./ol/li')
                for group_li in group_li_list:
                    property_learning_news_title = group_li.xpath('./a/h5/text()')
                    property_learning_news_href = group_li.xpath('./a/@href')
                    property_learning_news_cite = group_li.xpath('./a/div/cite/text()')
                    property_learning_news_time = group_li.xpath('./a/div/time/text()')

                    property_learning_news_item = {}
                    property_learning_news_item['property_learning_news_title'] = property_learning_news_title[0] if property_learning_news_title else ''
                    property_learning_news_item['property_learning_news_href'] = property_learning_news_href[0] if property_learning_news_href else ''
                    property_learning_news_item['property_learning_news_cite'] = property_learning_news_cite[0] if property_learning_news_cite else ''
                    property_learning_news_item['property_learning_news_time'] = property_learning_news_time[0] if property_learning_news_time else ''
                    property_group_list.append(property_learning_news_item)

                group_item = {}
                group_item['group_list_learning_from'] = property_group_list_learning_from[0] if property_group_list_learning_from else ''
                group_item['group_list'] = property_group_list

                property_learning_item_list.append(group_item)

            property_item = {}
            property_item['property_subject'] = property_subject[0] if property_subject else ''
            property_item['property_class'] = property_class
            property_item['property_key'] = property_key[0] if property_key else ''
            property_item['property_word'] = property_word[0] if property_word else ''
            property_item['property_scores'] = property_scores[0] if property_scores else ''
            property_item['property_learning_item_list'] = property_learning_item_list
            property_item_list.append(property_item)

        # 1.1.3 标签模块
        tag_item_list = []
        tag_div_list = fact_div.xpath('./div/section[@data-scope="tag"]/div/div[@data-span="cell"]')
        for tag_div in tag_div_list:
            tag_subject = tag_div.xpath('./article/dl/dd[@data-field="subject"]/text()')  # 迈凯伦
            tag_class = tag_div.xpath('./article/dl/dd[@data-field="predicate"]/text()')  # 标签
            tag_name = tag_div.xpath('./article/dl/dd[@data-field="object"]/text()')  # 品牌
            tag_scores = tag_div.xpath('./article/dl/@data-confidence')  # 100

            # 1.1.1.1 每一条描述下的信息
            tag_learning_item_list = []
            tag_learning_li_list = tag_div.xpath('./article/div[@data-collapse="collapsed"]/ul/li')
            for tag_learning_li in tag_learning_li_list:
                tag_group_list_learning_from = tag_learning_li.xpath('./@title')
                tag_group_list = []
                group_li_list = tag_learning_li.xpath('./ol/li')
                for group_li in group_li_list:
                    tag_learning_news_title = group_li.xpath('./a/h5/text()')
                    tag_learning_news_href = group_li.xpath('./a/@href')
                    tag_learning_news_cite = group_li.xpath('./a/div/cite/text()')
                    tag_learning_news_time = group_li.xpath('./a/div/time/text()')

                    tag_learning_news_item = {}
                    tag_learning_news_item['tag_learning_news_title'] = tag_learning_news_title[0] if tag_learning_news_title else ''
                    tag_learning_news_item['tag_learning_news_href'] = tag_learning_news_href[0] if tag_learning_news_href else ''
                    tag_learning_news_item['tag_learning_news_cite'] = tag_learning_news_cite[0] if tag_learning_news_cite else ''
                    tag_learning_news_item['tag_learning_news_time'] = tag_learning_news_time[0] if tag_learning_news_time else ''
                    tag_group_list.append(tag_learning_news_item)

                group_item = {}
                group_item['group_list_learning_from'] = tag_group_list_learning_from[0] if tag_group_list_learning_from else ''
                group_item['group_list'] = tag_group_list

                tag_learning_item_list.append(group_item)

            tag_item = {}
            tag_item['tag_subject'] = tag_subject[0] if tag_subject else ''
            tag_item['tag_class'] = tag_class[0] if tag_class else ''
            tag_item['tag_name'] = tag_name[0] if tag_name else ''
            tag_item['tag_scores'] = tag_scores[0] if tag_scores else ''
            tag_item['tag_learning_item_list'] = tag_learning_item_list
            tag_item_list.append(tag_item)

        fact_item = {}
        fact_item['fact_name'] = fact_name[0] if fact_name else ''
        fact_item['fact_class'] = fact_class[0] if fact_class else ''
        fact_item['fact_scores'] = fact_scores[0] if fact_scores else ''
        fact_item['description_item_list'] = description_item_list
        fact_item['property_item_list'] = property_item_list
        fact_item['tag_item_list'] = tag_item_list
        fact_item_list.append(fact_item)


    # 2. 下边的一条一条的新闻列表
    news_item_list = []
    news_div_list = html.xpath('//div[@class="card" and @data-type="web"]')
    for news_div in news_div_list:
        news_title = news_div.xpath('./a/h3/text()')
        news_url_1 = news_div.xpath('./a/cite/text()')
        news_url_2 = news_div.xpath('./a/@href')    # 备用 url
        news_time = news_div.xpath('./p/time/text()')
        news_content = ''.join(news_div.xpath('./p//text()[name(..)!="time"]'))

        news_item = {}
        news_item['news_title'] = news_title[0] if news_title else ''
        news_item['news_url'] = news_url_1[0] if news_url_1 else (news_url_2[0] if news_url_2 else '')
        news_item['news_time'] = news_time[0] if news_time else ''
        news_item['news_content'] = news_content
        news_item_list.append(news_item)

    res_item = {}
    res_item['kwd'] = kwd
    res_item['fact_item_list'] = fact_item_list
    res_item['news_item_list'] = news_item_list

    return res_item


def run(kwd):
    # selenium 位置信息配置
    # windows 本地测试
    # chrome_executable_path = r".\chromedriver.exe"
    # linux 本地测试
    # chrome_executable_path = r"./chromedriver"
    # mac 本地测试
    chrome_executable_path = os.path.join(os.path.dirname(__file__), 'chromedriver')
    # 线上服务器
    # chrome_executable_path = r"/home/yyq/code/COVID_19/World/codes/number/chromedriver"

    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

    # # selenium 参数信息配置
    desired_capabilities = webdriver.DesiredCapabilities.INTERNETEXPLORER.copy()
    # 创建的新实例驱动
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument('window-size=120x60')
    options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错
    options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
    options.add_argument(f'user-agent={user_agent}')  # --headless 后访问的时候就不携带ua了,所以会被检测出来.手动加上ua,就可以了.
    driver = webdriver.Chrome(executable_path=chrome_executable_path, chrome_options=options,
                              desired_capabilities=desired_capabilities)

    # 流程开始
    msg = run_selenium(driver, kwd)
    # msg = {'status': 1, 'html_path': '../htmls/magi/迈凯伦.html'}
    if msg['status'] == 1:
        html = msg["html_path"]
        res_item = parse_page(html, kwd)
        del msg['html_path']
        msg['data'] = res_item
        # with open(os.path.join(JSON_BASE_PATH, '{}.json'.format(kwd)), 'w', encoding='utf-8') as f:
        #     f.write(json.dumps(msg, ensure_ascii=False, indent=4))
        return msg
    else:
        return msg



if __name__ == '__main__':
    # kwd = '李涓子'
    # kwd = '迈凯伦'
    # kwd = '胡春明'
    # kwd = '刘知远'
    kwd = '刘志远'
    run(kwd)
