#!/usr/bin/env python
# coding: utf-8

# Adopted from Ryan McGreal work:
# https://github.com/quandyfactory/dicttoxml/blob/master/dicttoxml.py

"""
Converts a Python dictionary or other native data type into a valid XML string.

Supports item (`int`, `float`, `long`, `decimal.Decimal`, `bool`, `str`, `unicode`, `datetime`, `none` and other number-like objects) and collection (`list`, `set`, `tuple` and `dict`, as well as iterable and dict-like objects) data types, with arbitrary nesting for the collections. Items with a `datetime` type are converted to ISO format strings. Items with a `None` type become empty XML elements.

This module works with both Python 2 and 3.
"""



__version__ = '1.7.4'
version = __version__

from random import randint
import collections
import numbers
import logging
from xml.dom.minidom import parseString


LOG = logging.getLogger("dicttoxml")

# python 3 doesn't have a unicode type
try:
    str
except:
    str = str

# python 3 doesn't have a long type
try:
    int
except:
    long = int


def set_debug(debug=True, filename='dicttoxml.log'):
    if debug:
        import datetime
        print(('Debug mode is on. Events are logged at: %s' % (filename)))
        logging.basicConfig(filename=filename, level=logging.INFO)
        LOG.info('\nLogging session starts: %s' % (
            str(datetime.datetime.today()))
        )
    else:
        logging.basicConfig(level=logging.WARNING)
        print('Debug mode is off.')


def unicode_me(something):
    """Converts strings with non-ASCII characters to unicode for LOG.
    Python 3 doesn't have a `unicode()` function, so `unicode()` is an alias
    for `str()`, but `str()` doesn't take a second argument, hence this kludge.
    """
    try:
        return str(something, 'utf-8')
    except:
        return str(something)


ids = [] # initialize list of unique ids

def make_id(element, start=100000, end=999999):
    """Returns a random integer"""
    return '%s_%s' % (element, randint(start, end))


def get_unique_id(element):
    """Returns a unique id for a given element"""
    this_id = make_id(element)
    dup = True
    while dup:
        if this_id not in ids:
            dup = False
            ids.append(this_id)
        else:
            this_id = make_id(element)
    return ids[-1]


def get_xml_type(val):
    """Returns the data type for the xml type attribute"""
    if type(val).__name__ in ('str', 'unicode'):
        return 'str'
    if type(val).__name__ in ('int', 'long'):
        return 'int'
    if type(val).__name__ == 'float':
        return 'float'
    if type(val).__name__ == 'bool':
        return 'bool'
    if isinstance(val, numbers.Number):
        return 'number'
    if type(val).__name__ == 'NoneType':
        return 'null'
    if isinstance(val, dict):
        return 'dict'
    if isinstance(val, collections.Iterable):
        return 'list'
    return type(val).__name__


def escape_xml(s):
    if type(s) in (str, str):
        s = unicode_me(s) # avoid UnicodeDecodeError
        s = s.replace('&', '&amp;')
        s = s.replace('"', '&quot;')
        s = s.replace('\'', '&apos;')
        s = s.replace('<', '&lt;')
        s = s.replace('>', '&gt;')
    return s


def make_attrstring(attr):
    """Returns an attribute string in the form key="val" """
    attrstring = ' '.join(['%s="%s"' % (k, v) for k, v in list(attr.items())])
    return '%s%s' % (' ' if attrstring != '' else '', attrstring)


def key_is_valid_xml(key):
    """Checks that a key is a valid XML name"""
    LOG.info('Inside key_is_valid_xml(). Testing "%s"' % (unicode_me(key)))
    test_xml = '<?xml version="1.0" encoding="UTF-8" ?><%s>foo</%s>' % (key, key)
    try:
        parseString(test_xml)
        return True
    except Exception: # minidom does not implement exceptions well
        return False


def make_valid_xml_name(key, attr):
    """Tests an XML name and fixes it if invalid"""
    LOG.info('Inside make_valid_xml_name(). Testing key "%s" with attr "%s"' % (
        unicode_me(key), unicode_me(attr))
    )
    key = escape_xml(key)
    attr = escape_xml(attr)

    # pass through if key is already valid
    if key_is_valid_xml(key):
        return key, attr

    # prepend a lowercase n if the key is numeric
    if key.isdigit():
        return 'n%s' % (key), attr

    # replace spaces with underscores if that fixes the problem
    if key_is_valid_xml(key.replace(' ', '_')):
        return key.replace(' ', '_'), attr

    # key is still invalid - move it into a name attribute
    attr['name'] = key
    key = 'key'
    return key, attr


