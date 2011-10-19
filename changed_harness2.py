#!/usr/bin/python2.6
import os,sys,time,thread,select,re,threading,socket
from ssh import SSH
from readnwrite import unblocked_read
from threading import Thread
from Queue import Queue
import logging,exceptions
'''FIX ME
1)Remove all the global variables and make it static.
2)Any bugs while interaction with the menu is highly probable because of the merry go round of the functions of that  part.. watch it.
3)Temporary fix for the build detection
newly added code include controlled and timed number of cntrl-c and making the slave exit when master is dead during the master_wait sleep and also handled the race between the master thread and slave thread during the restarts

'''
done = False
kill = False
JOB_HASH = []
KILL_DICT = {}
DONE_HASH = []
cid=[]  #list of all currently running jobs
pending_jobs= []  #list of all queued jobs
#pending_jobs= 0
DYN_RESTART = {} #dict of the conf file name and its coressponding arguments to the Job object
dead_jobs = set()  #set of all dead jobs
ALL_JOBS = {}   #dict of all the conf files and corresponding job id's
DEPENDENCY_DICT = {} #dict of conf files , with keys as their master's job-id
BUILD_KILL=False # this should be used by externel code for the auto stop of the all apps running,don't mess with this


class BuildRestart(exceptions.Exception):
    def __init__(self):
        return
    
    def __string__(self):
        print 'somebody called the BUILD_KILL'

