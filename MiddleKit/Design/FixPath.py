def FixPathForMiddleKit(verbose=0):
    """Enhance sys.path so that you can import MiddleKit.whatever.

    We *always* enhance the sys.path so that Generate.py is using the MiddleKit
    that contains him, as opposed to whatever happens to be found first in the
    Python path. That's an subtle but important feature for those of us who
    sometimes have more than one MiddleKit on our systems.
    """
    v = verbose
    import os, sys
    if '__file__' in globals():
        # We were imported as a module
        location = __file__
        if v:
            print 'took location from __file__'
    else:
        # We were executed directly
        location = sys.argv[0]
        if v:
            print 'took location from sys.argv[0]'

    location = os.path.join(os.getcwd(), location)

    if v:
        print 'location =', location
    if location.lower() == 'generate.py':
        # The simple case. We're at MiddleKit/Design/Generate.py
        location = os.path.abspath('../../')
    else:
        # location will basically be:
        # .../MiddleKit/Design/Generate.py
        if os.name == 'nt':
            # Case insenstive file systems:
            location = location.lower()
            what = 'middlekit'
        else:
            what = 'MiddleKit'
        if what in location:
            if v:
                print 'MiddleKit in location'
            location = location.split(what, 1)[0]
            if v:
                print 'new location =', location
        location = os.path.abspath(location)
        if v:
            print 'final location =', location
    sys.path.insert(1, location)
    if v:
        print 'path =', sys.path
        print
        print 'importing MiddleKit...'
    import MiddleKit
    if v:
        print 'done.'

FixPathForMiddleKit()
