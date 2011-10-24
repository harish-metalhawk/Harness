#!/usr/bin/python2.7
import re,os,exceptions

class BadConf(exceptions.Exception):
    def __init__(self):
        return

    def __string__(self):
        print 'Bad conf file'

def readConf(path):
    invalid_parm = []
    std_keys = ['user','host','path','command','logs','pass','dur','port','restart','delay']
    if not os.path.isfile(path):
        print "could not find the conf file in the given path"
    else:
        confs = dict()
        conf_file = open(path,'r')
        conf = conf_file.readlines()
        for i in conf:
            try:
                opt,val = i.split('=',1)
                confs[opt] = val
            except:
                #if i =='' or i == '\n':
                    #print 'a blank line'
                #print 'wats this'
                pass
        confs = validate_conf(clean_up(confs))
        for l in confs.iterkeys():
                if l not in std_keys:
                    #print '------',l
                    #print 'bad conf file(opts), please check the usage'
                    invalid_parm.append(l)
        [ confs.pop(i) for i in invalid_parm ]
        #for val,keys in confs.iteritems():
                #self.validate_conf(confs,std_keys)
        for i in std_keys:
            if i not in confs:
                raise BadConf      #raise an exception of bad confs
        return confs

def validate_conf(opts):
    extra_opts = {'dur':'0','port':'0','restart':'0','delay':'0'}
    for k,v in extra_opts.iteritems():
        if k not in opts:
            opts[k] = v
    return opts
        

def clean_up(opts):
    new_opts = {}
    for i,k in opts.iteritems():
        new_opts[i.rstrip(' ').lstrip(' ')] = k.lstrip(' ')
    return new_opts

if __name__ == '__main__':
    k = readconf('/home/harish/New_ssh/conf0.txt')
    for i in k:
        print i

                        
