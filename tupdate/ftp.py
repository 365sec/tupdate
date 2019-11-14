#!usr/bin/env python
# -*- coding:utf-8 -*-
import ftplib
import os
import socket
from ftplib import FTP
 
import sys

 

#ftp.set_debuglevel(2)
 
class Ftp():

    def __init__(self):
        self.ftp = FTP()
 
    def connect_ftp(self,host, port, user, passwd):
        try:
            self.ftp.connect(host=host, port=port)  
        except(socket.error, socket.gaierror), e:
            print host 
            raise e
        try:
            self.ftp.login(user=user, passwd=passwd)
        except(ftplib.error_perm), e:
            raise e
            
     

    def cat_dir(self,filepath):
        cat = self.ftp.dir(filepath)
        return cat
     
 
    def make_dir(self,filepath):
        try:
            mkd = self.ftp.mkd(filepath)  
            return mkd
 
        except (ftplib.error_perm), e:
            print e
            
            
    def cwd(self,remotepath):
       self.ftp.cwd(remotepath)
       
       
    def remove_dir(self,dirname):
        try:
            self.ftp.rmd(dirname)
        except (ftplib.error_perm), e:
            print(e)
 
 

    def downloadfile(self,localpath, filename):
        bufsize = 1024  
        file_handler=None
        try:
            filepath=os.path.join(localpath,filename)
            file_handler = open(filepath, "wb")
            self.ftp.retrbinary("RETR %s" % (filename), file_handler.write, bufsize)
            return filepath
        except Exception as e:
            print e
            raise e
        finally:
            if file_handler!=None:
                file_handler.close()
 
    def delete(self,filename):
        self.ftp.delete(filename)
 
 
    def upload(self,localpath):
        bufsize = 8192
        file_handler = None
        try:
            file_handler = open(localpath, "rb")
            filename = os.path.split(localpath)[-1]
            self.ftp.storbinary("stor %s" % (filename), file_handler, bufsize)
        except Exception as e:
            print str(e)
        finally:
            if file_handler != None:
                file_handler.close()       
 
    def lst_file(self):
        s=[]
        try:
            for name in self.ftp.nlst():
                s.append(name)
            return s
        except Exception as e:
            print  e
            raise e
     
    def close(self):
        self.ftp.quit()


#
# if __name__ == "__main__":
#     #in  155.133.10.187
#     #out 192.168.30.10 grxa_scy/grxa@2018
#     print os.path.join("/guangzhang/","sf.tet")
#     #connect_ftp("192.168.30.10",21,"grxa_scy","grxa@2018")
#
#     #(host, port, user, passwd,timeout="10"):