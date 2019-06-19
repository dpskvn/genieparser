''' show_context.py

Parser for the following show commands:
    * show context
    * show context detail
'''

import re
from genie.metaparser import MetaParser
from genie.metaparser.util.schemaengine import Schema, \
                                                Any, \
                                                Optional

# =============================================
# Schema for 'show context'
# =============================================
class ShowContextSchema(MetaParser):
    """Schema for
        * show context
    """
    schema = {
        Any(): {
            'candidate_default': bool,
            'class': str,
            'mode': str,
            'url': str,
            'interfaces': {
                Any(): {
                    'interface': str
                }
            }
        }
    }

# =============================================
# Parser for 'show context'
# =============================================
class ShowContext(ShowContextSchema):
    """Parser for
        * show context
    """

    cli_command = 'show context'

    def cli(self, output=None):
        if output is None:
            # excute command to get output
            out = self.device.execute(self.cli_command)
        else:
            out = output

        ret_dict = {}
        name = ''

        # pod1             default              Vlan100,Vlan200      Routed       disk0:/pod-context/pod1
        # pod2             111                  Vlan300,Vlan400      Routed       disk0:/pod-context/pod2
        # *admin            default              Vlan1000,Vlan1001,   Routed       disk0:/pod-context/admin.cfg
        #                                         Vlan1030,Vlan1031,
        #                                         Vlan1050,Vlan1051,
        #                                         Vlan1082,Vlan1083...
        p1 = re.compile(
            r'^(?P<name>(?!,)|\S+) *(?P<class>(?!,)|\S+) *(?P<interface>\S+) *'
            '(?P<mode>(?!,)|\S+) *(?P<url>(?!,)|\S+)$')

        for line in out.splitlines():
            line = line.strip()

            # pod1             default              Vlan100,Vlan200      Routed       disk0:/pod-context/pod1
            # pod2             111                  Vlan300,Vlan400      Routed       disk0:/pod-context/pod2
            # *admin            default              Vlan1000,Vlan1001,   Routed       disk0:/pod-context/admin.cfg
            #                                         Vlan1030,Vlan1031,
            #                                         Vlan1050,Vlan1051,
            #                                         Vlan1082,Vlan1083...
            m = p1.match(line)
            if m:
                groups = m.groupdict()
                if groups['name']:
                    if '*' in groups['name'][0]:
                        name = groups['name'][1:]
                        dict_name = ret_dict.setdefault(name, {})
                        dict_name.update({'candidate_default': True})
                    else: 
                        name = groups['name']
                        dict_name = ret_dict.setdefault(name, {})
                        dict_name.update({'candidate_default': False})
                    dict_name.update({'class': groups['class']})
                    dict_name.update({'mode': groups['mode']})
                    dict_name.update({'url': groups['url']})
                    dict_intefaces = dict_name.setdefault('interfaces', {})
                    interfaces = groups['interface']
                    if interfaces[-1] == ',':
                        interfaces = interfaces[:-1]
                    splitted_interface = interfaces.split(',')
                    for interface in splitted_interface:
                        dict_interface = dict_intefaces.setdefault(interface, {})
                        dict_interface.update({'interface': interface})
                else:
                    dict_name = ret_dict.setdefault(name, {})
                    dict_intefaces = dict_name.setdefault('interfaces', {})
                    interfaces = groups['interface']
                    if interfaces[-1] == ',':
                        interfaces = interfaces[:-1]
                    if interfaces[-3:] == '...':
                        interfaces = interfaces[:-3]
                    splitted_interface = interfaces.split(',')
                    for interface in splitted_interface:
                        dict_interface = dict_intefaces.setdefault(interface, {})
                        dict_interface.update({'interface': interface})
            continue

        return ret_dict

# =============================================
# Schema for 'show context detail'
# =============================================
class ShowContextDetailSchema(MetaParser):
    """Schema for
        * show context detail
    """
    schema = {
        Any(): {
            'id': int,
            'flags': str,
            'class': str,
            'context_created': bool,
            Optional('url'): str,
            Optional('interfaces'): {
                Optional('real_interfaces'): {
                    Any(): {
                        'real_interface': str
                    }
                },
                Optional('mapped_interfaces'): {
                    Any(): {
                        'mapped_interface': str
                    }
                }
            }
        }
    }