class Job(Thread):

    def readconf(self,path):
        std_keys = ['user','host','path','command','logs','dur','delay','pass','port']
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
                    pass
            for l in confs.iterkeys():
                if l not in std_keys:
                    print 'bad conf file(opts), please check the usage'
            for val,keys in confs.iteritems():
                self.validate_conf(confs,std_keys)
            return confs

    def validate_conf(self,confs,std_keys):
        if len(std_keys) != len(confs):
                self.CONF_GOOD = False
        for keys in confs.iterkeys():
            if keys not in std_keys:
                self.CONF_GOOD = False
        for keys,vals in confs.iteritems():
            if not re.match('^(user|host|path|command|logs|dur|delay|pass|port)$',keys):
                self.CONF_GOOD = False
            if re.match('^(dur|delay)$',keys):
                try:
                    float(vals)
                except:
                    self.CONF_GOOD = False
                    pass

                

    def __init__(self,items):
        global KILL_DICT,DONE_HASH
        self.CONF_GOOD=True
        self.tdata=''
        #self.build = buid
        path,self.JOB_ID,self.MASTER_ID,self.build,self.restart_attempts = items
        DONE_HASH[self.JOB_ID] = False
        self.path = path
        self.conf=self.readconf(path)
        KILL_DICT[self.path] = False
        kill = False
        print self.path,DONE_HASH[self.JOB_ID],KILL_DICT[self.path] 
        if self.CONF_GOOD:
            self.initialize(path)
            Thread.__init__(self)

    def initialize(self,path):
        user = self.conf['user'].rstrip('\n')
        self.user = user
        host = self.conf['host'].rstrip('\n')
        self.host = host
        self.EXPECT=user+'@'+host
        self.port = int(self.conf['port'].rstrip('\n'))
        self.log = self.conf['logs'].rstrip('\n')
        self.duration = float(self.conf['dur'].rstrip('\n'))
        self.time_handling = False
        self.sleep_time = float(self.conf['delay'].rstrip('\n'))
        if self.duration > 0:
            self.time_handling = True
        self.arg= user+'@'+host
        self.process_alive = True
        self.process_killed= False
        self.PORT_OPEN = False
        self.allIsWell = True
        self.is_slave = False
        self.is_restart = True
        #self.restart_attempts = 3

    

    def wait_till_master(self):
        global JOB_HASH
        self.is_slave = True
        while not JOB_HASH[self.MASTER_ID] and not (kill or KILL_DICT[self.path]) and not DONE_HASH[self.MASTER_ID]:
            time.sleep(3)
        print JOB_HASH[self.MASTER_ID],(kill or KILL_DICT[self.path]),DONE_HASH[self.MASTER_ID],'\t somebody woke me up',self.path

    def run(self):
        global cid
        global pending_jobs   #highly thread unsafe, but for now living with it.
        if self.sleep_time > 0:
            self.delay()
        #if not (kill or KILL_DICT[self.path]):
        if self.MASTER_ID != -1:
            #pending_jobs += 1
            pending_jobs.append(self.path)
            self.wait_till_master()
            #pending_jobs -= 1
            pending_jobs.remove(self.path)
        if not (kill or KILL_DICT[self.path]):
            cid.append(self.path)
            #print 'appended!!!!!!',self.path
            #print self.MASTER_ID
            sshOb = SSH(self.host,self.user,self.conf['pass'])
            self.pid,fd,success = sshOb.fork()
            print '---------------',success
            #print fd
            if success:
                self.parent_processing(fd)
            else:
                cid.remove(self.path)
        DONE_HASH[self.JOB_ID] = True
        dead_jobs.add(self.path)


    def parent_processing(self,fd):
        global cid
        global DONE_HASH
        #print self.ident
        if self.time_handling:
            self.spawn_timer()
        if self.build != '' :
            self.conf['command'] = 'SANDBOX='+self.build+'/sandbox '+self.conf['command']
        #cid.append(self.pid) #appending the child process id for safe clean-up
        if self.allIsWell:
            self.write(fd,'cd '+ self.conf['path'])
            self.readtillexpect(fd,self.EXPECT) #If there is issue in the expect ,where the second time read directly results in the expect which is a bogus one bcoz of the previous command to change the path, simple fix would be to do a read by select method for a period of time so the fd is emptied.
            #self.backup_read(fd)
            unblocked_read(fd,1024,3)
            self.write(fd,self.conf['command'])
            if int(self.port) != 0 :
                self.port_monitor()
            else:
                JOB_HASH[self.JOB_ID] = True #this should have been under else statement
            #self.unblocking_read3(fd,output,data)
            self.readtillexpect(fd,self.EXPECT,True)
        self.process_killed = True
        cid.remove(self.path)
        #cid.pop()
        JOB_HASH[self.JOB_ID] = False
        #print 'a value popped',self.path
        DONE_HASH[self.JOB_ID] = True

    def backup_read(self,fd):
        rd,rd,wt = select.select([fd],[],[],5)
        if fd in rd:
            return os.read(fd,1024)
        else:
            return ''

    def write(self,fd,cont):
        if not cont.endswith('\n'):
            cont += '\n'
        chars = os.write(fd,cont)
        time.sleep(1)
        return chars

    def readtillexpect(self,fd,expect,log=False):
        global done,kill,KILL_DICT
        assert isinstance(expect,str)
        try:
            fi = self.openlog(self.log,'w',1024,log)
            reply = ''
            self.restarted_times = 0
            has_restarted = False
            self.file_size = 0
            max_kill_attempts = 60
            kill_attempts = 0
            self.max_file_size = 100**4
            while True:
                if has_restarted:
                    self.write(fd,self.conf['command'])
                    reply = ''
                    has_restarted = False
                    self.log = self.log+'.'+str(self.restarted_times)
                    fi = self.openlog(self.log,'w',1024,log)
                if kill or KILL_DICT[self.path] or (self.is_slave and not JOB_HASH[self.MASTER_ID]): #can be argued to be wrong implementation but logically correct as it is used in logical and only if it is a slave the second part i.e., JOB_HASH[self.master_id] is checked
                    #print 'got a kill signal'
                    self.write(fd,'\x03')
                    time.sleep(4)
                    kill_attempts += 1
                    print 'no of attempts :',kill_attempts
                rd,wt,ex = select.select([fd],[],[],.1)
                if fd in rd:
                    rep = os.read(fd,1024)
                    rep.replace('\r','')
                    #print rep,
                    self.writelog(fi,rep,log)
                    if log and self.file_size > self.max_file_size:
                        fi = self.file_ops(fi)
                    reply += rep
                    self.file_size += len(rep)
                if re.search(expect,reply) or kill_attempts > max_kill_attempts:
                    #rep = self.backup_read(fd) # A rather more cautious read to make sure the buffer is cleared up
                    rep = unblocked_read(fd,1024,3)
                    self.writelog(fi,rep,log)
                    kill_attempts = 0
                    if self.restart(log):
                        has_restarted = True
                        continue
                    break
        finally:
            self.closelog(fi)

    def restart(self,log):
        if kill or KILL_DICT[self.path] or (self.is_slave and not JOB_HASH[self.MASTER_ID]) or not (self.is_restart and self.restart_attempts > 0 and self.restarted_times < self.restart_attempts) or not log:
            return False
        self.restarted_times += 1
        return True


    def openlog(self,fname,mode,bsize,log):
        if log:
            return  open(fname,mode,bsize)

    def closelog(self,fi):
        try:
            fi.close()
        except:
            pass

    def writelog(self,fi,wt,log):
        if log:
            fi.write(wt)


    def export_sandbox(self,fd):
        self.blocked_read_write(fd,1024,'export SANDBOX='+sys.argv[1]+'\n')
        


    def port_monitor(self):
        monitor = Thread(target = self.pmonitor)
        monitor.daemon=True
        monitor.start()
    
    def pmonitor(self):
        global JOB_HASH
        while not self.port_scan(self.host,self.port) :
            #print 'port not established yet'
            time.sleep(2)
        #print 'Did I reach here????'
        JOB_HASH[self.JOB_ID] = True
        #print 'finally!!!!11 port esatblished'

    def port_scan(self,host,port):
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            s.connect((host,int(port)))
            s.shutdown(2)
            return  True
        except:
            return False


    def spawn_timer(self):
        k = Thread(target = self.handle_time_dur, args=(self.duration,self.pid))
        k.start()

    def handle_time_dur(self,dur,pid):
        max_sleep = float(dur)*60
        sleep_count=0
        while not self.process_killed and sleep_count < max_sleep and not (kill or  KILL_DICT[self.path]):
            time.sleep(1)
            sleep_count +=1
        KILL_DICT[self.path] = True
        #try:
            #os.kill(pid,9)
            #self.process_killed = True
        #except:
            #print 'handle this baby'


    def delay(self):
        global pending_jobs
        max_sleep = float(self.sleep_time)*60
        sleep_count = 0
        #pending_jobs += 1
        pending_jobs.append(self.path)
        while sleep_count < max_sleep  and not (kill or  KILL_DICT[self.path]):
            time.sleep(1)
            sleep_count += 1
        #pending_jobs -= 1
        pending_jobs.remove(self.path)

    def kill_child(self,child_pid):
        os.kill(child_pid,9)


    def file_ops(self,fh):
        fh.close()
        self.rotate_file(fh)  #implemented new file rotate method
        fh = open(self.log,'a',1024)
        self.file_size = 0
        return fh

    def rotate_file(self,fh):
        rotate_fi = open(self.log)
        full = rotate_fi.readlines()
        rotate_fi.close()
        rotate_fi = open(self.log,'w')
        rotate_fi.writelines(full[-300:])
        rotate_fi.close()

        


    def check_process_alive(self):
        try:
            os.kill(self.pid,0)
            self.process_alive = True
        except:
            self.process_alive = False 

