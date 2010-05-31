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
        info = 'HTTP Error '+str(e.code)
        return (False, info)
    except URLError, e:
        info = 'Connectivity problem'
        return (False, info)
    else:
        return (True,'')
        
class URLCheckThread(Thread):
    def __init__ (self,sites,callback):
        Thread.__init__(self)  
        self.sites = sites
        self.callback = callback
        self.logger = logging.getLogger('MLogger.MURLMonitor.URLCheckThread')
        
    def run(self):
        for site in self.sites:
            if site['monitor'] == 1:
                self.logger.debug('Checking URL: %s',site['url'])
                status,info = check_url(site['url'])
                self.callback(site,status,info)
                self.logger.debug('Checked URL: %s, %s, %s',site['url'],status,info)



if __name__ == "__main__":
    #For testing
    
    check_url('http://demo.moodle.net')
    
    check_url('http://demo.moodle.net/zs')
    
    check_url('http://xZsa.mmolllle.net')