#!/usr/bin/env python

from distutils.log import warn as printf
from pymongo import MongoClient, errors
from random import randrange as rand
import crypt, random, string
from datetime import datetime
import time

DBNAME = 'API_AUTH'
COLLECTION_USERS = 'users'
COLLECTION_APPS = 'apps'

TOKEN_VALID_HOURS = 2

USER_FIELDS = ('login', 'phone', 'email', 'job')
APP_FIELDS = ('appid', 'appkey', 'accesstoken', 'starttime', 'expiretime')
COLSIZ = 20

tformat = lambda s: str(s).title().ljust(COLSIZ)
cformat = lambda s: s.upper().ljust(COLSIZ)

def getSalt(chars=string.letters + string.digits):
    return random.choice(chars) + random.choice(chars)

class MongoDB(object):
    def __init__(self, address='localhost'):
        try:
            cxn = MongoClient(address, 27017)
        except errors.AutoReconnect:
            raise RuntimeError()
        self.db = cxn[DBNAME]
        self.users = self.db[COLLECTION_USERS]
        self.apps = self.db[COLLECTION_APPS]

        #((login,passwd), (login, passwd), ...)
    def insertUserInfo(self, number, users_reg):
        if number == 1:
            who, passwd = users_reg
            s = getSalt()
            self.users.insert(dict(login=who, password=crypt.crypt(passwd,s), salt=s, phone=None, email=None, job=None))
        else: 
            for who, passwd in users_reg:
                s = getSalt()
                self.users.insert(dict(login=who, password=crypt.crypt(passwd,s), salt=s, phone=None, email=None, job=None))
        print self.users.find()
    
    def queryUserExist(self, who, passwd):
        cursor = self.users.find({'login':who})
        for user in cursor:
            if user['password'] == crypt.crypt(passwd, user['salt']):
                return True
        return False

    def updateUserInfo(self, login, passwd, info):
        i = -1
        for i, user in enumerate(self.users.find({'login':login})):
            if user['password'] != crypt.crypt(passwd, user['salt']):
                continue
            print user
            phone, email = info
            self.users.update(user, {'$set':{'phone':phone, 'email':email, 'job':'software engineer'}})
        print self.users.find()
        return i+1

    def deleteAllUsers(self):
        i = -1
        for i, user in enumerate(self.users.find()):
            self.users.remove(user)
        return i+1
   
        #appid, appkey, appsecret
    def insertAppsInfo(self, number, apps_info):
        if number == 1:
            nm, tp, snm, aid, key, secret = apps_info
            self.apps.insert_one(dict(appname=nm, apptype=tp, servicename=snm,\
                                    appid=aid, appkey=key, appsecret=secret,\
                                    accesstoken=None, expiretime=None, starttime=None))
        else:
            self.apps.insert(
                dict(appname=nm, apptype=tp, servicename=snm, \
                    appid=aid, appkey=key, appsecret=secret, \
                    accesstoken=None, expiretime=None, starttime=None) \
                for nm, tp, snm, aid, key, secret in apps_info )
        print self.apps.find()
    
    def queryAppIDExist(self, appid):
        cursor = self.apps.find({"appid":appid})
        if cursor.count() == 0:
            return False
        return True

        #access_token, expire_time, start_time,
    def updateAppInfo(self, appid, token):
        i = -1
        start = time.mktime(datetime.now().timetuple())
        expire = start + TOKEN_VALID_HOURS * 3600
        for i, app in enumerate(self.apps.find({'appid':appid})):
            self.apps.update(app, 
                            {'$set': {'accesstoken':token, 'expiretime':expire, 'starttime':start}})
        return i+1, token, start, expire
    
    def deleteAllApps(self):
        i = -1
        for i, app in enumerate(self.apps.find()):
            self.apps.remove(app)
        return i+1

    def deleteAppInfo(self, rmid):
        i = -1
        for i, app in enumerate(self.apps.find({'appid':rmid})):
            self.apps.remove(app)
        return i+1
    
    def dbDump(self):
        printf('\n%s' % ''.join(map(cformat, USER_FIELDS)))
        for user in self.users.find():
            printf(''.join(map(tformat, 
                (user[k] for k in USER_FIELDS))))

        printf('\n%s' % ''.join(map(cformat, APP_FIELDS)))
        for app in self.apps.find():
            printf(''.join(map(tformat, 
                (app[k] for k in APP_FIELDS))))

    def finish(self):
        self.db.connection.disconnect()

def main():
    printf('*** Connect to %r database' % DBNAME)
    try:
        mongo = MongoDB()
    except RuntimeError:
        printf('\nERROR: MongoDB server unreachable, exit')
        return
    mongo.deleteAllUsers()
    mongo.insertUserInfo(2,(('ting','111456'),('soozi', '234987')))
    printf('\n*** Update user info into table %r' % COLLECTION_USERS)
    mongo.updateUserInfo('ting', '111456', ('17639269483', 'sfcixios@gmail.com'))
    print 'user tig with passwd 111456 exist: ', mongo.queryUserExist('ting','111456')

    mongo.deleteAllApps()   
    printf('\n** Insert app info into table %r' % COLLECTION_APPS)
    mongo.insertAppsInfo(3,(('app','sdf','s86',001, 'k234','89234sdfc'),('app','sdf','ae3',002, 'weori','asdf87'), ('xuio','ssdf','sdf897',003, 'aosdif', '23947asdfh')))
    printf('\n** Update app info in table %r' % COLLECTION_APPS)
    mongo.updateAppInfo(001,('87zzzlolfi'))
    mongo.deleteAppInfo(002)
    print 'AppID 002 Exist: ', mongo.queryAppIDExist(002)
    print 'AppID 001 Exist: ', mongo.queryAppIDExist(001)
    mongo.dbDump()
   
if __name__ == '__main__':
    main()
