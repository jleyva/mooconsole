#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import sqlite3
import sys     
    
class MUpgrade(object):
    def __init__ (self,config):
        self.config = config
        self.logger = logging.getLogger('MLogger.MUpgrade.MUpgrade')
        
    def upgrade(self):
    
        if self.config.release != self.config.preferences['release']:
            new_release = int(self.config.release)
            old_release = int(self.config.preferences['release'])
            
            if old_release < 2010060101:
                self.logger.debug('Upgrading to 2010060101 from %s',old_release)
                try:
                    con = sqlite3.connect(self.config.db_path)    
                    con.execute('''CREATE TABLE IF NOT EXISTS "log" 
                        ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , 
                        "siteid" INTEGER,
                        "component" VARCHAR, 
                        "info" VARCHAR, 
                        "data" VARCHAR, 
                        "date" DATETIME
                        )                    
                    ''')
                    con.commit()
                    con.close()
                except:
                    self.logger.critical('Error upgrading to 2010060101 from %s: %s',old_release,sys.exc_info())
                    return False
                    
            self.config.preferences['release'] = self.config.release  
            self.config.preferences['version'] = self.config.version
            self.config.save_pref('release')
            self.config.save_pref('version')
            self.logger.debug('Upgrading to %s completed',self.config.release)
                
        return True



if __name__ == "__main__":
    #For testing    
    pass