#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import xml.dom.minidom
import urllib
import urllib2
import logging

class MoodleWSHelper(object):
    
    def __init__(self,ws_dir):
        
        
        self.logger = logging.getLogger('MLogger.MWSLib.MoodleWSHelper')
        
        def getText(nodelist):
            rc = ""
            for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                    rc = rc + node.data
            return rc 
        
        self.ws_list = []
        
        ws_list_dir = os.listdir(ws_dir)      
        ws_list_dir.sort()

        for ws_file in ws_list_dir:   
            fp = os.path.join(ws_dir,ws_file)
            
            if os.path.isfile(fp):
                xmlc = open(fp).read() 
                dom = xml.dom.minidom.parseString(xmlc)
                ws_ds = {}
                ws_ds['name'] = getText(dom.getElementsByTagName("name")[0].childNodes)
                ws_ds['description'] = getText(dom.getElementsByTagName("description")[0].childNodes)
                ws_ds['wsfname'] = getText(dom.getElementsByTagName("wsfname")[0].childNodes)            
                ws_ds['params'] = {}
                for param in dom.getElementsByTagName('param'):
                    param_name = getText(param.getElementsByTagName("name")[0].childNodes)
                    structure  = getText(param.getElementsByTagName("structure")[0].childNodes)
                    type = getText(param.getElementsByTagName("type")[0].childNodes)
                    
                    ws_ds['params'][param_name] = {}
                    ws_ds['params'][param_name]['structure'] = structure
                    ws_ds['params'][param_name]['type'] = type
                    
                    if type == 'object':
                        ws_ds['params'][param_name]['attributes'] = []
                        
                        object = param.getElementsByTagName("object")[0]
                        for attrs in object.getElementsByTagName('attribute'):
                            #print attrs.tagName+'abbb'
                            ws_ds['params'][param_name]['attributes'].append((getText(attrs.childNodes),attrs.getAttribute('type')))
                    
                
                self.ws_list.append(ws_ds)
        
        self.logger.debug('Web service descriptors loaded: %s', self.ws_list)
        

class MoodleWS(object):
    
    def __init__(self, ws_object):
        
        self.name = ws_object['name']
        self.description  = ws_object['description']
        self.wsfname = ws_object['wsfname']
        self.params = ws_object['params']
        self.data_grid = {}
        self.cols = {}
        self.logger = logging.getLogger('MLogger.MWSLib.MoodleWS')
        
    def set_data_grid(self,param,data):
        self.data_grid[param] = data    
    
    def get_data_grid(self,param):
        return self.data_grid[param]
        
    def get_grid_cols(self, param):
            
        param_data = self.params[param]
        
        if param not in self.cols:        
            self.cols[param] = []
                    
            if param_data['type'] == u'object':
                for a_name, a_type in param_data['attributes']:
                      
                    if a_type == 'int':
                        self.cols[param].append({'name' : a_name, 'format' : 'number'})                
                    else:
                        self.cols[param].append({'name' : a_name, 'format' : ''})
                    
            else:
                if param_data['type'] == 'int':
                    self.cols[param].append({'name' : param, 'format' : 'number'})
                else:
                    self.cols[param].append({'name' : param, 'format' : ''})
        
        return self.cols[param]    
    
    
    def set_data(self,data):
        self.ws_data = {}
        
        for p_name,p_data in self.params.iteritems():
            
            if p_data['type'] == 'object' and p_data['structure'] == 'list':
                cols = self.get_grid_cols(p_name)
                l_cols = []
                
                for c_data in cols:
                    c_name = c_data['name']                    
                    l_cols.append(c_name)
                
                pos = 0
                for row in data:
                    valid_row = False
                    l_data = len(row)
                    
                    for i in range(0,l_data):
                        if row[i] != u'':
                            valid_row = True
                        
                    if valid_row:                            
                        for i in range(0,l_data):
                            self.ws_data[p_name+'['+str(pos)+']['+l_cols[i]+']'] = row[i]
                                                
                        pos = pos + 1    
        

            elif p_data['structure'] == 'list':
                pos = 0
                for row in data:
                    if row[0] != u'':
                        self.ws_data[p_name+'['+str(pos)+']'] = row[0]
                        pos = pos + 1 
       
        
            else:
                if data[0][0] != u'':
                    self.ws_data[p_name] = data[0][0]
        
    
    def is_ready(self):
        return len(self.ws_data) > 0
    
    def execute(self, site):
        opener =  urllib2.build_opener()
        urllib2.install_opener(opener)

        headers = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; WindowsNT)'}

        if site.wstoken:
            url  = site.url + '/webservice/rest/server.php?wstoken='+site.wstoken+'&wsfunction='+self.wsfname
        elif site.wsusername != '' and site.wspassword != '':
            url  = site.url + '/webservice/rest/server.php?wsusername='+site.wsusername +'&wspassword='+site.wspassword +'&wsfunction='+self.wsfname
        else:
            return (False, None)

        params = urllib.urlencode(self.ws_data)
        
        self.logger.debug('Executing WS: %s %s',url,params)
        
        req = urllib2.Request(url, params, headers)

        response = ''
        try:
            response = urllib2.urlopen(req).read()
        except:
            return (False, None)
        
        
        def getText(nodelist):
            rc = ""
            for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                    rc = rc + node.data
            return rc
        
        self.logger.debug('WS Response: %s',response)
        
        if response.find('<EXCEPTION class') > -1:
            dom = xml.dom.minidom.parseString(response)
            
            message = getText(dom.getElementsByTagName("MESSAGE")[0].childNodes)
            
            return (False,message)
            
        else:
        
            dom = xml.dom.minidom.parseString(response)

            grid = []
            cols_names = []
            first = True
            
            for single in dom.getElementsByTagName('SINGLE'):
                cols = []
                
                for key in single.getElementsByTagName('KEY'):
                    try:
                        value = ''
                        for val in key.getElementsByTagName("VALUE"):
                            if value != '':
                                value = value+','+getText(val.childNodes)
                            else:
                                value = getText(val.childNodes)
                        
                    finally:                    
                        cols.append(value)
                        
                    if first:                        
                        cols_names.append(key.getAttribute('name'))
                    
                first = False                
                grid.append(cols)
                
            return (True,(cols_names,grid))
        

if __name__ == "__main__":
    #For testing
    pass