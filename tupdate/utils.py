#coding:utf-8
import os, zipfile

def rc4(data, key):
    """RC4 encryption and decryption method."""
    S, j, out = list(range(256)), 0, []

    for i in range(256):
        j = (j + S[i] + ord(key[i % len(key)])) % 256
        S[i], S[j] = S[j], S[i]

    i = j = 0
    for ch in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(chr(ord(ch) ^ S[(S[i] + S[j]) % 256]))

    return "".join(out)

def rc4Encrypt(srcpath,dstpath,key):
    finput=open(srcpath,"rb")
    data=finput.read()
    out = rc4(data, key)
    finput.close()
    
    foutput=open(srcpath,"wb")
    foutput.write(out)
    foutput.close()

    
    
def rc4Decrypt(srcpath,dstpath,key):
   return rc4Encrypt(srcpath,dstpath,key)


#打包目录为zip文件（未压缩）
def make_zip(source_dir, output_filename):
  zipf = zipfile.ZipFile(output_filename, 'w')
  pre_len = len(os.path.dirname(source_dir))
  print os.path.dirname(source_dir)
  for parent, dirnames, filenames in os.walk(source_dir):
    for filename in filenames:
      print parent,filename
      pathfile = os.path.join(parent, filename)
      arcname = pathfile[pre_len:].strip(os.path.sep)   #相对路径
      print "arcname->",arcname
      zipf.write(pathfile, arcname)
  zipf.close()
  
def un_zip(file_name,dst_dir):
    """unzip zip file"""
    zip_file = zipfile.ZipFile(file_name)
    if os.path.isdir(dst_dir):
        pass
    else:
        os.mkdir(dst_dir)
    for names in zip_file.namelist():
        zip_file.extract(names,dst_dir)
    zip_file.close()

  
if __name__ == "__main__":
    buf = rc4("Hello World", "rc4")
    print rc4(buf, "rc4")