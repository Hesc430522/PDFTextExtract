import sys
import uuid
import requests
import hashlib
import json
import time
import pdfplumber
import jieba
from collections import Counter
from string import digits
from imp import reload

def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()

def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

def PdfIdentifyText(pdffile):
    PdfContent = ""

    # 利用pdfplumber提取文字
    with pdfplumber.open(pdffile) as pdf: 
        for temp in pdf.pages:
            PdfContent += temp.extract_text()

    # 使用jieba将全文分割，并将大于两个字的词语放入列表
    tokens = jieba.cut(PdfContent) 
    return Counter(tokens).most_common()

def tranRequest(query_word):
    reload(sys)

    YOUDAO_URL = 'https://openapi.youdao.com/api'
    APP_KEY = ''    # 有道云app key
    APP_SECRET = '' # 有道云app secret
    data = {}

    q = query_word
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data['from'] = 'en'
    data['to'] = 'zh-CHS'
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['q'] = q
    data['salt'] = salt
    data['sign'] = sign

    # data['vocabId'] = "您的用户词表ID"
    retult = requests.post(YOUDAO_URL, data=data, headers=headers)
    
    # 保存单词MP3 音频
    contentType = retult.headers['Content-Type']
    if contentType == "audio/mp3":
        millis = int(round(time.time() * 1000))
        filePath = "./file/" + str(millis) + ".mp3"
        fo = open(filePath, 'wb')
        fo.write(retult.content)
        fo.close()
    else:
        return json.loads(retult.text)

# 将结果保存到csv文件中
def ToCsvFile(data):
    data = data["count"]+ "," + data["EnglishWord"] + "," + data["EnglishExplains"]+'\r\n'

    # 文件写入
    TocsvFile.write(data.encode()) 

def DataClea(data):
    for temp in data:
        if len(temp[0].translate(str.maketrans('', '', digits))) > 1:

            # 创建请求获取单词注释
            tranRequestContent = tranRequest(temp[0]) 
            dictWord = {}
            dictWord["count"] = str(temp[1])

            # 查询英文单词
            dictWord["EnglishWord"]  = tranRequestContent["query"].lower() 
            try:
                # 中文注释
                dictWord["EnglishExplains"] = "||".join(tranRequestContent["basic"]["explains"]) 
            except:
                print(tranRequestContent["query"].lower() + '单词翻译出错!')
                dictWord["EnglishExplains"] = " "
            ToCsvFile(dictWord)

if __name__ == '__main__':

    pdfFile = "" # 需要翻译的PDF文件
    csvFile = "" # 单词保存的CSV文件

    # 打开csv文件
    TocsvFile = open(csvFile, "wb")  

    PdfTextContent = PdfIdentifyText(pdfFile)
    DataClea(PdfTextContent) 

    # 关闭csv文件
    TocsvFile.close() 