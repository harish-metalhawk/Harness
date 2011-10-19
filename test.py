#!/home/buildmaster/sw/python/2.6.5/linux/x86_64/bin/python2.6
from changet_harness2 import implemtation
from adv_auto_start import check_for_new_build,get_latest_build

def parser():
    parse = optparse.OptionParser(usage='fix this')
    parse.add_option('-r',dest='restart',type='int',default=0)
    parse.add_option('-b',dest='build',type='string',default='main-dev')
    parse_add_option('-m',dest='conf',type='string')

build = check_for_new_build(get_latest_build())
implemtation(build)
