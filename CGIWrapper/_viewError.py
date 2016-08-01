"""CGIWrapper view error file admin script."""

import os

filename = os.path.basename(fields['filename'].value)
filename = os.path.join(wrapper.setting('ErrorMessagesDir'), filename)
try:
    print open(filename).read()
except IOError:
    print 'Cannot read error file.'
