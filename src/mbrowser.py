#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import *
import urllib
import urllib2
import cookielib
import re
try:
    import json
except ImportError:
    import simplejson as json
import PHPUnserialize
import MultipartPostHandler
from threading import Thread
from time import sleep
import PHPUnserialize
import MultipartPostHandler
import logging
import sys

class FileUploaderThread(Thread):
    def __init__ (self,upload_queue,first,last,callback):
        Thread.__init__(self)  
        self.queue = upload_queue
        self.first = first
        self.last = last
        self.callback = callback
        self.sess_key = ''
        self.logger = logging.getLogger('MLogger.MBrowser.FileUploaderThread')
        
    def run(self):
        for i in range(self.first, self.last):
            site = self.queue[i]['site']
            dir = self.queue[i]['dir']
            
            self.callback(i,'uploading')
            self.logger.debug('Uploading %s to %s',self.queue[i]['file_path'],site.name)
            
            us = PHPUnserialize.PHPUnserialize()
            dir_data = us.unserialize(b64decode(dir))
            
            upload_sess_url = url = site.url + '/files/index.php?contextid='+dir_data['contextid']+'&itemid='+dir_data['itemid']+'&filearea='+dir_data['filearea'] +'&filepath='+dir_data['filepath']+'&filename='+dir_data['filename']

            if self.sess_key == '':
                cj = cookielib.CookieJar()

                opener =  urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                urllib2.install_opener(opener)

                headers = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; WindowsNT)'}
                url  = site.url+'/login/index.php'
                params = urllib.urlencode({'username': site.username, 'password': site.password, 'testcookies' : 0})
                req = urllib2.Request(url, params, headers)
                try:
                    response = urllib2.urlopen(req)
                except:
                    self.callback(i,'failed')
                    break

                url = upload_sess_url
                req = urllib2.Request(url, None, headers)                       
                try:
                    response = urllib2.urlopen(req).read()
                except:
                    self.callback(i,'failed')
                    break
                                
                p = re.compile('name="sesskey" value="([^"]+)"')
                m = p.search(response)
              
                if m:
                    self.sess_key = m.group(1)
                
            if self.sess_key != '':    
                self.logger.debug('Uploading file now %s',self.queue[i]['file_path'])
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),
                                        MultipartPostHandler.MultipartPostHandler)
                url = site.url + '/files/index.php'
                params = {'newfile': open(self.queue[i]['file_path'], "rb") ,'sesskey': self.sess_key, 'contextid' : dir_data['contextid'], 'filearea' : dir_data['filearea'], 'filename' : '', 'filepath' : dir_data['filepath'], 'itemid' : dir_data['itemid']}
                
                try:
                    response = opener.open(url,params).read()                
                except:
                    self.callback(i,'failed')
                    continue
                
                #TODO - Really check that the file was upload
                #Take care with utf-8 problems in windows
                self.callback(i,'uploaded')
                self.sess_key = ''
                
                p = re.compile('name="sesskey" value="([^"]+)"')
                m = p.search(response)
              
                if m:
                    self.sess_key = m.group(1)
            

