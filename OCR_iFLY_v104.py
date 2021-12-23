#!/usr/bin/env python 
# -*- coding:utf-8 -*-

### 讯飞公式识别模块，基于官方接口文档开发
# 接口文档：https://www.xfyun.cn/doc/words/formula-discern/API.html
# 错误码查询：https://www.xfyun.cn/document/error-code （错误码code为5位数字）

import requests
import datetime
import hashlib
import base64
import hmac
import json
import re ### 正则表达式处理
import configparser ### 读写配置文件包
import os
import sys

### 注意：使用 PyInstaller 进行打包时，配置文件路径的定义，与调试时不同。
### 使用 Python IDE 调试时，需要注释掉第二行，使第一行命令生效；而使用 PyInstaller 进行打包时，需要注释掉第一行，使第二行命令生效。
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) ### 用于读写配置文件的全局路径
#BASE_DIR = os.path.dirname(sys.executable) ### 用于读写配置文件的全局路径

class get_result(object):
    def __init__(self,host):
        # 从配置文件加载 API 值
        self.conf = configparser.ConfigParser()  # 加载现有配置文件
        self.conf.read(os.path.join(BASE_DIR, 'config.ini'), encoding="utf-8-sig")  # 从全局路径读取配置文件
        # 应用 ID（到控制台获取）
        self.APPID = self.conf.get('API_iFLY', 'APPID')
        # 接口 APISercet（到控制台公式识别服务页面获取）
        self.Secret = self.conf.get('API_iFLY', 'APISecret')
        # 接口 APIKey（到控制台公式识别服务页面获取）
        self.APIKey= self.conf.get('API_iFLY', 'APIKey')

        # POST 请求内容
        self.Host = host
        self.RequestUri = "/v2/itr"
        # 设置url
        self.url="https://"+host+self.RequestUri
        self.HttpMethod = "POST"
        self.Algorithm = "hmac-sha256"
        self.HttpProto = "HTTP/1.1"

        # 设置当前时间
        curTime_utc = datetime.datetime.utcnow()
        self.Date = self.httpdate(curTime_utc)
        # 设置测试图片文件
        self.conf = configparser.ConfigParser()  # 加载现有配置文件
        self.conf.read(os.path.join(BASE_DIR, 'config.ini'),encoding="utf-8-sig") # 从全局路径读取配置文件
        self.AudioPath = self.conf.get('img_Location', 'DOC')
        self.BusinessArgs={
                "ent": "teach-photo-print",
                "aue": "raw",
            }

    def imgRead(self, path):
        with open(path, 'rb') as fo:
            return fo.read()

    def hashlib_256(self, res):
        m = hashlib.sha256(bytes(res.encode(encoding='utf-8'))).digest()
        result = "SHA-256=" + base64.b64encode(m).decode(encoding='utf-8')
        return result

    def httpdate(self, dt):
        """
        Return a string representation of a date according to RFC 1123
        (HTTP/1.1).

        The supplied date must be in UTC.

        """
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                 "Oct", "Nov", "Dec"][dt.month - 1]
        return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month,
                                                        dt.year, dt.hour, dt.minute, dt.second)

    def generateSignature(self, digest):
        signatureStr = "host: " + self.Host + "\n"
        signatureStr += "date: " + self.Date + "\n"
        signatureStr += self.HttpMethod + " " + self.RequestUri \
                        + " " + self.HttpProto + "\n"
        signatureStr += "digest: " + digest
        signature = hmac.new(bytes(self.Secret.encode(encoding='utf-8')),
                             bytes(signatureStr.encode(encoding='utf-8')),
                             digestmod=hashlib.sha256).digest()
        result = base64.b64encode(signature)
        return result.decode(encoding='utf-8')

    def init_header(self, data):
        digest = self.hashlib_256(data)
        #print(digest)
        sign = self.generateSignature(digest)
        authHeader = 'api_key="%s", algorithm="%s", ' \
                     'headers="host date request-line digest", ' \
                     'signature="%s"' \
                     % (self.APIKey, self.Algorithm, sign)
        #print(authHeader)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Method": "POST",
            "Host": self.Host,
            "Date": self.Date,
            "Digest": digest,
            "Authorization": authHeader
        }
        return headers

    def get_body(self):
        audioData = self.imgRead((self.AudioPath))
        content = base64.b64encode(audioData).decode(encoding='utf-8')
        postdata = {
            "common": {"app_id": self.APPID},
            "business": self.BusinessArgs,
            "data": {
                "image": content,
            }
        }
        body = json.dumps(postdata)
        #print(body)
        return body

    def call_url(self): # 返回值：公式识别结果字符串，如果无法识别则返回错误信息。
        if self.APPID == '' or self.APIKey == '' or self.Secret == '':
            final_output = "错误：Appid 、APIKey 或 APISecret 为空！请在设置中填写相关信息。"
        else:
            code = 0
            body=self.get_body()
            headers=self.init_header(body)
            ### request 执行异常处理
            try:
                response = requests.post(self.url, data=body, headers=headers,timeout=8)
            except:
                request_ERRmsg="错误：request 请求异常，并且没有返回状态码。可能是没有连接到网络。"
                return request_ERRmsg
            ### request 成功则继续执行
            status_code = response.status_code
            #print(response.content)
            if status_code!=200:
                # 鉴权失败
                final_output = "错误：Http 请求失败，状态码：" + str(status_code) + "，错误信息：" + response.text
            else:
                # 鉴权成功
                respData = json.loads(response.text)
                print(respData) ###调试：输出原始 JSON 文本

                ### 处理 JSON 文本 ###
                formula_list = re.findall('"recog": {"content": "(.*?)", "element"', json.dumps(respData, ensure_ascii=False)) # 正则表达式匹配公式文本,生成一个列表。设置 ensure_ascii=False，可以使公式图片中的中文字符能够正常识别
                output_formula = ['']  # 初始化输出列表，长度比列表数据多 1 位
                for length in range(len(formula_list)+1):
                    output_formula.append('')

                for i in range (0,len(formula_list)):
                    origin_formula = formula_list[i] # 取出列表中每个公式
                    #print(origin_formula) # [调试] 输出原始公式字符串
                    # 对公式字符串进行修饰
                    cut_down_1 = origin_formula.replace("\\\\","\\") # 修正多余的双斜线
                    cut_down_2 = cut_down_1.replace(" ifly-latex-begin", "").replace(" ifly-latex-end", "") # 去掉 latex-begin 和 end 标识符
                    output_formula[i] = cut_down_2.replace("^ {", "^{").replace("_ {", "_{") # 去掉元素间影响观感的多余空格（不去掉也没关系）

                # 最终结果
                #print("公式",i + 1,": ",output_formula) ### [调试] 打印输出
                final_output = '\n'.join(output_formula) # 合并列表中的元素

                # 以下仅用于调试
                code = str(respData["code"])
                if code!='0':
                    final_output = "识别失败，错误码：" + code + "\n" + "请前往 https://www.xfyun.cn/document/error-code?code=" + code + "查询解决办法"

        print(final_output)
        return final_output

