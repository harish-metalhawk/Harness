User Manual for the Harness

command line option(alternately use harness.py -h for help)

1)"-d" : which runs the harness in the daily build detection mode, i.e., it launches set of jobs till a new build is ready and then relaunches the same jobs with the new build

2)"-m" : path to the master conf file(compulsary)

3)"-p" : path to where the build detection should be done, by default it is main-dev

4)"-n" : This option makes the harness run in plain mode that is with no build detection 

5)"-c" : which runs the harness with the currently available lates build

Brief description :

1) "-d" : when run in this mode the SANDBOX variable is exported , which could be used by the Jobs , for example to get java -version for a new build,

your command will be something like :
${SANDBOX}/azlinux/j2sdk1.6/x86_64/product/bin/java -version

2)"-m" : all the configuration files of the jobs are declared in master conf file ,each line can have path to one conf file or if there are master and slave jobs ,they should be seperated by "->" (with no spaces)

Decription on conf file:

contents
1)user
2)host
3)path
4)command
5)dur
6)delay
7)restart
8)port

parameters from 1 to 4 are compulsary

1)user : The user name with which the ssh has to be done

2)host : machine for ssh

3)path : The path from where the command has to be launched, more importantly cannot be blank or undefined

4)command : The simple command which is same as the one used to launch the desired job manually in a terminal.

5)dur : This parameters controls the duration for which the job has to be run(in mins) by default its set to zero

6)delay : This parameter controls the time delay before the job is started (in mins), default is zero

7)restart : This parameters sets the no of times the job has to be restarted in case of premature end of the job(like in case of a crash),by default 0

8)port : It can be set if the job uses a port like in case of app-servers and then any dependent jobs will be queued until the port is established, by default turned off( 0=> turn off, < int numbers > => port monitor is on )

Menu
---

Hitting the cntrl-c takes you to the menu of the harness which enables to kill, restart, reconfigure the apps