class MoodleFileBrowser(object):
    
    def __init__(self, site, config):
        self.site = site
        self.config = config
        self.files_tree = {}
        self.cache_mode = False
        self.selected_dir = ''
        self.cj = cookielib.CookieJar()
        opener =  urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(opener)
        self.logger = logging.getLogger('MLogger.MWSLib.MoodleFileBrowser')

    def create_folder(self,dir,name):
        
        headers = {'User-Agent' : self.config.preferences['user_agent']}
        
        us = PHPUnserialize.PHPUnserialize()
        dir_data = us.unserialize(b64decode(dir))
        
        upload_sess_url = url = self.site.url + '/files/index.php?contextid='+dir_data['contextid']+'&itemid='+str(dir_data['itemid'])+'&filearea='+dir_data['filearea']+'&filepath='+dir_data['filepath']+'&filename='+dir_data['filename']         
        
        self.logger.debug('Creating folder %s in %s', name, upload_sess_url)

        url = upload_sess_url
        req = urllib2.Request(url, None, headers)                       
        try:
            response = urllib2.urlopen(req).read()
        except:
            self.logger.debug('Cannot create folder %s in %s',name,upload_sess_url)
            return False
                        
        p = re.compile('name="sesskey" value="([^"]+)"')
        m = p.search(response)
      
        if m:
            sess_key = m.group(1)

            url = self.site.url + '/files/index.php'
            params = urllib.urlencode({'newdirname': name ,'sesskey': sess_key, 'contextid' : dir_data['contextid'], 'filearea' : dir_data['filearea'], 'filename' : '', 'filepath' : dir_data['filepath'], 'itemid' : dir_data['itemid']})
                        
            req = urllib2.Request(url, params, headers)
            try:
                response = urllib2.urlopen(req).read()                
            except:
                self.logger.debug('Cannot create folder %s in %s %s',name,url,params)
                return False
            
            #TODO Check if the folder is created
            return True
            
        self.logger.debug('Cannot get sesskey to create folder %s',name)
        return False
        
    
    def get_root(self):
        if not self.cache_mode:            
            
            headers = {'User-Agent' : self.config.preferences['user_agent']}
            url  = self.site.url + '/login/index.php'
            params = urllib.urlencode({'username': self.site.username, 'password': self.site.password, 'testcookies' : 0})
            req = urllib2.Request(url, params, headers)
            try:
                response = urllib2.urlopen(req)
            except:
                return False
            
            
            if self.site.repo_id == 0:            
                for i in range(1,int(self.config.preferences['max_repo_id']) + 1):
                    r_url = self.site.url + '/repository/repository_ajax.php?action=list&repo_id='+str(i)+'&p=&page=&env=editor&filearea=user_draft'
                    req = urllib2.Request(r_url, headers=headers)
                    try:
                        response = urllib2.urlopen(req).read()
                        elements = json.loads(response)
                        self.logger.debug('Getting site repo id, repository response %s', elements) 
                        if 'upload' not in elements and 'list' in elements:
                            self.site.repo_id = i
                            self.site.update()
                            break
                    except:
                        self.logger.error('Getting site repo id, error %s', sys.exc_info())
                        continue
                

            if self.site.repo_id == 0:
                self.logger.warning('Getting site repo id, repo id is 0')
                return False
            
            url = self.site.url + '/repository/repository_ajax.php?action=list&repo_id='+str(self.site.repo_id)+'&p=&page=&env=editor&filearea=user_draft'
            
            req = urllib2.Request(url, headers=headers)
            try:
                response = urllib2.urlopen(req).read()
            except:
                return False
            
            try:
                elements = json.loads(response)          
                us = PHPUnserialize.PHPUnserialize()
            except:
                return False
            
            for el in elements[u'list']:
                file_branch = {}
                for key,value in el.iteritems():                
                    
                    if key == 'path' or key == 'source':
                        dec = b64decode(value)                        
                        file_branch[key] = us.unserialize(dec)
                        file_branch['link'] = value
                    else:
                        file_branch[key] = value
                
                self.logger.debug('Root Branch %s', file_branch)
                self.files_tree[file_branch['link']] = file_branch

            return self.files_tree
            
        
    def get_branch(self,b):
        if not self.cache_mode:
            headers = {'User-Agent' : self.config.preferences['user_agent']}

            url = self.site.url + '/repository/repository_ajax.php?action=list&repo_id='+str(self.site.repo_id)+'&p=&page=&env=editor&filearea=user_draft&p='+b
            
            req = urllib2.Request(url, headers=headers)
            try:
                response = urllib2.urlopen(req).read()
            except:
                self.logger.error('Error gettinb branch %s', url)
                return False
            
            try:
                elements = json.loads(response)            
                us = PHPUnserialize.PHPUnserialize()
            except:
                self.logger.error('Error gettinb branch %s', url)
                return False
            
            branches = {}
            
            for el in elements[u'list']:
                file_branch = {}
                for key,value in el.iteritems():                
                    
                    if key == 'path' or key == 'source':
                        dec = b64decode(value)                        
                        file_branch[key] = us.unserialize(dec)
                        file_branch['link'] = value
                    else:
                        file_branch[key] = value
                
                self.logger.debug('Dir Branch %s', file_branch)
                branches[file_branch['link']] = file_branch

            return branches
        
    def can_upload(self,b):
        if b is not None and b != '':
            us = PHPUnserialize.PHPUnserialize()
            b_clear = us.unserialize(b64decode(b))
            return 'filearea' in b_clear and b_clear['filearea'] != '' and b_clear['filearea'] is not None
        else:
            return False
            
    def set_branch(self):
        pass        

if __name__ == "__main__":
    #For testing
    
    config = MConfig()
    config.master_password = '123456781234567812345678'
    config.db_path = 'moohelper.sqlite'
    config.tmp_path = ''
    
    site = MoodleSite(config,'Demo','http://demo.moodle.net','admin','FunMood1ing!')   
    