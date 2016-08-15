#!/usr/bin/env python

"""Doc.py

> python Doc.py -h
"""

import os
import shutil
import sys
import time

import FixPath
import MiddleKit
from MiscUtils.Funcs import valueForString
from WebUtils.Funcs import htmlEncode


class Doc(object):

    sourceStyleSheetFilename = 'GenDocStyles.css'  # in MiddleKit/Design/
    destStyleSheetFilename = 'Styles.css'
    otherKeys = 'isDerived Min Max Enums'.split()

    def main(self, args=None):
        self.progPath = os.path.join(os.getcwd(), sys.argv[0])

        self.otherKeys = self.otherKeys  # pick up class level value
        self.parseArgs(args)

        modelName = self.args.get('model')
        if not modelName:
            classesName = self.args.get('classes')
            if not classesName:
                self.usage('No model or classes file specified.')

        outDir = self.args.get('outDir', os.curdir)
        self.requireDir(outDir)

        outDir = os.path.join(outDir, 'GeneratedDocs')
        self.requireDir(outDir)

        self.outDir = outDir

        from MiddleKit.Core.Model import Model
        if modelName:
            self.model = Model(modelName, havePythonClasses=False)
        else:
            self.model = Model(classesFilename=classesName,
                havePythonClasses=False)

        source = os.path.join(os.path.dirname(self.progPath),
            self.sourceStyleSheetFilename)
        dest = os.path.join(outDir, self.destStyleSheetFilename)
        shutil.copyfile(source, dest)

        #self.dump()
        self.generateHTML()

    def generateHTML(self):
        path = os.path.join(self.outDir, self.model.name()+'.html')
        wr = open(path, 'w').write
        wr('''
<html>

<head>
<link rel="stylesheet" type="text/css" href="%s">
</head>

<body>
<a name=#top></a>
''' % self.destStyleSheetFilename)

        wr('<div class="head1">%s Model (MiddleKit)</div>\n'
            % self.model.name())
        wr('Generated on %s <br>\n' % time.asctime())
        wr('From %s <br>\n' % self.model.filename())

        wr('<br>\n')

        wr('<table>\n')
        wr('<tr class="Class">'
            '<td class="ClassName" colspan="3">Classes</td></tr>\n')
        wr('<tr class="AttrTitles"><td class=AttrTitles>In Alpha Order</td>'
            '<td class="AttrTitles">In Inheritance Order</td></tr>\n')
        wr('<tr><td style="vertical-align:top">\n')
        klasses = self.model.allKlassesInOrder()
        for klass in sorted(klasses, key=lambda klass: klass.name().lower()):
            name = klass.name()
            wr('<a href="#%s">%s</a><br>\n' % (name, name))
        wr('<td style="vertical-align:top">')
        for klass in klasses:
            if not klass.superklass():
                self.writeKlassLinkAndRecurse(wr, klass)
        wr('</table>\n')

        for klass in klasses:
            name = klass.name()
            wr('''
<a id="%(name)s"></a>
<table class="Class">
<tr class="ClassName">
    <td class="ClassName" colspan="7">
        <table style="width:100%%">
            <tr>
                <td class="ClassName">%(name)s</td>
                <td class="Top" style="text-align:right"><a href="#top">top</a></td>
            </tr>
        </table>
    </td>
</tr>
            ''' % locals())

            wr('<tr class="ClassInfo"><td class="ClassInfo" colspan="7">\n')

            # ancestor classes
            wr('<table>\n')
            if klass.get('isAbstract'):
                wr('<tr><td style="vertical-align:top">abstract:</td>'
                    '<td style="vertical-align:top">yes</td></tr>\n')
            wr('<tr><td style="vertical-align:top">ancestors:</td>'
               '<td style="vertical-align:top">')
            ancestor = klass.superklass()
            if ancestor:
                while ancestor:
                    name = ancestor.name()
                    wr(' <a href="#%s">%s</a>&nbsp;' % (name, name))
                    ancestor = ancestor.superklass()
            else:
                wr('none')
            wr('</td></tr>\n')

            # subclasses
            wr('<tr><td style="vertical-align:top">subclasses:</td>'
               '<td style="vertical-align:top">\n')
            if klass.subklasses():
                for subklass in klass.subklasses():
                    name = subklass.name()
                    wr('<a href="#%s">%s</a>&nbsp;' % (name, name))
            else:
                wr('none')
            wr('</td></tr>\n')

            # notes
            wr('<tr> <td style="vertical-align:top">notes:</td>'
               '<td style="vertical-align:top">')
            if klass.get('Notes'):
                wr(htmlEncode(klass['Notes']))
            else:
                wr('none')
            wr('</td></tr>\n')

            wr('</table>\n')

            wr('''
<tr class="AttrTitles">
<td class="AttrTitles">Name</td>
<td class="AttrTitles">Type</td>
<td class="AttrTitles">IsRequired</td>
<td class="AttrTitles">Default</td>
<td class="AttrTitles">Notes</td>
</tr>
''')

            for attr in klass.allAttrs():
                # print attr
                values = Values(attr)
                if attr.klass() is klass:
                    values['Prefix'] = ''
                else:
                    values['Prefix'] = 'Inh'
                values['Type'] = attr.htmlForType()
                wr('''
<tr class="Attr">
<td class="%(Prefix)sAttrName">%(Name)s</td>
<td class="%(Prefix)sAttr">%(Type)s</td>
<td class="%(Prefix)sAttr">%(isRequired)s</td>
<td class="%(Prefix)sAttr">%(Default)s</td>
''' % values)
                notes = []
                if attr.get('Notes'):
                    notes.append(htmlEncode(attr.get('Notes')))
                for key in self.otherKeys:
                    if attr.get(key) is not None:
                        notes.append('%s = %s' % (key, attr[key]))

                if notes:
                    notes = '<br>'.join(notes)
                    notes = mystr(notes)
                    values['Notes'] = notes
                    # wr('<tr class=Attr><td class=%(Prefix)sAttr>&nbsp;</td>'
                    # '<td class=%(Prefix)sAttrNotes colspan=7>%(Notes)s</td>'
                    # '</tr>\n' % values)
                    wr('<td class="%(Prefix)sAttrNotes">%(Notes)s</td>\n' % values)
                else:
                    wr('<td class="%(Prefix)sAttrNotes">&nbsp;</td>\n' % values)
                wr('</tr>')
            wr('</table>\n')
        wr('</body></html>\n')


    def writeKlassLinkAndRecurse(self, wr, klass, level=0):
        wr('&nbsp;'*level*4)
        name = klass.name()
        wr('<a href="#%s">%s</a><br>\n' % (name, name))
        level += 1
        for klass in klass.subklasses():
            self.writeKlassLinkAndRecurse(wr, klass, level)


    def dump(self):
        """Dump the class and attribute definitions in order.

        This is a simple example that you could expand to generate your own
        brand of HTML or some other output format.
        """
        for klass in self.model.allKlassesInOrder():
            print klass
            for attr in klass.allAttrs():
                print attr

    def requireDir(self, d):
        if not os.path.exists(d):
            os.mkdir(d)
        elif not os.path.isdir(d):
            print 'Error: Output target, %s, is not a directory.' % d

    def parseArgs(self, args):
        self.parseGenericArgs(args)
        args = self.args

        if 'otherkeys' in args:
            self.otherKeys = args['otherkeys']
            if isinstance(self.otherKeys, basestring):
                self.otherKeys = self.otherKeys.split()

        if 'morekeys' in args:
            moreKeys = args['morekeys']
            if isinstance(moreKeys, basestring):
                moreKeys = moreKeys.split()
            self.otherKeys += list(moreKeys)

    def parseGenericArgs(self, args):
        if args is None:
            args = sys.argv[1:]
        values = {}
        for arg in args:
            parts = arg.split('=', 1)
            if len(parts) == 2:
                values[parts[0].lower()] = valueForString(parts[1])
            else:
                values[parts[0].lower()] = True
        self.args = values

    def usage(self, errorMsg=None):
        progName = os.path.basename(sys.argv[0])
        if errorMsg:
            print '%s: error: %s' % (progName, errorMsg)
        print '''
USAGE:
  %(progName)s model=FILENAME [OPTIONS]
  %(progName)s classes=FILENAME [OPTIONS]

OPTIONS:
  [outDir=DIRNAME] [moreKeys="foo bar"] [otherKeys="foo bar"]

NOTES:
  * If outDir is not specified, then the base filename
    (sans extension) is used.
  * GeneratedDocs is appended to the output directory.
  * The Notes column will also include the other keys:
    isDerived, Min, Max and Enums.
  * You can redefine those keys with the otherKeys argument.
  * But more typically, you would use moreKeys to _add_ keys
    specific to your model (i.e., user-defined rather than
    MiddleKit-defined).
''' % locals()
        print
        sys.exit(1)


