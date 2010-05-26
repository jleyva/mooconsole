#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyDes import *
from binascii import hexlify
from binascii import unhexlify
from base64 import *

class MEncrypter(object):
        
    def __init__(self, key):
        if len(key) < 24:
            key = key + b64encode(key.encode("utf-8")) 
            key = key + b64encode(key.encode("utf-8")) * 2            
            
        key = key[0:24]   

        self.k = triple_des(key.encode("utf-8"), CBC, "\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
    
    def encrypt(self, text):
        return hexlify(self.k.encrypt(text.encode("utf-8")))

    def decrypt(self, text):
        return unicode(self.k.decrypt(unhexlify(text)),"utf-8")


if __name__ == "__main__":
    #For testing
    
    enc = MEncrypter(u'123456781234567812345678')
    e = enc.encrypt(u'abñ')
    d = enc.decrypt(e)
    
    print "Encrypted: %r" % e
    print "Decrypted: %r" % d