import paramiko
import os,json
import random, hashlib, urllib, http.client
import requests, time


def uploadFile(local, remote, host="lfs.aminer.cn", port=23333, user='ftp', password='F58StU8tO1j5J5hI2Xm0Q2qmZIw8TIox'):
    sf = paramiko.Transport((host, port))
    sf.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(sf)
    try:
        sftp.put(local, remote)
    except:
        print('Upload Error!!!')
    sf.close()

def downloadFile(remote, local, host="lfs.aminer.cn", port=23333, user='ftp', password='F58StU8tO1j5J5hI2Xm0Q2qmZIw8TIox'):
    sf = paramiko.Transport((host, port))
    sf.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(sf)
    try:
        sftp.get(remote, local)
    except:
        print('Downloads Error!!!')
    sf.close()

def baidu_translate(text, from_lang, to_lang):
    uti_result = ''
    appid = '20200519000462270'  # 填写你的appid
    secretKey = 'khqpWWLZIcQ9efjMMpOT'  # 填写你的密钥
    httpClient = None
    myurl = '/api/trans/vip/translate'
    fromLang, toLang = from_lang, to_lang  # 原文语种, 译文语种
    salt = random.randint(32768, 65536)
    sign = appid + text + str(salt) + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(
        text) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
        salt) + '&sign=' + sign
    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
        httpClient.request('GET', myurl)
        # response是HTTPResponse对象
        response = httpClient.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)
        uti_result = result.get('trans_result')[0].get('dst')
    except Exception as e:
        pass
    finally:
        if httpClient:
            httpClient.close()
    return uti_result


def youdao_translate(text, input_type):
    url = "http://fanyi.youdao.com/translate"
    if type(text) == list:
        src = ",".join(text)
    else:
        src = text
    data = {
        "doctype": "json",
        "type": input_type,
        "i": src,
    }
    rs = requests.get(url=url, params=data)
    try:
        trans_data = rs.json()["translateResult"]
        tgt = [t["tgt"] for t in trans_data[0]]
        time.sleep(3)
        return tgt
    except Exception:
        # print("There is an error in translation")
        return text




if __name__ == '__main__':
    # uploadFile('code/test.xls', '/misc/Drop_Covid/test.xls', 'put')
    uploadFile('test.xls', '/misc/Drop_Covid/test.xls', 'get')
