#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cookielib
import urllib
import urllib2
import re
import sqlite3
from mconfig import *
import logging
import sys

class MLiveStats(object):
    
    def __init__(self, config, site):
        self.config = config
        self.site = site
        self.logger = logging.getLogger('MLogger.MLiveStats.MLiveStats')
        self.cj = None
        self.opener = None
        self.log = {}
        self.headers = {'User-Agent' : self.config.preferences['user_agent']}
        
    def login(self):
        self.logger.debug('Loggin site for live stats %s',site.name)
        self.cj = cookielib.CookieJar()
        
        self.opener =  urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(self.opener)
        
        url  = site.url + '/login/index.php'
        params = urllib.urlencode({'username': site.username, 'password': site.password, 'testcookies' : 0})
        req = urllib2.Request(url, params, self.headers)
        try:
            response = urllib2.urlopen(req)
        except:
            self.logger.error('Loggin site for live stats, error cannot login to site %s',sys.exc_info())
            return False
        
        
    def update(self):
        if self.cj is None:
            if not self.login():
                return False
            
        url  = self.url + '/course/report/log/live.php?id=1'
        req = urllib2.Request(url, None, self.headers)                       

        try:
            response = urllib2.urlopen(req).read()
        except:
            self.logger.warning('Getting log live, error %s', sys.exc_info())
            if self.login():
                try:
                    response = urllib2.urlopen(req).read()
                except:
                    self.logger.warning('Getting log live, error %s', sys.exc_info())
                    return False
            else:
                return False
            
            
    
if __name__ == "__main__":
    #For testing
    
##    config = MConfig()
##    config.master_password = '123456781234567812345678'
##    config.db_path = 'moohelper.sqlite'
##    config.tmp_path = ''
##    
##    site = MoodleSite(config,'Demo','http://demo.moodle.net','admin','FunMood1ing!')
##    
##    ls = MLiveStats(config,site)
##    print ls.update()

    text = '''<tr class="r0"><td class="cell c0"><a href="http://demo.moodle.net/course/view.php?id=1">Moodle Demo mome</a></td><td class="cell c1" align="right">Mon 7 June 2010, 04:11 AM</td><td class="cell c2"><a title="Popup window" href="http://demo.moodle.net/iplookup/index.php?ip=89.131.126.237&amp;user=2"  onclick="this.target='iplookup'; return openpopup('/iplookup/index.php?ip=89.131.126.237&amp;user=2', 'iplookup', 'menubar=0,location=0,scrollbars,resizable,width=700,height=440', 0);">89.131.126.237</a></td><td class="cell c3">   <a href="http://demo.moodle.net/user/view.php?id=2&amp;course=1">Admin User</a></td><td class="cell c4"><a title="Popup window" href="http://demo.moodle.net/course/report/log/live.php?id=1"  click="this.target='fromloglive'; return openpopup('/course/report/log/live.php?id=1', 'fromloglive',menubar=0,location=0,scrollbars,resizable,width=700,height=440', 0);">course report live</a></td><td class="cell c5">Moodle Demonstration Site</td></tr>
    '''
    e = re.compile('<td[^>]*>(.+)<\/td>')
    print e.findall(text)

    
    
    