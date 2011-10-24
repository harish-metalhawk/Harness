#!/usr/bin/python2.7
import optparse

def opts():
    parse = optparse.OptionParser(usage='please read the usage by typing %prog -h')
    parse.add_option('-d',dest='build',action='store_true',default=False,help="this option enables  \"smokes mode\"")
    parse.add_option('-m',dest='conf',type='string',help="This is a compulsary option which provides the path to master conf")
    parse.add_option("-p",dest='path',type='string',default="/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/latest",help='this option sets the path of the branch to look out for new build , by default its the main-dev build')
    parse.add_option('-n',dest='plain',action='store_true',default=False,help="this mode makes the application run as a simple harness without any build-detection")
    if parse.parse_args()[0].plain and ( parse.parse_args()[0].build or parse.parse_args()[0].path != "/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/latest") :
        parse.error("incompatible options")
    if parse.parse_args()[0].conf is None :
        parse.error("invalid arguments")
    return parse.parse_args()


if __name__ == '__main__':
    print opts()[0]

    
