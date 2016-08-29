#!/usr/bin/env python

import uuid
import time
from datetime import datetime
from hashlib import md5
from db import MongoDB

def digest(string):
    return md5(string).hexdigest()

class AuthApi:
    def __init__(self):
        try:
            self.mongo = MongoDB()
        except RuntimeError:
            printf('\nERROR: MongoDB server unreachable, exit')
            return
    
    def registerDev(self, uname, upasswd):
        if self.mongo.queryUserExist(uname, upasswd):
           return False, 'Error: user exists' 
        self.mongo.insertUserInfo(1,(uname,upasswd))
        return True, 'Info: success'

    def createApp(self, app_name, app_type, service_name):
        app_key = uuid.uuid1().hex
        app_id = uuid.uuid4().hex[2:12]
        app_secret = digest(app_key)
        if self.mongo.queryAppIDExist(app_id):
            return False, 'Error: app exists'
        self.mongo.insertAppsInfo(1,(app_name, app_type, service_name, app_id, app_key, app_secret))
        return app_id, app_key, app_secret

    def genToken(self, grant_type, app_id, app_key_secret):
        token = digest(app_id + app_key_secret + time.asctime())
        _, _, start, expire = self.mongo.updateAppInfo(app_id, token)
        return token, start, expire

    def refreshToken(self, grant_type, app_id, app_key_secret, token):
        cursor = self.mongo.apps.find({'appid':app_id, 'appsecret': app_key_secret, 'accesstoken': token})
        if cursor.count() == 0:
            return False, 'Error: token not exist', None, None
        for app in cursor:
            if app['expiretime'] > time.mktime(datetime.now().timetuple()):
                return False, 'Error: token not expire', None, None
        new_token, start, expire = self.genToken(grant_type, app_id, app_key_secret)
        return True, 'refresh token successed', new_token, expire
        
    def isTokenValid(self, token):
        cursor = self.mongo.apps.find({'accesstoken':token})
        if cursor.count() == 0:
            return False
        for i in cursor:
            if i['expiretime'] > time.mktime(datetime.now().timetuple()):
                return True
        return False

def main():
    cc = AuthApi()
    cc.registerDev('jennie','901234')
    print cc.registerDev('jennie', '901234')
    #cc.mongo.deleteAllApps()
    #print cc.createApp('text editor', 'news publisher', 'emotion analysis')
    #print cc.genToken('user credential','e182c3abb0','260553ad578ce008cbd6ec8b0c05eb81')
    print cc.isTokenValid('baf80af1d648ed3181ca0d6b86071e2f')
    print cc.refreshToken('refresh_token','e182c3abb0','260553ad578ce008cbd6ec8b0c05eb81', 'baf80af1d648ed3181ca0d6b86071e2f')
if __name__ == '__main__':
    main()
