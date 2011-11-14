#!/usr/bin/python2.7
import optparse

def opts():
    parse = optparse.OptionParser(usage='%prog -m <Master conf path> -d <to run in smokes mode> -c <to pick the currently available latest build> -p <path to build detection> -n < to run harness in a plain mode>')
    parse.add_option('-d',dest='build',action='store_true',default=False,help="this option enables  \"smokes mode\"")
    parse.add_option('-m',dest='conf',type='string',help="This is a compulsary option which provides the path to master conf")
    parse.add_option('-c',dest='current',action='store_true',default=False,help="This is options makes the jobs run in the currently available latest builds")
    parse.add_option("-p",dest='path',type='string',default="/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/latest",help='this option sets the path of the branch to look out for new build , by default its the main-dev build')
    parse.add_option('-n',dest='plain',action='store_true',default=True,help="this mode makes the application run as a simple harness without any build-detection")
    if parse.parse_args()[0].build or parse.parse_args()[0].current:
        parse.parse_args()[0].plain = False
    if parse.parse_args()[0].plain and ( parse.parse_args()[0].build or parse.parse_args()[0].path != "/home/buildmaster/nightly/AVM/main-dev-x86/in_progress/latest") :
        parse.error("incompatible options")
    if parse.parse_args()[0].conf is None :
        parse.error("invalid arguments")
    if parse.parse_args()[0].current and parse.parse_args()[0].plain :
        parse.error("plain harness and build detection cannot exist together,conflicting options passed")
    return parse.parse_args()


if __name__ == '__main__':
    print opts()[0]

    
