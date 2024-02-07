import json

import jsonpath
import yaml
from config.setting import extract_yanl_path
from utils.recordlog import logs
import re


def extract_data(testdata_extract_expression, response):
    '''
    提取接口的返回值，支持正则表达式和json提取器
    :param testdata_extract_expression:testcase文件yaml中的extract值
    :param response:接口的实际返回值
    :return:
    '''
    try:
        pattern_lst = ['(.*?)', '(.+?)', r'(\d)', r'(\d*)']
        for key, value in testdata_extract_expression.items():

            # 处理正则表达式提取
            for pat in pattern_lst:
                if pat in value:
                    ext_lst = re.search(str(value), str(response))
                    if pat in [r'(\d+)', r'(\d*)']:
                        extract_data = {key: int(ext_lst.group(1))}
                        logs.info('提取接口的返回值：{}'.format(extract_data))
                    else:
                        extract_data = {key: ext_lst.group(1)}
                        logs.info('提取接口的返回值：{}'.format(extract_data))
                    write_extract_yaml(extract_data)
            # 处理json提取参数
            if '$' in value:
                ext_json = jsonpath.jsonpath(response, value)[0]
                if ext_json:
                    extarct_data = {key: ext_json}
                    logs.info('提取接口的返回值：{}'.format(extarct_data))
                else:
                    extarct_data = {key: '未提取到数据，请检查接口返回值是否为空！'}
                    logs.info('提取接口的返回值：{}'.format(extarct_data))
                write_extract_yaml(extarct_data)
    except Exception as e:
        logs.error(e)


def write_extract_yaml(data, extract_yanl_path=extract_yanl_path):
    '''
    将提取到的变量写入extract_yanl_path文件中
    :param data: 要写入的数据
    :param extract_yanl_path: 保存提取变量的文件路径
    :return:
    '''
    try:
        if isinstance(data, dict):
            with open(extract_yanl_path, 'a', encoding="utf-8") as f:
                data = yaml.dump(data, allow_unicode=True)
                f.write(data)
        else:
            print('写入到[extract_yanl_path.yaml]的数据必须是字典类型格式！')
    except Exception as e:
        logs.info(e)


if __name__ == '__main__':
    exp = {"token": "'token': '(.*?)'"}
    response = r"{'orgId': '4140913758110176843','token': '啊啊啊aD2EFABD3DC2d2Aa361c87bdcaAba啊啊啊'}"
    print(extract_data(exp, response))


    # exp = {"token": "$.token"}
    # response = {"token": "aD2EFABD3DC2d2Aa361c87bdcaAba"}
    # print(extract_data(exp, response))