def wrap_cdata(s):
    """Wraps a string into CDATA sections"""
    s = unicode_me(s).replace(']]>', ']]]]><![CDATA[>')
    return '<![CDATA[' + s + ']]>'


def default_item_func(parent):
    return 'item'


def convert(obj, ids, attr_type, item_func, cdata, parent='root', namespace=''):
    """Routes the elements of an object to the right function to convert them
    based on their data type"""

    LOG.info('Inside convert(). obj type is: "%s", obj="%s"' % (type(obj).__name__, unicode_me(obj)))

    item_name = item_func(parent)

    if isinstance(obj, numbers.Number) or type(obj) in (str, str):
        return convert_kv(item_name, obj, attr_type, cdata, namespace=namespace)

    if hasattr(obj, 'isoformat'):
        return convert_kv(item_name, obj.isoformat(), attr_type, cdata, namespace=namespace)

    if type(obj) == bool:
        return convert_bool(item_name, obj, attr_type, cdata, namespace=namespace)

    if obj is None:
        return convert_none(item_name, '', attr_type, cdata, namespace=namespace)

    if isinstance(obj, dict):
        return convert_dict(obj, ids, parent, attr_type, item_func, cdata, namespace=namespace)

    if isinstance(obj, collections.Iterable):
        return convert_list(obj, ids, parent, attr_type, item_func, cdata, namespace=namespace)

    raise TypeError('Unsupported data type: %s (%s)' % (obj, type(obj).__name__))


def convert_dict(obj, ids, parent, attr_type, item_func, cdata, namespace=''):
    """Converts a dict into an XML string."""
    LOG.info('Inside convert_dict(): obj type is: "%s", obj="%s"' % (
        type(obj).__name__, unicode_me(obj))
    )
    output = []
    addline = output.append

    item_name = item_func(parent)

    for key, val in list(obj.items()):
        LOG.info('Looping inside convert_dict(): key="%s%s", val="%s", type(val)="%s"' % (
            unicode_me(namespace), unicode_me(key), unicode_me(val), type(val).__name__)
        )

        attr = {} if not ids else {'id': '%s' % (get_unique_id(parent)) }

        key, attr = make_valid_xml_name(key, attr)

        if isinstance(val, numbers.Number) or type(val) in (str, str):
            addline(convert_kv(key, val, attr_type, attr, cdata, namespace=namespace))

        elif hasattr(val, 'isoformat'): # datetime
            addline(convert_kv(key, val.isoformat(), attr_type, attr, cdata, namespace=namespace))

        elif type(val) == bool:
            addline(convert_bool(key, val, attr_type, attr, cdata, namespace=namespace))

        elif isinstance(val, dict):
            if attr_type:
                attr['type'] = get_xml_type(val)
            addline('<%s%s%s>%s</%s%s>' % (
                namespace, key, make_attrstring(attr),
                convert_dict(val, ids, key, attr_type, item_func, cdata, namespace=namespace),
                namespace, key
                )
            )

        elif isinstance(val, collections.Iterable):
            if attr_type:
                attr['type'] = get_xml_type(val)
            addline('<%s%s%s>%s</%s%s>' % (
                namespace, key,
                make_attrstring(attr),
                convert_list(val, ids, key, attr_type, item_func, cdata, namespace=namespace),
                namespace, key
                )
            )

        elif val is None:
            addline(convert_none(key, val, attr_type, attr, cdata, namespace=namespace))

        else:
            raise TypeError('Unsupported data type: %s (%s)' % (
                val, type(val).__name__)
            )

    return ''.join(output)


