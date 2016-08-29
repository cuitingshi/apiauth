#!/usr/bin/env python

from flask import Flask, request, render_template, jsonify, url_for
from flask_restful import Resource, Api
from functools import wraps

from authapi import AuthApi 
from db import MongoDB

auth_server = Flask(__name__)
auth_api = Api(auth_server)
auClient = AuthApi()

class LoginError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

@auth_server.route('/dev/home')
def home():
    #username = kwds['user']
    return render_template('home.html') #, username=username)

@auth_server.route('/dev/register', methods = ['GET', 'POST'])
def registerDev():
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':    
        uname = request.form.get('username')
        passwd = request.form.get('password')
        if uname is None or passwd is None:
            abort(400)
        
        success, msg = auClient.registerDev(uname, passwd)
        status = 200
        if not success:
            status = 406
        return jsonify({'status':status, 'message':msg})

@auth_server.route('/dev/signin', methods = ['GET', 'POST'])
def signinDev():
    if request.method == 'GET':
        referrer = request.args.get('next', '/')
        return render_template("signin.html", next=referrer)
    if request.method == 'POST':
        uname = request.form['username']
        passwd = request.form['password']
        next = request.form['next']
        try:
            if not MongoDB().queryUserExist(uname, passwd):
                raise LoginError('wrong user name or password ')
            session['logged_in'] = uname
            return redirect(next)
        except LoginError as e:
            return render_template('signin.html', next=next, error=e.value)

@auth_server.route('/dev/signout/', methods=['POST'])
def signout():
    session.pop('logged_in', None)
    return redirect(url_for('/dev/home'))

@auth_server.route('/dev/apps/create', methods=['POST'])
def createApp():
    #createApp(self, app_name, app_type, service_name)
    appname = request.form.get('appname')
    apptype = request.form.get('apptype')
    servicename = request.form.get('servicename')
    appid, appkey, appsecret = auClient.createApp(appname, apptype, servicename)
    return jsonify({'AppID':appid, 'AppKey':appkey, 'AppSecret':appsecret})

@auth_server.route('/dev/apps/token', methods=['POST'])
def getOrRefreshToken():
    granttype = request.json['grant_type']
    appid = request.json['client_id']
    appsecret = request.json['client_secret']
    
    #genToken(self, grant_type, app_id, app_key_secret)
    if granttype == 'client_credentials':
        #get a new token
        token, start, expire = auClient.genToken(granttype, appid, appsecret)
        return jsonify({'access_token':token, 'expire_timestamp':expire})
    elif granttype == 'refresh_token':
        pretoken = request.json.get('token')
        success, msg, token, expire = auClient.refreshToken(granttype, appid, appsecret, pretoken)
        if not success:
            return jsonify({'status':406, 'message': msg})
        return jsonify({'status':200, 'previous_token':pretoken, 'refreshed_token':token, 'expire_timestamp':expire})
    else:
        return jsonify({'status':406, 'message':'unknown grant_type ' + granttype })
    
@auth_server.route('/dev/apps/token/auth', methods=['POST'])
def isTokenValid():
    token = request.json.get('token')
    success = auClient.isTokenValid(token)
    return jsonify({'valid':success})

def main():
    auth = AuthApi()
    auth_server.run(debug=True)

if __name__ == '__main__':
    main()
    

