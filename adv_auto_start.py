#!/home/buildmaster/sw/python/2.6.5/linux/x86_64/bin/python2.6
'''usage <executable> <duration> <job>'''
'''In case for test purspose uncomment line #83 and comment out  rest of the lines'''
import subprocess,os,sys
from threading import Thread
from time import sleep
from datetime import datetime
import re
class MyThreadOb(Thread):
    def __init__(self,cmd):
        self.proc = None
        self.cmd = cmd.split()
        self.isStarted = False
        Thread.__init__(self)

    def run(self):
        self.proc = subprocess.Popen(self.cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.isStarted = True

    def isProcessStarted (self):
        return self.isStarted

    def check_state(self):
        ret = None
        if self.isStarted :
            ret = self.proc.poll()
        return ret

    def kill_proc(self):
        print 'PROC-ID=',self.proc.pid
        #kill_job = subprocess.Popen(['kill', '-9', str(self.proc.pid)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if self.isStarted and self.proc.poll() == None:
            self.proc.kill()

def fire_up_a_job():
    obj = MyThreadOb(sys.argv[2])
    obj.start()
    while (not obj.isProcessStarted()):
        pass
    time_check=1
    sleep_time= int(sys.argv[1])/10
    #print sleep_time
    while obj.check_state() is None and time_check<=10:
        sleep(sleep_time)
        #print time_check
        time_check +=1
    if obj.check_state() is  None:
        print " gonna kill the proc"
        obj.kill_proc()
    return

def check_for_build_complete(new):
    while True:
        if os.path.exists(new + "/sandbox/logs/buildstatusemail/buildstatusemail.ready"):
            print(str(datetime.now())+" : Build ready for rock and roll!!!")
            return
        sleep(1800)
        #print(str(datetime.now())+" : build not ready yet")

def get_latest_build(path="/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/latest"):
    proc = subprocess.Popen(["ls","-lrt",path,],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    k= str(proc.communicate()[0])
    if proc.returncode != 0:
        print 'The path for build detection is invalid'
        sys.exit(1)
    #print(k)
    k = re.match(".*[-][>][\s](.*)",k)
    return k.group(1)

def check_for_new_build(old,path="/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/latest"):
    new=''
    #old='/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/avm-x86-1269/'
    while True :
        new=get_latest_build(path)
        if not ( re.match(new,old)):
            old = new 
            #print(str(datetime.now())+" : finally!!! a new build:)")
            check_for_build_complete(new)
            #fire_up_a_job()
            break
        sleep(1800)
        #print(str(datetime.now()) + " : No new build yet:(")
    return new
def get_current_build(path="/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/latest"):
    return get_latest_build(path)
'''incase for an immediate test uncomment the next line and comment the remaining lines
updated usage
1) use just get_latest_build() to get the current build and check_for_new_build() for finding the next build by passing the get_latest_build() as the argyment'''
#check_for_new_build(get_latest_build())#'/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/avm-x86-1338/')
#while True:
     #check_for_new_build(get_current_build())


