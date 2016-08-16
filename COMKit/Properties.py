name = 'COMKit'

version = (1, 2, 0)

docs = [
    {'name': "User's Guide", 'file': 'UsersGuide.html'},
]

status = 'stable'

synopsis = """COMKit allows COM objects to be used in the multi-threaded versions of WebKit. Especially useful for data access using ActiveX Data Objects. Requires Windows and Python win32 extensions."""

requiredPyVersion = (2, 6, 0)

requiredOpSys = 'nt'

requiredSoftware = [
    {'name': 'pythoncom'},
]

def willRunFunc():
    # WebKit doesn't check requiredSoftware yet. So we do so:
    try:
        # For reasons described in the __init__.py, we can't actually import
        # pythoncom here, but we need to see if the module is available.
        # We can use the "imp" standard module to accomplish this.
        import imp
        for soft in requiredSoftware:
            imp.find_module(soft['name'])
    except ImportError:
        success = False
    else:
        success = True
    if not success:
        return 'The pythoncom module (pywin32 library) is required to use COMKit.'