def convert_list(items, ids, parent, attr_type, item_func, cdata, namespace=''):
    """Converts a list into an XML string."""
    LOG.info('Inside convert_list()')
    output = []
    addline = output.append

    item_name = item_func(parent)

    if ids:
        this_id = get_unique_id(parent)

    for i, item in enumerate(items):
        LOG.info('Looping inside convert_list(): item="%s", item_name="%s", type="%s"' % (
            unicode_me(item), item_name, type(item).__name__)
        )
        attr = {} if not ids else { 'id': '%s_%s' % (this_id, i+1) }
        if isinstance(item, numbers.Number) or type(item) in (str, str):
            addline(convert_kv(item_name, item, attr_type, attr, cdata, namespace=namespace))

        elif hasattr(item, 'isoformat'): # datetime
            addline(convert_kv(item_name, item.isoformat(), attr_type, attr, cdata, namespace=namespace))

        elif type(item) == bool:
            addline(convert_bool(item_name, item, attr_type, attr, cdata, namespace=namespace))

        elif isinstance(item, dict):
            if not attr_type:
                addline('<%s%s>%s</%s%s>' % (
                    namespace, item_name,
                    convert_dict(item, ids, parent, attr_type, item_func, cdata, namespace=namespace),
                    namespace, item_name,
                    )
                )
            else:
                addline('<%s%s type="dict">%s</%s%s>' % (
                    namespace, item_name,
                    convert_dict(item, ids, parent, attr_type, item_func, cdata, namespace=namespace),
                    namespace, item_name,
                    )
                )

        elif isinstance(item, collections.Iterable):
            if not attr_type:
                addline('<%s%s %s>%s</%s%s>' % (
                    namespace, item_name, make_attrstring(attr),
                    convert_list(item, ids, item_name, attr_type, item_func, cdata, namespace=namespace),
                    namespace, item_name,
                    )
                )
            else:
                addline('<%s%s type="list"%s>%s</%s%s>' % (
                    namespace, item_name, make_attrstring(attr),
                    convert_list(item, ids, item_name, attr_type, item_func, cdata, namespace=namespace),
                    namespace, item_name,
                    )
                )

        elif item is None:
            addline(convert_none(item_name, None, attr_type, attr, cdata, namespace=namespace))

        else:
            raise TypeError('Unsupported data type: %s (%s)' % (
                item, type(item).__name__)
            )
    return ''.join(output)


def convert_kv(key, val, attr_type, attr={}, cdata=False, namespace=''):
    """Converts a number or string into an XML element"""
    LOG.info('Inside convert_kv(): key="%s", val="%s", type(val) is: "%s"' % (
        unicode_me(key), unicode_me(val), type(val).__name__)
    )

    key, attr = make_valid_xml_name(key, attr)

    if attr_type:
        attr['type'] = get_xml_type(val)
    attrstring = make_attrstring(attr)
    return '<%s%s%s>%s</%s%s>' % (
        namespace, key, attrstring,
        wrap_cdata(val) if cdata == True else escape_xml(val),
        namespace, key
    )


def convert_bool(key, val, attr_type, attr={}, cdata=False, namespace=''):
    """Converts a boolean into an XML element"""
    LOG.info('Inside convert_bool(): key="%s", val="%s", type(val) is: "%s"' % (
        unicode_me(key), unicode_me(val), type(val).__name__)
    )

    key, attr = make_valid_xml_name(key, attr)

    if attr_type:
        attr['type'] = get_xml_type(val)
    attrstring = make_attrstring(attr)
    return '<%s%s%s>%s</%s%s>' % (namespace, key, attrstring, str(val).lower(), namespace, key)


def convert_none(key, val, attr_type, attr={}, cdata=False, namespace=''):
    """Converts a null value into an XML element"""
    LOG.info('Inside convert_none(): key="%s"' % (unicode_me(key)))

    key, attr = make_valid_xml_name(key, attr)

    if attr_type:
        attr['type'] = get_xml_type(val)
    attrstring = make_attrstring(attr)
    return '<%s%s%s></%s%s>' % (namespace, key, attrstring, namespace, key)


def dicttoxml(obj, root=True, custom_root='root', ids=False, attr_type=False,
    item_func=default_item_func, cdata=False, namespace=''):
    """Converts a python object into XML.
    Arguments:
    - root specifies whether the output is wrapped in an XML root element
      Default is True
    - custom_root allows you to specify a custom root element.
      Default is 'root'
    - ids specifies whether elements get unique ids.
      Default is False
    - attr_type specifies whether elements get a data type attribute.
      Default is True
    - item_func specifies what function should generate the element name for
      items in a list.
      Default is 'item'
    - cdata specifies whether string values should be wrapped in CDATA sections.
      Default is False
    """

    if namespace != '':
      namespace_attribute = ' xmlns:{}="{}"'.format(namespace, namespace)
      namespace += ':'
      root = True
    else:
      namespace_attribute = ''

    LOG.info('Inside dicttoxml(): type(obj) is: "%s", obj="%s"' % (type(obj).__name__, unicode_me(obj)))
    output = []
    addline = output.append
    if root:
        addline('<?xml version="1.0" encoding="UTF-8" ?>')
        addline('<%s%s%s>%s</%s%s>' % (namespace, custom_root, namespace_attribute,
          convert(obj, ids, attr_type, item_func, cdata, parent=custom_root, namespace=namespace),
          namespace, custom_root))
    else:
        addline(convert(obj, ids, attr_type, item_func, cdata, parent='', namespace=namespace))
    return ''.join(output).encode('utf-8')
