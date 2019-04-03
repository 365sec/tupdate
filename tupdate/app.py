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
    ST_OTHER=0
    ST_DOWNLOAD = 1
    ST_INSTALL=2
    ST_COMPLETE=3


    def __init__(self):
        self.progress = 0
        self.download_status = True
        self.install_progress = 0
        self.install_status = 0
        self.install_auto = 0
        self.status=self.ST_OTHER
        self.starttime = 300


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
                                "upgrade_url":upgrade_url
                            }
                        elif is_update == 0 :
                            version_type = status.get("type","code")
                            state = self.get_state(version_type)
                            content = {
                                "success":False,
                                "state":state,
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
                            "version":"1.1888"
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
        try:
            update_path = url
            self.download_status = True
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
                        self.progress = (data_count / content_size) * 100
            
            self.progress = 100
            print(self.progress)
            try:
                self.install_progress = 0
                logger.info("installing start!")
                if install_pkt.td01_install_pkt(filename,version,version_type) ==True:
                    self.version = version
                    self.install_status = 2
                else:
                    self.install_status = 3
                logger.info("installing end!")
            except Exception,e:
                logger.error("install failure!" + str(e))
                self.install_status = 3
                
        except Exception,e:
            print str(e)
            logger.error(str(e))
            self.download_status = False


    def download_progress(self):
        content = {
            "success":self.download_status,
            "progress":str(self.progress)
        }
        return json.dumps(content,ensure_ascii=False)

    #def td01_install_pkt(update_file,update_info,update_version,update_type,update_status):
    def download_file(self,upgrade_url,version_type,version):
            try:
                version = version
                version_type = version_type
                url = upgrade_url
                get_file_url = "%s/version/get_file?version=%s&type=%s" % (url,version,version_type)
                filename = "%s.zip" % version
                self.install_progress = 1
                print('---------->',self.install_progress)
                t = threading.Thread(target=self.get_file,args=(version,get_file_url,filename,version_type))
                t.start()
                t.join()
                print('---------->', self.install_progress)
                self.install_progress = 2
                content = {
                    "success": True,
                    "msg": "升级成功"
                }
            except Exception,e:
                print str(e)
                logger.error(str(e))
                content = {
                    "success":False,
                    "msg":"下载失败！"
                }
            return json.dumps(content, encoding="UTF-8", ensure_ascii=False)

    def get_upgrade_status(self):
        status = str(self.install_status)
        print(status)
        progress = "100" if self.install_status == 2 else "0"
        content = {
            "status": status,
            "progress": progress,
            "failure":""
        }
        # if progress == "100":
        #     try:
        #         print self.version
        #         f = open(status_path,"rb")
        #         statud_dict = json.loads(f.read())
        #         f.close()
        #         statud_dict["version"] = self.version
        #         fw = open(status_path,"wb")
        #         fw.write(json.dumps(statud_dict,ensure_ascii=False))
        #         fw.close()
        #     except Exception,e:
        #         print str(e)
        return json.dumps(content, encoding="UTF-8", ensure_ascii=False)


    def instauto(self):
        while True:
            xtime=self.starttime
            for s in range(300,0,-1):

                if tupdate1.install_auto == 0 and s==1:
                    tupdate1.install_auto = 2
                    res = tupdate1.compare_versions()

                    r = json.loads(res)
                    state = r["success"]
                    if state == True:
                        if tupdate1.install_progress == 0:
                            tupdate1.download_file()

                time.sleep(1)
                #print('+++>',threading.currentThread().ident, s)


            tupdate1.install_auto = 0



@app.route('/compare',methods=['GET','POST'])
def compare():

    respones=tupdate1.compare_versions()
    print(respones)
    logger.debug(respones)
    logger.info(respones)
    return respones

@app.route('/update',methods=['GET','POST'])
def tupdate():
    #check status
    if tupdate1.install_auto!=2:
        tupdate1.install_auto=1
        res = tupdate1.compare_versions()
        status = json.loads(res)
        success = status["success"]
        version_type=status.get("version_type","")
        version = status.get("version", "")
        upgrade_url=status.get("upgrade_url","")
        if success == True:
            if tupdate1.install_progress == 0:
                tupdate1.download_file(upgrade_url,version_type,version)
                content={
                        "success":True,
                        "progress":tupdate1.progress,
                        "download_status":tupdate1.download_status,
                        "install_progress":tupdate1.install_progress,
                        "install_status":tupdate1.install_status,
                        "install_auto":tupdate1.install_auto,
                        "status":tupdate1.status,
                        "starttime":tupdate1.starttime,
                        "msg":"开始升级"
                           }
                respones=json.dumps(content, encoding="UTF-8", ensure_ascii=False)
                logger.info(respones)
            elif tupdate1.install_progress==1:
                content={
                            "success":True,
                            "progress":tupdate1.progress,
                            "download_status":tupdate1.download_status,
                            "install_progress":tupdate1.install_progress,
                            "install_status":tupdate1.install_status,
                            "install_auto":tupdate1.install_auto,
                            "status":tupdate1.status,
                            "starttime":tupdate1.starttime,
                            "msg":"正在安装，请勿操作"
                        }
                respones = json.dumps(content, encoding="UTF-8", ensure_ascii=False)
            else:
                if tupdate1.install_status==2:
                    content ={
                                "success":True,
                                "progress":tupdate1.progress,
                                "download_status":tupdate1.download_status,
                                "install_progress":tupdate1.install_progress,
                                "install_status":tupdate1.install_status,
                                "install_auto":tupdate1.install_auto,
                                "status":tupdate1.status,
                                "starttime":tupdate1.starttime,
                                "msg": "安装完成"
                     }
                    tupdate1.install_status=0
                elif tupdate1.install_status==3:
                    content = {
                        "success": True,
                        "progress": tupdate1.progress,
                        "download_status": tupdate1.download_status,
                        "install_progress": tupdate1.install_progress,
                        "install_status": tupdate1.install_status,
                        "install_auto": tupdate1.install_auto,
                        "status": tupdate1.status,
                        "starttime": tupdate1.starttime,
                        "msg": "安装失败"
                    }
                else :
                    content = {
                        "success": True,
                        "progress": tupdate1.progress,
                        "download_status": tupdate1.download_status,
                        "install_progress": tupdate1.install_progress,
                        "install_status": tupdate1.install_status,
                        "install_auto": tupdate1.install_auto,
                        "status": tupdate1.status,
                        "starttime": tupdate1.starttime,
                        "msg": "安装失败"
                    }
                tupdate1.install_progress = 0
                respones = json.dumps(content, encoding="UTF-8", ensure_ascii=False)
        else:
            respones =res
        tupdate1.install_auto = 0
    else:
        content = {
            "success":True,
                            "progress":tupdate1.progress,
                            "download_status":tupdate1.download_status,
                            "install_progress":tupdate1.install_progress,
                            "install_status":tupdate1.install_status,
                            "install_auto":tupdate1.install_auto,
                            "status":tupdate1.status,
                            "starttime":tupdate1.starttime,
                             "msg": "自动安装，请勿操作"
        }
        respones = json.dumps(content, encoding="UTF-8", ensure_ascii=False)
    logger.debug(respones)
    return respones
@app.route('/status',methods=['GET','POST'])
def status():
    respones=tupdate1.get_upgrade_status()
    return respones

tupdate1 = Update()
def tupdate_deamon():
    initLog()
    t = threading.Thread(target=tupdate1.instauto, args=())
    print ("main->",threading.currentThread().ident)
    t.start()
    app.run()
    
if  __name__ == '__main__':
    tupdate_deamon()
'''
    log = Logger('/all.log',level='debug')
    log.logger.debug('debug')
    log.logger.info('info')
    log.logger.warning('警告')
    log.logger.error('报错')
    log.logger.critical('严重')
    Logger('error.log', level='error').logger.error('error')
'''