class Values(dict):

    def __init__(self, data):
        dict.__init__(self, data)
        self['isRequired'] = 'required' if self.get('isRequired') not in (
            False, '0', 0, 0.0, None) else ''

    def __getitem__(self, key):
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            value = None
        if value is None:
            value = '&nbsp;'
        return value


def mystr(s):
    """Convert a Unicode string to a basic string."""
    try:
        return str(s)
    except UnicodeError:
        s = s.replace(u'\u201c', '"').replace(u'\u201d', '"')
        try:
            return str(s)
        except UnicodeError:
            parts = []
            for c in s:
                try:
                    parts.append(str(c))
                except UnicodeError:
                    parts.append(repr(c))
            return ''.join(parts)


def htmlForType(self):
    return self['Type']
from MiddleKit.Core.Attr import Attr
Attr.htmlForType = htmlForType

def htmlForType(self):
    return '<a href="#%s" class="ClassRef">%s</a>' % (
        self['Type'], self['Type'])
from MiddleKit.Core.ObjRefAttr import ObjRefAttr
ObjRefAttr.htmlForType = htmlForType

def htmlForType(self):
    return 'list of <a href="#%s" class="ClassRef">%s</a>' % (
        self.className(), self.className())
from MiddleKit.Core.ListAttr import ListAttr
ListAttr.htmlForType = htmlForType


if __name__ == '__main__':
    Doc().main(sys.argv)
