"""ExpansiveHTMLForException.py

Create expansive HTML for exceptions using the CGITraceback module.
"""

from WebUtils import CGITraceback


HTMLForExceptionOptions = {
    'table': 'background-color:#F0F0F0;font-size:10pt',
    'default': 'color:#000000',
    'row.location': 'color:#000099',
    'row.code': 'color:#990000',
    'editlink': None,
}


def ExpansiveHTMLForException(context=5, options=None):
    """Create expansive HTML for exceptions."""
    if options:
        opt = HTMLForExceptionOptions.copy()
        opt.update(options)
    else:
        opt = HTMLForExceptionOptions
    return CGITraceback.html(context=context, options=opt)
