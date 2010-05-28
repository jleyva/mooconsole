﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
import os.path

class MPathHelper(object):
# Thanks to http://us.pycon.org/media/2010/talkdata/PyCon2010/038/paper.html
    def platform(self):
        if sys.platform.startswith('win'):
            return 'windows'
        elif sys.platform.startswith('darwin'):
            return 'mac'
        return 'linux'

    def is_package(self): # eg /usr/bin/phatch
        return not sys.argv[0].endswith('.py')

    def setup(self):
        if hasattr(sys, 'frozen'):
            return 'frozen'
        elif self.is_package():
            return 'package'
        return 'source'    
    
    def __init__(self):
        self.path_data = ''
        self.path_user_data = ''
        
        context = (self.platform(),self.setup())
        
        #TODO paths
        if context == ('mac', 'frozen'):
            DATA = os.path.join(APP_ROOT, 'Contents','Resources') # py2app
        elif context == ('windows', 'frozen'):
            self.path_data = os.path.join(os.getcwd(),'data')
            self.path_user_data = os.path.join(os.getcwd(),'user_data')
        elif context == ('linux', 'package'):
            DATA = os.path.join(sys.prefix, 'share', APP_NAME) # linux
        else:
            pathname = os.path.dirname(sys.argv[0])
            base, src = os.path.split(os.path.abspath(pathname))
            self.path_data = os.path.join(base,'data')
            self.path_user_data = os.path.join(base,'user_data')
            

class MConfig(object):
    preferences = dict()
    master_password = ''
    db_path = ''
    tmp_path = ''
        
    def __init__(self):
        p = MPathHelper()
        self.db_path = os.path.join(p.path_user_data,'mooconsole.sqlite')
        self.log_path = os.path.join(p.path_user_data,'log.txt')
        self.img_path = os.path.join(p.path_data,'img')
        self.tmp_path = p.path_user_data
        self.ws_path = os.path.join(p.path_data,'webservice')
        
        self.master_password = ''        
        self.preferences['user_agent'] = 'Mozilla/4.0 (compatible; MSIE 5.5; WindowsNT)'
        self.preferences['max_repo_id'] = '5'
        self.preferences['max_log_files'] = '5'
        self.preferences['max_log_file_size'] = '1048576'
        self.preferences['url_monitor_time'] = '0'
        self.preferences['site_gatherer_time'] = '0'
        self.reload()
        

    def reload(self):
        con = sqlite3.connect(self.db_path)
        c = con.cursor()
        c.execute('select * from config')        
        
        for row in c:
            self.preferences[row[1]] = row[2]
        c.close()
        
    def save(self):
        con = sqlite3.connect(self.db_path)    
        c = con.cursor()
            
        for name, value in self.preferences.iteritems():           
            c.execute('select name from config where name = ?', (name,))
            if c.fetchone() is not None:
                c.execute('update config set value = ? where name = ?', (value,name))        
            else:
                c.execute('insert into config (name,value) values (?,?)', (name,value))        
        con.commit()
        c.close()

if __name__ == "__main__":
    #For testing
    
    config = MConfig()
    config.preferences[u'test'] = u'my test value'
    config.save()
    print config.preferences