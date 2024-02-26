import json
import operator

from filecmp import cmp

from jsonpath import jsonpath

from utils.connect_DB import SqlserverConnect
from utils.recordlog import logs


class AssertionMangement:

    def contain_assert(self, expected, response, status_code):
        assert_flag = 0

        for k, v in expected.items():
            if k == "status_code":
                if v != status_code:
                    assert_flag += 1
            else:
                response_list = jsonpath(response, f"$..{k}")
                if response_list:
                    response_list = "".join(response_list)
                    if v in response_list:
                        logs.info("字符串包含断言成功：预期结果-->%s；实际结果-->%s" % (expected, response))
                    else:
                        assert_flag += 1
                        logs.error("字符串包含断言失败：预期结果-->%s；实际结果-->%s" % (expected, response))
                else:
                    assert_flag += 1
                    logs.error("从接口相应中提取不到对应的断言内容，请检查断言字段是否包含在接口返回的内容中")

        return assert_flag

    def equal_assert(self, expected, response):
        assert_flag = 0
        result = None
        response_key_list = []
        if isinstance(expected, dict) and isinstance(response, dict):
            for key,value in response.items():
                if list(expected.keys())[0] !=key:
                    response_key_list.append(key)
            for key in response_key_list:
                del response[key]
            result = (operator.eq(expected, response))
            if result:
                logs.info(f"相等断言成功：接口实际结果{response}，等于预期结果：" + str(expected))
            else:
                assert_flag += 1
                logs.error(f"相等断言失败：接口实际结果{response}，不等于预期结果：" + str(expected))
        else:
            raise TypeError('相等断言--类型错误，预期结果和接口实际响应结果必须为字典类型！')

        return assert_flag

    def db_assert(self, expected, response):
        connect = SqlserverConnect()
        assert_flag = 0
        db_result = None
        try:
            for sql, key in expected.items():
                db_result = connect.query(sql)
            real_result = jsonpath(response, f"$..{key}")[0]
            if db_result:
                for result_key, result_value in db_result.items():
                    if str(result_value) == str(real_result):
                        logs.info(f"sql断言成功：接口实际结果{real_result}，等于数据库的预期结果：" + str(result_value))
                    else:
                        assert_flag += 1
                        logs.error(f"sql断言失败：接口实际结果{real_result}，不等于数据库的预期结果：" + str(result_value))
            else:
                assert_flag += 1
                logs.error("sql有语法错误或者其他错误")
        except Exception as e:
            assert_flag += 1
            logs.error(f"SQL断言失败，异常信息：{e}")
        return assert_flag

    def assert_result(self, expected: list, response: dict, status_code=200):
        all_assert_flag = 0
        try:
            for yq in expected:
                for k, v in yq.items():
                    if k == "contains":
                        all_assert_flag = all_assert_flag + self.contain_assert(v, response, status_code)
                    elif k == "equals":
                        all_assert_flag = all_assert_flag + self.equal_assert(v, response)
                    elif k == "sql":
                        all_assert_flag = all_assert_flag + self.db_assert(json.loads(v), response)
        except Exception as e:
            logs.info("请检查断言字段是否包含在接口返回的内容中")
            logs.info(f"异常信息:{e}")
            raise e

        if all_assert_flag == 0:
            logs.info('断言正常，测试成功')
            assert True
        if all_assert_flag !=0:
            logs.error('断言错误，测试失败')
            assert False


if __name__ == '__main__':
    assertion = AssertionMangement()
    sql = [{
        "sql": "{\" select 开票机号 from 销项发票 where 发票GUID='3d980d9f-6cb4-407c-89d1-86030be8fe98' \": \"msg_code\"}"
    }
    ]
    sql_exp = [{
        'sql': '{"\' select 开票机号 from 销项发票 where 发票GUID=\"3d980d9f-6cb4-407c-89d1-86030be8fe98\"  \' ": "msg_code"}'}]
    expected1 = [{"contains": "{'msg': '登录成功'}"}]
    response1 = {'error_code': None, 'msg': '登录成功', 'msg_code': "200", 'orgId': '4140913758110176843',
                 'token': '6FCB5A3a360D08445B9Ae0B41CEbf', 'userId': '2013060194418209567'}
    # print(assertion.contain_assert(expected, response,200))
    expected2 = [{"equals": "{'msg': '登录成功'}"}]
    response2 = {'msg': '登录成功'}
    assertion.assert_result(expected1, response1)
    assertion.assert_result(sql, response1)
    assertion.assert_result(expected2, response1)