def kill_menu():
    global KILL_DICT
    print '================================='
    print '1) To kill all running apps type "all" and exit\n2) To kill an app type "kill"\n3) To resume type "resume"\n4) To see the list of running and queued process type "list"\n5) To restart a dead job enter "restart"\n6) To dynamically reconfigure the conf file type "reconf"'
    val = str(raw_input('-> ')) #needs to be fixed, in a rare occassion all apps may be dead but the main thread is blocked for a raw_input
    val = val.rstrip('\n')
    if val != 'all' and val != 'resume' and  val != 'kill'  and val != 'list' and val != 'restart' and val != 'reconf':
        kill_menu()
    else:
        clean_up(val)

def current_jobs():
    global cid
    print 'Current jobs: ',[ i  for i in cid ],'\tPending jobs: ',[ i  for i in pending_jobs ],'\tDead Jobs: ',[i for i in dead_jobs] #if found buggy use if cid!='' in bot the for loops respectively

def clean_up(val):
    global cid,kill,DONE_HASH,KILL_DICT
    #val = kill_menu()
    if val == 'all':
        #kill = True
        #time.sleep(2)     #for a rare race condition where after a restart  the job thread has not yet updated the kill or KILL_DICT values but the main thread exists bcoz of the past values, probably seen if only one conf file is used
        #while False in DONE_HASH:
            #time.sleep(1)
        #kill_all_procs(cid)
        kill_all()
        sys.exit()
    elif val == 'resume':
        signal_handle()
    elif val == 'list':
        current_jobs()
    elif val == 'restart':
        handle_dynrestart()
    elif val == 'kill':
        kill_display()
        #KILL_DICT[val] = True
        #if len(cid) > 1:
            #kill_menu()
        #signal_handle()
    elif val == 'reconf':
        handle_reconf()
    else :
        print 'invalid selection'
        kill_menu()
    signal_handle()

def kill_all():
    global cid,kill,DONE_HASH,KILL_DICT
    kill = True
    time.sleep(2)     #for a rare race condition where after a restart  the job thread has not yet updated the kill or KILL_DICT values but the main thread exists bcoz of the past values, probably seen if only one conf file is used
    while False in DONE_HASH:
        time.sleep(1)
    kill_all_procs(cid)

def handle_reconf():
    global ALL_JOBS,KILL_DICT,DONE_HASH,dead_jobs
    reconf_val = raw_input('Enter the conf file name to be reconf or exit to exit to main menu\n-> ')
    if reconf_val == 'exit':
        kill_menu()
    if reconf_val not in ALL_JOBS.iterkeys():
        print 'wrong conf file name'
        kill_menu()
    else:
        KILL_DICT[reconf_val] = True
        while not DONE_HASH[ALL_JOBS[reconf_val]]:
            time.sleep(2)
        dynamic_restart(reconf_val)
        dead_jobs.discard(reconf_val)
    signal_handle()

