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
    ST_INIT=0
    ST_OTHER=0
    ST_DOWNLOAD = 1
    ST_INSTALL=2
    ST_COMPLETE=3
    ST_NOTINSTALL = 0
    ST_INSTALLING = 1
    ST_INSTALLFINISH = 2
    ST_INSTALLFAIL = 3
    ST_INSTALLBYAUTO=2
    ST_INSTALLBYUSER=1



    def __init__(self):
        self.progress = self.ST_INIT
        self.download_status = False
        self.install_progress = self.ST_INIT
        self.install_status = self.ST_INIT
        self.install_auto = self.ST_INIT
        self.status=self.ST_INIT
        self.starttime = 300
        self.msg=""
        self.success=False


    def makecontent(self):
        self.content = {
            "success": self.success,        #是否允许更新
            "progress": self.progress,     #下载进度
            "download_status": self.download_status,    #下载状态
            "install_progress": self.install_progress,
            "install_status": self.install_status,
            "install_auto": self.install_auto,
            "status": self.status,
            "starttime": self.starttime,
            "msg": self.msg
        }


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
            self.progress=0
            update_path = url
            self.download_status = True
            with closing(requests.get(url, stream=True)) as response:
                chunk_size = 1024
                content_size = int(response.headers['Content-Length'])
                print(content_size)
                content_disposition = response.headers['Content-Disposition']
                reg = re.search('filename=(?P<filename>[^\s]*)', content_disposition)
                if reg:
                    filename = reg.group("filename")
                else:
                    #get file failed
                    return 
                data_count = self.ST_INIT
                filename = os.path.join(config.UPDATE_PATH,filename)
                logger.info("download file store:"+filename)
                with open(filename, "wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        data_count = data_count + len(data)
                        #print(data_count)
                        self.progress = (float(data_count) / float(content_size)) * 100
                        self.progress=round(self.progress,3)

            try:

                logger.info("installing start!")

                if install_pkt.td01_install_pkt(filename,version,version_type) ==True and self.progress ==100.0 :
                    self.version = version
                    self.install_status = 2
                else:
                    self.install_status = 3
                logger.info("installing end!")
            except Exception,e:
                logger.error("install failure!" + str(e))
                self.install_status = 3
            self.install_progress = self.ST_INIT
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
                if self.install_progress ==  self.ST_NOTINSTALL:
                    t = threading.Thread(target=self.get_file,args=(version,get_file_url,filename,version_type))
                    t.start()
                content = {
                    "success": True
                }
            except Exception,e:
                    self.msg="下载失败！"

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
            for runtime in range(300,0,-1):

                if tupdate1.install_auto == tupdate1.ST_NOTINSTALL and runtime==1:
                    tupdate1.install_auto = tupdate1.ST_INSTALLBYAUTO
                    res = tupdate1.compare_versions()
                    r = json.loads(res)
                    state = r["success"]
                    if state == True:
                        if tupdate1.install_progress == 0:
                            tupdate1.download_file()

                time.sleep(1)
                #print('+++>',threading.currentThread().ident, s)


            tupdate1.install_auto = self.ST_INIT



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
    if tupdate1.install_auto!=tupdate1.ST_INSTALLBYAUTO:
        tupdate1.install_auto=tupdate1.ST_INSTALLBYUSER
        res = tupdate1.compare_versions()
        status = json.loads(res)
        tupdate1.success = status["success"]
        version_type=status.get("version_type","")
        version = status.get("version", "")
        upgrade_url=status.get("upgrade_url","")

        if tupdate1.success == True:
            if tupdate1.install_status==0:
                if tupdate1.install_progress == tupdate1.ST_NOTINSTALL:
                    tupdate1.download_file(upgrade_url,version_type,version)
                    tupdate1.install_progress = tupdate1.ST_INSTALLBYUSER
                    tupdate1.msg="开始升级"
                    tupdate1.makecontent()
                    respones=json.dumps(tupdate1.content, encoding="UTF-8", ensure_ascii=False)
                    logger.info(respones)
                elif tupdate1.install_progress==tupdate1.ST_INSTALLING:
                    tupdate1.msg = "升级中，请勿操作"
                    tupdate1.makecontent()
                    respones = json.dumps(tupdate1.content, encoding="UTF-8", ensure_ascii=False)
            else:
                if tupdate1.install_status==tupdate1.ST_INSTALLFINISH:
                    tupdate1.msg="安装成功"
                    tupdate1.makecontent()
                elif tupdate1.install_status==tupdate1.ST_INSTALLFAIL:
                        tupdate1.msg="安装失败"
                tupdate1.makecontent()
                tupdate1.install_status = tupdate1.ST_INIT
                respones = json.dumps(tupdate1.content, encoding="UTF-8", ensure_ascii=False)
        else:
            respones =res
        tupdate1.install_auto = tupdate1.ST_INIT
    else:
        tupdate1.msg= "自动安装，请勿操作"
        tupdate1.makecontent()
        respones = json.dumps(tupdate1.content, encoding="UTF-8", ensure_ascii=False)
    logger.debug(respones)
    tupdate1.msg=""
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