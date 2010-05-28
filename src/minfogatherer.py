#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib2 import Request
from urllib2 import urlopen
from urllib2 import HTTPError
from urllib2 import URLError
from threading import Thread
import mlib
import logging

        
class SiteInfoGatherer(Thread):
    def __init__ (self,config,sites):
        Thread.__init__(self)  
        self.sites = sites
        self.config = config
        self.logger = logging.getLogger('MLogger.MInfoGatherer.SiteInfoGatherer')
        
    def run(self):
        for site in self.sites:
            if site['gatherer'] == 1:
                self.logger.debug('Starting info gathering: %s',site['url'])                
                osite = mlib.MoodleSite(self.config,db_id=site['db_id'])
                osite.get_info()                
                self.logger.debug('Finishing info gathering: %s',site['url'])



if __name__ == "__main__":
    #For testing
    pass