# =============================================
# Parser for 'show context detail'
# =============================================
class ShowContextDetail(ShowContextDetailSchema):
    """Parser for
        * show context detail
    """

    cli_command = 'show context detail'

    def cli(self, output=None):
        if output is None:
            # excute command to get output
            out = self.device.execute(self.cli_command)
        else:
            out = output

        ret_dict = dict_name = {}
        name = interfaces_sort = ''

        # Context "pod1", has been created
        # Context "null", is a system resource
        p1 = re.compile(
            r'^Context +\"(?P<name>\S+)\",* (?P<condition>.*)$')

        # Config URL: disk0:/pod-context/pod1
        # Config URL: ... null ...
        p2 = re.compile(
            r'^Config+ URL:+ (?P<url>.*)$')

        # Real Interfaces: Vlan100, Vlan200
        # Real Interfaces:
        p3 = re.compile(
            r'^Real+ Interfaces: *(?P<real_interfaces>.*)$')

        # Mapped Interfaces: Vlan100, Vlan200
        # Mapped Interfaces:
        p4 = re.compile(
            r'^Mapped+ Interfaces: *(?P<mapped_interfaces>.*)$')

        #  Vlan993, Vlan994, Vlan995, Vlan996, Vlan997, Vlan998, Vlan999
        p5 = re.compile(
            r'^(?P<interfaces>(\S+,)? *(\S+,)? *(\S+,)? *(\S+,)? *(\S+,)? *(\S+,)? *'
            '(\S+,)? *(\S+,)? *(\S+,)? *(\S+,)? *(\S+,)? *(\S+,)? *(\S+)? *)$')
        
        # Class: default, Flags: 0x00000111, ID: 1
        p6 = re.compile(
            r'^Class: *(?P<class>\S+), *Flags: *(?P<flags>\S+), *ID: *(?P<id>\d+)$')


        for line in out.splitlines():
            line = line.strip()

            # Context "pod1", has been created
            # Context "null", is a system resource
            m = p1.match(line)
            if m:
                groups = m.groupdict()
                if groups['name']:
                    name = groups['name']                         
                    dict_name = ret_dict.setdefault(name, {})
                    if 'created' in groups['condition']:
                        dict_name.update({'context_created': True})
                    else:
                        dict_name.update({'context_created': False})
                else:
                    dict_name = ret_dict.setdefault(name, {})
                continue

            # Config URL: disk0:/pod-context/pod1
            # Config URL: ... null ...
            m = p2.match(line)
            if m:
                groups = m.groupdict()
                if '... null ...' in groups['url']:
                    url = None
                else:
                    url = groups['url']
                    dict_name.update({'url': url})
                continue

            # Real Interfaces: Vlan100, Vlan200
            # Real Interfaces:
            m = p3.match(line)
            if m:
                groups = m.groupdict()
                if groups['real_interfaces']:
                    interfaces_sort = 'real_interfaces'
                    interface_sort = 'real_interface'
                    dict_real_interfaces = dict_name.setdefault('interfaces', {}). \
                    setdefault(interfaces_sort, {})
                    interfaces = groups['real_interfaces']
                    if interfaces[-1] == ',':
                        interfaces = interfaces[:-1]
                    interfaces = interfaces.replace(' ','')
                    splitted_interface = interfaces.split(',')
                    for interface in splitted_interface:
                        dict_interface = dict_real_interfaces.setdefault(interface, {})
                        dict_interface.update({'real_interface': interface})
                continue

            # Mapped Interfaces: Vlan100, Vlan200
            # Mapped Interfaces:
            m = p4.match(line)
            if m:
                groups = m.groupdict()
                if groups['mapped_interfaces']:
                    interfaces_sort = 'mapped_interfaces'
                    interface_sort = 'mapped_interface'
                    dict_real_interfaces = dict_name.setdefault('interfaces', {}). \
                    setdefault(interfaces_sort, {})
                    interfaces = groups['mapped_interfaces']
                    if interfaces[-1] == ',':
                        interfaces = interfaces[:-1]
                    interfaces = interfaces.replace(' ','')
                    splitted_interface = interfaces.split(',')
                    for interface in splitted_interface:
                        dict_interface = dict_real_interfaces.setdefault(interface, {})
                        dict_interface.update({'mapped_interface': interface})
                continue

            #  Vlan993, Vlan994, Vlan995, Vlan996, Vlan997, Vlan998, Vlan999
            m = p5.match(line)
            if m:
                groups = m.groupdict()
                if groups['interfaces']:
                    dict_real_interfaces = dict_name.setdefault('interfaces', {}). \
                    setdefault(interfaces_sort, {})
                    interfaces = groups['interfaces']
                    if interfaces[-1] == ',':
                        interfaces = interfaces[:-1]
                    interfaces = interfaces.replace(' ','')
                    splitted_interface = interfaces.split(',')
                    for interface in splitted_interface:
                        dict_interface = dict_real_interfaces.setdefault(interface, {})
                        dict_interface.update({interface_sort: interface})
                continue

            # Class: default, Flags: 0x00000111, ID: 1
            m = p6.match(line)
            if m:
                groups = m.groupdict()
                dict_name.update({'id': int(groups['id'])})
                dict_name.update({'flags': groups['flags']})
                dict_name.update({'class': groups['class']})
                continue

        return ret_dict