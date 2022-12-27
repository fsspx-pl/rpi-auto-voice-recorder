from config import get_config
from ftplib import FTP

def upload(filepath):
    config = get_config()['ftp']
    url = config['url']
    user = config['user']
    passwd = config['password']
    with FTP(host=url, user=user, passwd=passwd) as ftp:
        try:
            ftp.login()
        except:
            print("Error when logging into FTP. Are you already logged in?")
        finally:
            if(ftp):
                store_file(ftp, filepath)

def store_file(ftp, filepath):
    with open(filepath, "rb") as file:
        ftpCommand = "STOR %s" % filepath;
        ftp.storbinary(cmd=ftpCommand, fp=file)