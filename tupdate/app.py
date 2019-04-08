#coding:utf-8
#from .. import conf_list
import config
import install_pkt
from flask import Flask,request
import json
import time
import os
import re
import threading
import uuid
import requests
import cgi
from contextlib import closing
from  logset  import logger,initLog

app = Flask(__name__)


def get_mac_address():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])


class Update():
    #一般状态的初始化
    ST_INIT=0  #状态初始化

    #install_process 状态值
    ST_NOTINSTALL = 0 #未安装
    ST_INSTALLING = 1  #正在安装

    #install_status 状态值
    ST_NOTDOWN=0 #未下载
    ST_DOWNING =1 #下载中
    ST_DOWNSUCCESS =2 #下载完成
    ST_DOWNFAILED =3 #下载失败
    ST_INSTALLFINISH = 4 #安装完成
    ST_INSTALLFAIL = 5 #安装失败

    # install_auto 状态值
    ST_INSTALLBYAUTO=2 #自动安装
    ST_INSTALLBYUSER=1 #人工安装
    ST_FREE=0         #没自动安装，没人工安装



    def __init__(self):
        self.progress = self.ST_INIT  #下载进度
        self.install_progress = self.ST_NOTINSTALL
        self.install_status = self.ST_NOTDOWN
        self.install_auto = self.ST_FREE
        self.starttime = 3600
        self.msg=""
        self.success=False

    def get_state(self,version_type):
        if version_type == "code":
            state = 1
        elif version_type == "poc":
            state = 2
        elif version_type == "rule":
            state = 3
        else:
            state = 1
        return state

    def compare_versions(self):
        #if request.method == "POST":
            try:
                f = open(config.STATUS_FILE_PATH, 'r')
                content = json.loads(f.read())
                f.close()
                upgrade_url = content.get("upgrade_url", "")
                code_version = content.get("code_version", "")
                poc_version = content.get("poc_version", "")
                rule_version = content.get("rule_version", "")
                url = "%s/version/compare?code_version=%s&poc_version=%s&rule_version=%s" % (upgrade_url,code_version,poc_version,rule_version)
                logger.info(url)
                try:
                    res = requests.get(url,timeout=10,verify=False)
                    html = cgi.escape(res.text)
                    status = json.loads(html)
                    print status
                except:
                    status = {
                        "success":False,
                        "msg":"服务器连接失败！请检查网址是否正确！"
                    }
                is_update = status.get("is_update",0)
                success = status.get("success",False)
                scan_status = "STOP"  # 默认d01不在扫描状态
                '''
                try:
                    content = os.popen('td01_status_path').read().rstrip()
                    print('td01_status=======', content)
                    status_dict = json.loads(content.replace("'","\""))
                    scan_status = status_dict.get("status","STOP")
                except:
                    scan_status = "STOP"
                '''
                if scan_status == "RUNING":
                    content = {
                        "success":False,
                        "state":0,
                        "msg":"正在扫描资产中，无法获取升级状态！",
                        "version":""
                    }
                else:
                    if success:
                        if is_update == 1:
                            version = status.get("version","")
                            version_type = status.get("type","code")
                            state = self.get_state(version_type)
                            content = {
                                "success":True,
                                "state":state,
                                "msg":"",
                                "version":version,
                                "version_type":version_type,
                                "is_update": is_update,
                                "upgrade_url":upgrade_url,
                            }
                        elif is_update == 0 :
                            version_type = status.get("type","code")
                            state = self.get_state(version_type)
                            content = {
                                "success":False,
                                "state":state,
                                "version_type":version_type,
                                "msg":"版本还没有更新，请耐心等待！",
                                "version":""
                            }
                        else:
                            content = {
                                "success":False,
                                "state":0,
                                "msg":"更新状态获取失败！",
                                "version":""
                            }
                    else:
                        content = {
                            "success":False,
                            "state":0,
                            "msg":status.get("msg",""),
                            "version":"1.1"
                        }
            except Exception,e:
                logger.error(str(e))
                content = {
                    "success":False,
                    "state":0,
                    "msg":"获取版本对比信息失败!"
                }
            return json.dumps(content, encoding="UTF-8", ensure_ascii=False)


    def get_file(self,version,url,filename,version_type):
        """
        下载文件，并记录下载进度等内容
        :param url:
        :param filename:
        :return:
        """
        logger.info(version,url,filename,version_type)
        try:
            self.progress=self.ST_INIT
            self.install_status = self.ST_NOTDOWN
            update_path = url
            with closing(requests.get(url, stream=True)) as response:
                chunk_size = 1024
                content_size = int(response.headers['Content-Length'])
                content_disposition = response.headers['Content-Disposition']
                reg = re.search('filename=(?P<filename>[^\s]*)', content_disposition)
                if reg:
                    filename = reg.group("filename")
                else:
                    #get file failed
                    return 
                data_count = 0
                filename = os.path.join(config.UPDATE_PATH,filename)
                logger.info("download file store:"+filename)
                with open(filename, "wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        data_count = data_count + len(data)
                        #print(data_count)
                        self.progress = (float(data_count) / float(content_size)) * 100
                        self.progress=round(self.progress,3)
                        if self.progress == 100:
                            self.msg="下载阶段，下载成功!"
                            self.install_status=self.ST_DOWNSUCCESS
                        else:
                            self.install_status = self.ST_DOWNING
                            self.msg="下载阶段，下载中!"
            logger.info(self.msg, self.install_status)
            if self.progress != 100.0:
                self.msg = "下载阶段：下载失败!"
                self.install_status=self.ST_DOWNFAILED
                logger.info(self.msg, self.install_status)
                return
            try:
                logger.info("installing start!")
                self.msg = "安装阶段，安装中!"
                if install_pkt.td01_install_pkt(filename,version,version_type) ==True :
                    self.version = version
                    self.install_status = self.ST_INSTALLFINISH
                    self.msg = "安装阶段，安装成功!"

                else:
                    self.install_status = self.ST_INSTALLFAIL
                    self.msg = "安装阶段，安装失败!"

                logger.info("installing end!")
                logger.info(self.msg, self.install_status)
            except Exception,e:
                self.msg = "安装阶段，安装失败!"
                logger.error("install failure!" + str(e))
                self.install_status = self.ST_INSTALLFAIL
            self.install_progress = self.ST_INIT
        except Exception,e:
            logger.error(str(e))



    def download_progress(self):
        content = {
            "progress":str(self.progress)
        }
        return json.dumps(content,ensure_ascii=False)

    def download_file(self,upgrade_url,version_type,version):
            try:
                version = version
                version_type = version_type
                url = upgrade_url
                get_file_url = "%s/version/get_file?version=%s&type=%s" % (url,version,version_type)
                filename = "%s.zip" % version
                t = threading.Thread(target=self.get_file,args=(version,get_file_url,filename,version_type))
                t.start()
            except Exception,e:
                    self.install_status=self.ST_INSTALLFAIL
                    self.msg="无法正常安装！"


    def instauto(self):
        while True:
            time.sleep(self.starttime)
            if self.install_auto == self.ST_NOTINSTALL:
                self.install_auto = self.ST_INSTALLBYAUTO
                res = self.compare_versions()
                r = json.loads(res)
                state = r["success"]
                if state == True:
                    if self.install_progress == 0:
                        self.download_file()
                self.install_auto = self.ST_NOTINSTALL

@app.route('/compare',methods=['GET','POST'])
def compare():
    respones=tupdate1.compare_versions()
    print(respones)
    logger.info(respones)
    return respones

@app.route('/update',methods=['GET','POST'])
def tupdate():
    #check status
    logger.info(tupdate1.install_auto,tupdate1.install_progress)
    if tupdate1.install_auto!=tupdate1.ST_INSTALLBYAUTO :
        tupdate1.install_auto=tupdate1.ST_INSTALLBYUSER
        if tupdate1.install_progress == tupdate1.ST_NOTINSTALL:
            tupdate1.install_progress=tupdate1.ST_INSTALLING
            res = tupdate1.compare_versions()
            status = json.loads(res)
            tupdate1.success = status.get("success","")
            version_type=status.get("version_type","")
            version = status.get("version", "")
            upgrade_url=status.get("upgrade_url","")
            massage=status.get("msg","")
            logger.info(tupdate1.success,version_type,version,upgrade_url,massage)
            if tupdate1.success == True:
                tupdate1.msg = "开始升级中!"
                tupdate1.download_file(upgrade_url, version_type, version)
            else:
                tupdate1.msg=massage
                tupdate1.install_progress = tupdate1.ST_NOTINSTALL
        else:
            tupdate1.msg = "升级中，请勿操作!"
    else:
        tupdate1.msg= "系统自动安装中!"
    logger.debug(tupdate1.msg)
    tupdate1.install_auto = tupdate1.ST_INIT
    return json.dumps({
        "massage":tupdate1.msg
    },encoding="UTF-8", ensure_ascii=False)

@app.route('/status',methods=['GET','POST'])
def status():
    content = {
        "massage": tupdate1.msg,
        "install_status":tupdate1.install_status
    }
    logger.debug(content)
    return json.dumps(content,encoding="UTF-8", ensure_ascii=False)

tupdate1 = Update()
def tupdate_deamon():
    initLog()
    t = threading.Thread(target=tupdate1.instauto, args=())
    print ("main->",threading.currentThread().ident)
    t.start()
    app.run()
    
if  __name__ == '__main__':
    tupdate_deamon()
