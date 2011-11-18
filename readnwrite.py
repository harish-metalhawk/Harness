#!/usr/bin/python2.7
import os,select,time,re


def blocked_read(fd,size=1024):
    assert isinstance(fd,int)
    val = os.read(fd,size)
    return val

def write(fd,cont):
    assert isinstance(fd,int)
    if not cont.endswith('\n'):
        cont += '\n'
    chars = os.write(fd,cont)
    time.sleep(1)
    return chars

def unblocked_read(fd,size=1024,TIME_OUT=10):
    out = []
    while True:
        rd,wt,ex = select.select([fd],[],[],TIME_OUT)
        if fd not in rd:
            break
        out.append(os.read(fd,size))
    return ''.join(out)

def bunbread(fd,size=1024,TIME_OUT=2):
    out = []
    out.append(blocked_read(fd,size))
    out.append(unblocked_read(fd,size,TIME_OUT))
    return ''.join(out)
    
def readtillexpect(fd,expect):
    assert isinstance(expect,list)
    reply = ''
    t = time.time()
    while True:
        if (time.time() - t) > 300:   
            return 'bad login' #implementing a time out if bad bashrc files , pending : raise an exception rather than if statement
        rd,wt,ex = select.select([fd],[],[],.1)
        if fd in rd:
            rep = os.read(fd,1024)
            rep.replace('\r','')
            #print rep,
            reply += rep
        for i in expect :
            if re.search(i,reply):
                return reply
