import sys
import time


#print 'stdin:', sys.stdin.read()
print 'stdout'
print >> sys.stderr, 'stderr'

time.sleep(3)

print 'wakeup'