def kill_display():
    kill_val = raw_input('Enter the conf file name to be killed or exit to exit to main menu\n-> ')
    if kill_val == 'exit':
        kill_menu()
    if kill_val not in KILL_DICT.keys():
        print 'invalid conf file name'
        kill_menu()
    else:
        KILL_DICT[kill_val] = True
    signal_handle()

def kill_all_procs(cid):
    for processes in cid:
        try:
            os.kill(processes,9)
        except: 
            pass
            #print 'done'

def check_num_jobs(li):
    jobs = li.split('->')
    return jobs,len(jobs)

def signal_handle():
    global cid,dead_jobs,BUILD_KILL
    try:
        while True :#threading.active_count()>1:
            if BUILD_KILL:
                kill_all()
                raise BuildRestart 
            thread_no =  threading.enumerate()[1:]
            #print thread_no
            print 'number of current jobs: ',len(cid),'\tnumber of queued jobs: ',len(pending_jobs),'\tnumber of dead jobs: ',len(dead_jobs)
            #if len(cid)==0 and len(pending_jobs) == 0:
                #raise KeyboardInterrupt
            time.sleep(4)
    except KeyboardInterrupt:
        try:
            kill_menu()
        except KeyboardInterrupt:
            pass

def getconf(path,build,restart):
    global DYN_RESTART
    KILL_DICT = {}
    q = Queue()
    with open(path) as fi:
        li = fi.readlines()
        job_id = 0
        for i in li:
            s,le = check_num_jobs(i.rstrip('\n'))
            for r in s:
                pu = r,job_id,-1 if s.index(r) == 0 else (job_id-1),build,restart
                ALL_JOBS[r] = job_id
                DYN_RESTART[r] = pu
                KILL_DICT[r] = False
                if  s.index(r) != 0:
                    DEPENDENCY_DICT[job_id-1] = r #easier when the dict has job_id has key and conf file name has path
                q.put(pu)
                job_id += 1
    return q,KILL_DICT,job_id

def fireJobs(q):
    while not q.empty():
        try:
            o = q.get()
            th = Job(o)#q.get())
            try:
                th.daemon=True
            except:
                print 'bad conf file(%s)' %o
                continue
            th.start()
        except KeyboardInterrupt: 
            sys.exit(1)

def handle_dynrestart():
    global dead_jobs,DEPENDENCY_DICT,ALL_JOBS
    if len(dead_jobs) == 0:
        print 'No dead jobs currently'
        signal_handle()
    value = raw_input('enter the dead job name to restart of exit to exit from the submenu\n->')
    if value not in dead_jobs or value == 'exit':
        print 'Failed to restart the job',value
    else:
        try:
            if ALL_JOBS[value] in DEPENDENCY_DICT.iterkeys() and DEPENDENCY_DICT[ALL_JOBS[value]] not in pending_jobs:     #wait till the dependent children are dead before restarting and also may throw a key error for the second validation
                print 'has a dependent'
                while  DEPENDENCY_DICT[ALL_JOBS[value]] not in dead_jobs: #hmmm now gotta handle slave thread starting up even before master has reset its value
                    print 'waiting for the child to die'
                    time.sleep(2)
                #dynamic_restart(DEPENDENCY_DICT[ALL_JOBS[value]])
                #dead_jobs.discard(DEPENDENCY_DICT[ALL_JOBS[value]])
                #time.sleep(2)
                #print '---testing the race condition'
        except KeyError:
            pass
        dynamic_restart(value)
        #dynamic_restart(DEPENDENCY_DICT[ALL_JOBS[value]]) moved up int the if block..... might not really matter much
        dead_jobs.discard(value)
        time.sleep(1) #trying to make sure the master thread resets its values  before the slave reads it
        dynamic_restart(DEPENDENCY_DICT[ALL_JOBS[value]]) #moving it back from block..... matters very much
        dead_jobs.discard(DEPENDENCY_DICT[ALL_JOBS[value]])
    signal_handle()

def dynamic_restart(valu):
    global DYN_RESTART
    q = Queue()
    q.put(DYN_RESTART[valu])
    fireJobs(q)

def implementation(conf,build = '',restart = 0):
    global DONE_HASH,JOB_HASH,KILL_DICT,job_id,cid
    q = Queue()
    q,KILL_DICT,job_id = getconf(conf,build,restart)
    [ (JOB_HASH.append(False),DONE_HASH.append(False)) for k in range(0,job_id) ]
    fireJobs(q)
    time.sleep(.5)  #To handle the race between main threads and child threads
    signal_handle()

if __name__ == '__main__':
    implementation(sys.argv[1])
