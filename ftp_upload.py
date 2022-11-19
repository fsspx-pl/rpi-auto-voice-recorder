from config import CONFIG_PATH, get_config
from ftplib import FTP

def upload(filepath):
    config = get_config(CONFIG_PATH)
    ftp_config = config['ftp']
    url = ftp_config["url"]
    user = ftp_config["user"]
    passwd = ftp_config["password"]
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