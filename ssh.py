#!/usr/bin/python2.6
import os,sys,re
from readnwrite import blocked_read,write,unblocked_read,bunbread,readtillexpect
'''
more robust way of establishing ssh is implemented using the readtillexpect
'''

class SSH(object):
    def __init__(self, host = 'qaesp5', username='sqatest', pswd='BugM3qa'):
        self.host = host
        self.username = username
        self.pswd = pswd
        self.login = username+'@'+host

    def fork(self):
        '''return the pid and file descriptors'''
        pid,fd = os.forkpty()
        if pid == 0:
            self.execssh()
        else:
            success = self.authenticate(fd)
            return pid,fd,success

    def execssh(self):
        os.execv('/usr/bin/ssh',['ssh',self.login])

    def authenticate(self,fd):
        re_timeout = 'Connection timed out'
        re_authen = 'Are you sure you want to continue connecting (yes/no)?'
        re_hosterr = 'ssh: Could not resolve hostname '+self.host+': Name or service not known'
        re_permdenied = 'Permission denied, please try again.'
        re_pass = self.login+'\'s password:'
        re_log = self.login
        re_bad_bashrc = 'bad login'
        re_authorized = 'to the list of known hosts.'
        success = True
        reply = readtillexpect(fd,[re_timeout,re_authen,re_hosterr,re_permdenied,re_pass,re_log,re_authorized,re_bad_bashrc])
        if re.search(re_timeout,reply):
            print 'timed out'
            success = False
        if re.search(re_hosterr,reply):
            #raise AuthenticationError
            print 'authentication error'
            success = False
        if re.search(re_authen,reply):
            chars = write(fd,'yes')
            #print chars
            reply += readtillexpect(fd,[re_pass,re_log])
            #print reply
        if re.search(re_pass,reply):
            chars = write(fd,self.pswd)
            #print chars
            reply += readtillexpect(fd,[self.login,re_permdenied])
            #print reply
        if re.search(re_permdenied,reply):
            print 'authentication error'
            success = False
        if re.search(re_bad_bashrc,reply) :
            success = False
            print 'bad bashrc file'
        if re.search(self.login,reply) and success:
            success = True
        else:
            print 'wonder wats happening!!!!!!!'
            print reply
            success = False
            #sys.exit(1)
        return success

if __name__=='__main__':
    test = SSH(sys.argv[1],sys.argv[2])
    test.fork()
    
            
        
        

