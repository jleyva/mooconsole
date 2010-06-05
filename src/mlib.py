#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cookielib
import urllib
import urllib2
import re
import os
import webbrowser
import hashlib
import sqlite3
import  cStringIO
from time import sleep, strftime, localtime
from mencrypt import *
from mconfig import *
import logging
import sys
import string

class MoodleSite(object):
    
    def __init__(self, config, name='', url='', username='', password='',notes='',wstoken='',wsusername='',wspassword='',monitor=0,gatherer=0,db_id=0):
        self.config = config
        self.site_info = {'version':'','release':'','courses':'','users':'','roleassignments':'','courseupdaters':'','posts':'','questions':'','resources':'','lang':''}
        self.logger = logging.getLogger('MLogger.MLib.MoodleSite')      
        self.cj = None
        self.opener = None  
            
        if db_id > 0:
            con = sqlite3.connect(self.config.db_path)    
            c = con.cursor()
            c.execute('select name,url,username,password,notes,wstoken,wsusername,wspassword,repo_id,monitor,gatherer,favicon from sites where id = ?',(db_id,))
            row = c.fetchone()
            if row is not None:
                enc = MEncrypter(self.config.master_password)
                self.name = enc.decrypt(row[0])
                self.url = enc.decrypt(row[1])
                self.username = enc.decrypt(row[2])
                self.password = enc.decrypt(row[3])
                self.notes = enc.decrypt(row[4])
                self.wstoken = enc.decrypt(row[5])
                self.wsusername = enc.decrypt(row[6])
                self.wspassword = enc.decrypt(row[7])                
                self.db_id = db_id
                self.repo_id = int(row[8])
                self.monitor = int(row[9])
                self.gatherer = int(row[10])
                
                if row[8] is not None:
                    self.favicon = cStringIO.StringIO(row[11])
                else:
                    self.favicon = None    
            c.close()
            
            def dict_factory(cursor, row):
                d = {}
                for idx, col in enumerate(cursor.description):
                    d[col[0]] = row[idx]
                return d            
            
            con.row_factory = dict_factory
            c = con.cursor()

            c.execute('select * from site_info where siteid = ? ORDER BY date DESC LIMIT 1',(db_id,))
            row = c.fetchone()    
            
            if row is not None:
                for name, value in self.site_info.iteritems():
                    self.site_info[name] = row[name]
                
                    
            c.close()
        else:
            self.name = name
            self.url = url
            self.username = username        
            self.password = password
            self.notes = notes
            self.wstoken = wstoken
            self.wsusername = wsusername
            self.wspassword = wspassword
            self.db_id = 0
            self.repo_id = 0
            self.monitor = monitor
            self.gatherer = gatherer
                  
        
    def get_info(self):

        self.logger.debug('Updating site information %s',self.name)
        cj = cookielib.CookieJar()
        
        opener =  urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)

        headers = {'User-Agent' : self.config.preferences['user_agent']}
        url  = self.url + '/login/index.php'
        params = urllib.urlencode({'username': self.username, 'password': self.password, 'testcookies' : 0})
        req = urllib2.Request(url, params, headers)
        try:
            response = urllib2.urlopen(req)
        except:
            self.logger.error('Updating site information, error cannot login to site')
            return False

        url  = self.url + '/admin/'
        req = urllib2.Request(url, None, headers)                       
        try:
            response = urllib2.urlopen(req).read()
        except:
            self.logger.warning('Updating site information, user is not admin')
            return False
        
        p = re.compile('name="sesskey" value="([^"]+)"')
        m = p.search(response)
        
        url  = self.url + '/admin/register.php'
        if m:
            params = urllib.urlencode({'sesskey': m.group(1)})
            req = urllib2.Request(url, params, headers)
        else:
            req = urllib2.Request(url, headers=headers)
                
        
        try:
            response = urllib2.urlopen(req).read()
        except:
            self.logger.warning('Updating site information, user is not admin')
            return False
        
        p = re.compile('input type="hidden" name="([^"]+)" value="([^"]+)"')
        m = p.findall(response)
                
        
        if m:
            today_date = strftime('%Y-%m-%d %H:%M:%S',localtime())
            
            try:
                con = sqlite3.connect(self.config.db_path)    
                c = con.cursor()                
                c.execute('insert into site_info (siteid,date) values (?,?)',(self.db_id,today_date))
                con.commit()
                last_si_id = c.lastrowid
            except:
                self.logger.error('Updating site information, error in db %s', sys.exc_info())
                return False

            for name, value in m:
                if name in self.site_info:
                    try:
                        c.execute('update site_info set '+name+' = ? where id = ?',(value, last_si_id))
                        con.commit()
                        
                        self.site_info[name] = value
                        
                    except:
                        self.logger.error('Updating site information, error in db %s', sys.exc_info())
                        return False
            c.close()
            self.logger.debug('Site %s info updated',self.name)
            return True
        
        else:
            return False

    def is_working(self):
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 5.5; WindowsNT)')]
        try:
            opener.open(self.url)
        except:
            return False
        else:
            return True    
        
    def do_login_browser(self):
        
        tmp_file_contents = u'<html>\n'
        tmp_file_contents += u'    <head>\n'
        tmp_file_contents += u'        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
        tmp_file_contents += u'    </head>\n'    

        tmp_file_contents += u'    <body onLoad="document.f.submit()">\n'
        tmp_file_contents += u'        <form name="f" action="'+self.url+u'/login/index.php'+'" method="post">\n'
        tmp_file_contents += u'            <input type="hidden" name="username" value="'+self.username+'">\n'
        tmp_file_contents += u'            <input type="hidden" name="password" value="'+self.password+'">\n'
        tmp_file_contents += u'            <input type="hidden" name="testcookies" value="0">\n'
        tmp_file_contents += u'        </form>\n'
        tmp_file_contents += u'    </body>\n'
        tmp_file_contents += u'</html>\n'
        
        m = hashlib.md5()
        m.update(self.url)
        tmp_file_path = os.path.join(self.config.tmp_path,'tmplb'+m.hexdigest()+'.html')
        
        try:
            file = open(tmp_file_path, 'w')
            file.write(tmp_file_contents.encode('utf-8'))
            file.close()
        except:
            return False
            
        webbrowser.open(os.path.abspath(file.name))
        sleep(3)
        os.remove(os.path.abspath(file.name))            
                
            
    def save_to_db(self):
        enc = MEncrypter(self.config.master_password)
        try:
            icon_data = open(os.path.join(self.config.img_path,'moodle.ico'), "rb").read()
            con = sqlite3.connect(self.config.db_path)    
            c = con.cursor()
            c.execute('insert into sites (name,url,username,password,notes,wstoken,wsusername,wspassword, repo_id, favicon, monitor, gatherer) values (?,?,?,?,?,?,?,?,?,?,?,?)',(enc.encrypt(self.name),enc.encrypt(self.url),enc.encrypt(self.username),enc.encrypt(self.password),enc.encrypt(self.notes),enc.encrypt(self.wstoken),enc.encrypt(self.wsusername),enc.encrypt(self.wspassword),self.repo_id,sqlite3.Binary(icon_data),self.monitor,self.gatherer))
            con.commit()
            self.db_id = c.lastrowid
            
            c.close()
            self.logger.debug('Site %s created',self.name)
            return True
        except:
            self.logger.error('Site %s not created %s',self.name, sys.exc_info())
            return False
        
    def get_favicon(self):
        
        # Get the favicon
        
        headers = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; WindowsNT)', 'Connection' : 'close'}    
        
        try:
            req = urllib2.Request(self.url, headers = headers)   
            response = urllib2.urlopen(req).read()
        except:
            return False
        
        p = re.compile('link rel="shortcut icon" href="([^"]+)"')
        m = p.search(response) 
        
        url = m.group(1)  
    
        if url:
            try:
                req = urllib2.Request(url, headers = headers) 
                icon = urllib2.urlopen(req).read() 
            except:
                return False
            
            try:
                con = sqlite3.connect(self.config.db_path)    
                c = con.cursor()
            
                c.execute('update sites set favicon = ? where id = ?',(sqlite3.Binary(icon),self.db_id))
                con.commit()    
                
                c.close()
                self.logger.debug('Site %s icon updated',self.name)
                return True     
            except:
                return False
    
    def delete(self):
        try:
            con = sqlite3.connect(self.config.db_path)    
            c = con.cursor()
            c.execute('delete from sites where id = ?',(self.db_id,))
            con.commit()
            c.close()
            self.logger.debug('Site %s deleted',self.name)
            return True
        except:
            return False
    
    def update(self, master_password=''):
        if len(master_password) > 4:
            enc = MEncrypter(master_password)    
        else:
            enc = MEncrypter(self.config.master_password)    

        try:
            con = sqlite3.connect(self.config.db_path)    
            c = con.cursor()
            c.execute("""update sites set 
            name = ?, url = ?, username = ?, password = ?, notes = ?, wstoken = ?, wsusername = ?, wspassword = ?, repo_id = ?, monitor = ?, gatherer = ? 
            where id = ?""",(enc.encrypt(self.name),enc.encrypt(self.url),enc.encrypt(self.username),enc.encrypt(self.password),enc.encrypt(self.notes),enc.encrypt(self.wstoken),enc.encrypt(self.wsusername),enc.encrypt(self.wspassword),self.repo_id, self.monitor, self.gatherer ,self.db_id))

            con.commit()
            c.close()
            self.logger.debug('Site %s updated',self.name)
            return True        
        except:
            self.logger.error('Error updating %s %s',self.name,sys.exc_info())
            return False

    def get_pref(self,pref):
        
        if self.cj is None:
            self.logger.debug('Getting pref %s',pref)
            self.cj = cookielib.CookieJar()
            
            self.opener =  urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
            urllib2.install_opener(self.opener)

            headers = {'User-Agent' : self.config.preferences['user_agent']}
            url  = self.url + '/login/index.php'
            params = urllib.urlencode({'username': self.username, 'password': self.password, 'testcookies' : 0})
            req = urllib2.Request(url, params, headers)
            try:
                response = urllib2.urlopen(req)
            except:
                self.logger.error('Error Getting pref %s %s',pref,sys.exc_info())
                return (False, None)
            
        
        req = urllib2.Request(self.url+'/admin/search.php?query='+pref['query'], None)

        try:
            response = urllib2.urlopen(req).read()
        except:
            self.logger.error('Error Getting pref %s %s',pref,sys.exc_info())
            return (False, None)
        
        elements = string.split(response,'class="form-item clearfix"')
        
        p_select = re.compile('<option value="([^"]*)"[\s]?(selected)?[^>]*>([^<]+)<\/option>')
        p_text = re.compile('input type="text"[^>]*value="([^"]*)"')
        p_textarea = re.compile('<textarea [^>]*>([^<]*)<')
        p_checkbox = re.compile('<input type="checkbox"([^>]+)>')
        
        
        for el in elements:
            if el.find('"'+pref['mid']+'"') != -1:
                if el.find('<select'):                    
                    m = p_select.findall(el)
                    return (True, ('select',m))
                
                if el.find('<input type="text"'):                    
                    m = p_text.findall(el)
                    return (True, ('text',m))
                    
                if el.find('<textarea'):                    
                    m = p_textarea.findall(el)
                    return (True, ('textarea',m))
                    
                if el.find('<input type="checkbox"'):                    
                    m = p_checkbox.findall(el)
                    if m:
                        for el2 in m:
                            if el2.find('"'+pref['mid']+'"') != -1:
                                return (True, ('checkbox',m))
                            
        return (False, None)

    
if __name__ == "__main__":
    #For testing
    
    config = MConfig()
    config.master_password = '123456781234567812345678'
    config.db_path = 'moohelper.sqlite'
    config.tmp_path = ''
    
    site = MoodleSite(config,'Demo','http://demo.moodle.net','admin','FunMood1ing!')
    site.save_to_db()
    site.get_info()
    #site.save_to_db()    
    
    #site = MoodleSite(config,'Demo','http://demo.moodle.net')
    #print site.is_working()

    #Remember remove the tmp file, it has the username and password in plain text
    #site = MoodleSite(config,'Demo','http://demo.moodle.net','admin','FunMood1ing!')
    #site.do_login_browser('')
    
    