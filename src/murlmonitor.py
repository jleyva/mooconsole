#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib2 import Request
from urllib2 import urlopen
from urllib2 import HTTPError
from urllib2 import URLError
from threading import Thread
import logging

def check_url(url):
    headers = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; WindowsNT)', 'Connection' : 'close'}    
    
    req = Request(url, headers = headers)
    try:
        response = urlopen(req)
    except HTTPError, e:
        return False
    except URLError, e:
        return False 
    else:
        return True
        
class URLCheckThread(Thread):
    def __init__ (self,mt):
        Thread.__init__(self)  
        self.mt = mt
        self.logger = logging.getLogger('MLogger.MURLMonitor.URLCheckThread')
        
    def run(self):
        for site in self.mt.msites:
            if site['monitor'] == 1:
                self.logger.debug('Checking URL: %s',site['url'])
                if not check_url(site['url']):
                    self.mt.ChangeSiteURLStatus(site)
                self.logger.debug('Checked URL: %s',site['url'])



if __name__ == "__main__":
    #For testing
    
    check_url('http://demo.moodle.net')
    
    check_url('http://demo.moodle.net/zs')
    
    check_url('http://xZsa.mmolllle.net')