''' show_bgp.py
    IOSXE parsers for the following show commands:

    * show bgp all detail
    * show bgp all neighbor
    * show bgp all summary
    * show bgp all cluster-ids
    * show bgp all
    * show ip bgp template peer-session <WORD>
    * show ip bgp template peer-policy <WORD>
    * show ip bgp all dampening parameters
    * show ip bgp <af_name> [ vrf <vrf_id> ] <ipv4prefix>
    * show bgp vrf [vrf_id] <af_name> <ipv6prefix>
    * show bgp <af_name> <ipv6prefix>
    * show bgp all neighbors <neighbor> policy
    * show ip route vrf <WORD> bgp
    * show vrf detail

    * show bgp all neighbor x.x.x.x advertised-routes
    * show bgp all neighbor x.x.x.x routes
    * show bgp all neighbor x.x.x.x received
    * show bgp all neighbor x.x.x.x received-routes

'''

import re   
from metaparser import MetaParser
from metaparser.util.schemaengine import Schema, Any, Optional


class ShowBgpAllSummarySchema(MetaParser):
    """
    Schema for:
            * show bgp all summary
    """
    schema = {
        'vrf':
            {Any():
                 {Optional('neighbor'):
                      {Any():
                           {'address_family':
                                {Any():
                                     {'version': int,
                                      'as': int,
                                      'msg_rcvd': int,
                                      'msg_sent': int,
                                      'tbl_ver': int,
                                      'input_queue': int,
                                      'output_queue': int,
                                      'up_down': str,
                                      'state_pfxrcd': str,
                                      Optional('route_identifier'): str,
                                      Optional('local_as'): int,
                                      Optional('bgp_table_version'): int,
                                      Optional('routing_table_version'): int,
                                      Optional('prefixes'):
                                          {'total_entries': int,
                                           'memory_usage': int,
                                           },
                                      Optional('path'):
                                          {'total_entries': int,
                                           'memory_usage': int,
                                           },
                                      Optional('cache_entries'):
                                          {Any():
                                               {
                                                'total_entries': int,
                                                'memory_usage': int,
                                               },
                                          },
                                      Optional('entries'):
                                          {Any():
                                              {
                                                  'total_entries': int,
                                                  'memory_usage': int,
                                              },
                                          },
                                      Optional('community_entries'):
                                          {'total_entries': int,
                                           'memory_usage': int,
                                           },
                                      Optional('attribute_entries'): str,
                                      Optional('total_memory'): int,
                                      Optional('activity_prefixes'): str,
                                      Optional('activity_paths'): str,
                                      Optional('scan_interval'): int,
                                      },
                                 },
                            },
                       },
                  },
             },
        }


class ShowBgpAllSummary(ShowBgpAllSummarySchema):
    """
    Parser for:
          *  show bgp All Summary
    """

    def cli(self):
        cmd = 'show bgp all summary'
        out = self.device.execute(cmd)

        # Init vars
        sum_dict = {}
        cache_dict = {}
        entries_dict = {}

        for line in out.splitlines():
            if line:
                line = line.rstrip()
            else:
                continue

            # For address family: IPv4 Unicast
            p1 = re.compile(r'^\s*For address family: +(?P<address_family>[a-zA-Z0-9\s\-\_]+)$')
            m = p1.match(line)
            if m:
                # Save variables for use later
                address_family = str(m.groupdict()['address_family']).lower()
                vrf = 'default'
                attribute_entries = ""
                num_prefix_entries = ""
                path_total_entries = ""
                total_memory = ""
                activity_paths = ""
                activity_prefixes = ""
                scan_interval = ""
                cache_dict = {}
                entries_dict = {}
                num_community_entries = ""
                continue

            # BGP router identifier 200.0.1.1, local AS number 100
            p2 = re.compile(r'^\s*BGP +router +identifier'
                            ' +(?P<route_identifier>[0-9\.\:]+), +local +AS'
                            ' +number +(?P<local_as>[0-9]+)$')
            m = p2.match(line)
            if m:
                route_identifier = str(m.groupdict()['route_identifier'])
                local_as = int(m.groupdict()['local_as'])
                if 'vrf' not in sum_dict:
                    sum_dict['vrf'] = {}
                if vrf not in sum_dict['vrf']:
                    sum_dict['vrf'][vrf] = {}
                continue

            # BGP table version is 28, main routing table version 28
            p3 = re.compile(r'^\s*BGP +table +version +is'
                            ' +(?P<bgp_table_version>[0-9]+),'
                            ' +main +routing +table +version'
                            ' +(?P<routing_table_version>[0-9]+)$')
            m = p3.match(line)
            if m:
                bgp_table_version = int(m.groupdict()['bgp_table_version'])
                routing_table_version = int(m.groupdict()['routing_table_version'])
                continue

            # 27 network entries using 6696 bytes of memory
            p4 = re.compile(r'^\s*(?P<networks>[0-9]+) +network +entries +using'
                            ' +(?P<bytes>[0-9]+) +bytes +of +memory$')

            m = p4.match(line)
            if m:
                num_prefix_entries = int(m.groupdict()['networks'])
                num_memory_usage = int(m.groupdict()['bytes'])
                continue

            # 27 path entries using 3672 bytes of memory
            p5 = re.compile(r'^\s*(?P<path>[0-9]+) +path +entries +using'
                            ' +(?P<memory_usage>[0-9]+) +bytes +of +memory$')
            m = p5.match(line)
            if m:
                path_total_entries = int(m.groupdict()['path'])
                path_memory_usage = int(m.groupdict()['memory_usage'])
                continue

            # 2 BGP rrinfo entries using 48 bytes of memory
            p5_1 = re.compile(r'^\s*(?P<num_entries>([0-9]+)) +BGP +(?P<entries_type>(\S+)) +entries +using'
                              ' +(?P<entries_byte>[0-9]+) +bytes +of +memory$')
            m = p5_1.match(line)
            if m:
                num_entries = int(m.groupdict()['num_entries'])
                entries_type = str(m.groupdict()['entries_type'])
                entries_byte = int(m.groupdict()['entries_byte'])

                entries_dict[entries_type] = {}
                entries_dict[entries_type]['total_entries'] = num_entries
                entries_dict[entries_type]['memory_usage'] = entries_byte
                continue

            # 4 BGP extended community entries using 96 bytes of memory
            p5_2 = re.compile(r'^\s*(?P<num_community_entries>[0-9]+) +BGP +extended +community +entries +using'
                            ' +(?P<memory_usage>[0-9]+) +bytes +of +memory$')
            m = p5_2.match(line)
            if m:
                num_community_entries = int(m.groupdict()['num_community_entries'])
                community_memory_usage = int(m.groupdict()['memory_usage'])
                continue

            # 1/1 BGP path/bestpath attribute entries using 280 bytes of memory
            p6 = re.compile(r'^\s*(?P<attribute_entries>(\S+)) +BGP +(?P<attribute_type>(\S+))'
                            ' +attribute +entries +using +(?P<bytes>[0-9]+) +bytes +of +memory$')
            m = p6.match(line)
            if m:
                attribute_entries = str(m.groupdict()['attribute_entries'])
                attribute_type = str(m.groupdict()['attribute_type'])
                attribute_memory_usage = int(m.groupdict()['bytes'])
                continue

            # 0 BGP route-map cache entries using 0 bytes of memory
            p6_1 = re.compile(r'^\s*(?P<num_cache_entries>([0-9]+)) +BGP +(?P<cache_type>(\S+)) +cache +entries +using'
                            ' +(?P<cache_byte>[0-9]+) +bytes +of +memory$')
            m = p6_1.match(line)
            if m:
                num_cache_entries = int(m.groupdict()['num_cache_entries'])
                cache_type = str(m.groupdict()['cache_type'])
                cache_byte = int(m.groupdict()['cache_byte'])

                cache_dict[cache_type] = {}
                cache_dict[cache_type]['total_entries'] = num_cache_entries
                cache_dict[cache_type]['memory_usage'] = cache_byte
                continue

            # BGP using 10648 total bytes of memory
            p7 = re.compile(r'^\s*BGP +using'
                            ' +(?P<total_memory>[0-9]+) +total +bytes +of +memory$')
            m = p7.match(line)
            if m:
                total_memory = int(m.groupdict()['total_memory'])
                continue

            # BGP activity 47/20 prefixes, 66/39 paths, scan interval 60 secs
            p8 = re.compile(r'^\s*BGP +activity'
                            ' +(?P<activity_prefixes>(\S+)) +prefixes, +(?P<activity_paths>(\S+))'
                            ' +paths, +scan +interval +(?P<scan_interval>[0-9]+) +secs$')
            m = p8.match(line)
            if m:
                activity_prefixes = str(m.groupdict()['activity_prefixes'])
                activity_paths = str(m.groupdict()['activity_paths'])
                scan_interval = str(m.groupdict()['scan_interval'])
                continue


            # Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
            # 200.0.1.1       4          100       0       0        1    0    0 01:07:38 Idle
            # 200.0.2.1       4          100       0       0        1    0    0 never    Idle
            # 200.0.4.1       4          100       0       0        1    0    0 01:07:38 Idle

            p9 = re.compile(r'^\s*(?P<neighbor>[a-zA-Z0-9\.\:]+) +(?P<version>[0-9]+)'
                            ' +(?P<as>[0-9]+) +(?P<msg_rcvd>[0-9]+)'
                            ' +(?P<msg_sent>[0-9]+) +(?P<tbl_ver>[0-9]+)'
                            ' +(?P<inq>[0-9]+) +(?P<outq>[0-9]+)'
                            ' +(?P<up_down>[a-zA-Z0-9\:]+)'
                            ' +(?P<state>[a-zA-Z0-9\(\)\s]+)$')
            m = p9.match(line)
            if m:
                # Add neighbor to dictionary
                neighbor = str(m.groupdict()['neighbor'])
                if 'neighbor' not in sum_dict['vrf'][vrf]:
                    sum_dict['vrf'][vrf]['neighbor'] = {}
                if neighbor not in sum_dict['vrf'][vrf]['neighbor']:
                    sum_dict['vrf'][vrf]['neighbor'][neighbor] = {}
                nbr_dict = sum_dict['vrf'][vrf]['neighbor'][neighbor]

                # Add address family to this neighbor
                if 'address_family' not in nbr_dict:
                    nbr_dict['address_family'] = {}
                if address_family not in nbr_dict['address_family']:
                    nbr_dict['address_family'][address_family] = {}
                nbr_af_dict = nbr_dict['address_family'][address_family]

                # Add keys for this address_family
                nbr_af_dict['version'] = int(m.groupdict()['version'])
                nbr_af_dict['as'] = int(m.groupdict()['as'])
                nbr_af_dict['msg_rcvd'] = int(m.groupdict()['msg_rcvd'])
                nbr_af_dict['msg_sent'] = int(m.groupdict()['msg_sent'])
                nbr_af_dict['tbl_ver'] = int(m.groupdict()['tbl_ver'])
                nbr_af_dict['input_queue'] = int(m.groupdict()['inq'])
                nbr_af_dict['output_queue'] = int(m.groupdict()['outq'])
                nbr_af_dict['up_down'] = str(m.groupdict()['up_down'])
                nbr_af_dict['state_pfxrcd'] = str(m.groupdict()['state'])
                nbr_af_dict['route_identifier'] = route_identifier
                nbr_af_dict['local_as'] = local_as
                nbr_af_dict['bgp_table_version'] = bgp_table_version
                nbr_af_dict['routing_table_version'] = routing_table_version

                try:
                # Assign variables
                    if attribute_entries:
                        nbr_af_dict['attribute_entries'] = attribute_entries
                    if num_prefix_entries:
                        nbr_af_dict['prefixes'] = {}
                        nbr_af_dict['prefixes']['total_entries'] = num_prefix_entries
                        nbr_af_dict['prefixes']['memory_usage'] = num_memory_usage

                    if path_total_entries:
                        nbr_af_dict['path'] = {}
                        nbr_af_dict['path']['total_entries'] = path_total_entries
                        nbr_af_dict['path']['memory_usage'] = path_memory_usage

                    if total_memory:
                        nbr_af_dict['total_memory'] = total_memory

                    if activity_prefixes:
                        nbr_af_dict['activity_prefixes'] = activity_prefixes

                    if activity_paths:
                        nbr_af_dict['activity_paths'] = activity_paths

                    if scan_interval:
                        nbr_af_dict['scan_interval'] = int(scan_interval)

                    if len(cache_dict):
                        nbr_af_dict['cache_entries'] = cache_dict

                    if len(entries_dict):
                        nbr_af_dict['entries'] = entries_dict

                    if num_community_entries:
                        nbr_af_dict['community_entries'] = {}
                        nbr_af_dict['community_entries']['total_entries'] = num_community_entries
                        nbr_af_dict['community_entries']['memory_usage'] = community_memory_usage
                except:
                    pass
            else:
                # when neighbor info break down to 2 lines.
                #  Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
                #  2001:DB8:20:4:6::6
                #           4          400      67      73       66    0    0 01:03:11        5

                p10 = re.compile(r'^\s*(?P<neighbor>[a-zA-Z0-9\.\:]+)$')
                m = p10.match(line)
                if m :
                    # Add neighbor to dictionary
                    neighbor = str(m.groupdict()['neighbor'])
                    if 'neighbor' not in sum_dict['vrf'][vrf]:
                        sum_dict['vrf'][vrf]['neighbor'] = {}
                    if neighbor not in sum_dict['vrf'][vrf]['neighbor']:
                        sum_dict['vrf'][vrf]['neighbor'][neighbor] = {}
                    nbr_dict = sum_dict['vrf'][vrf]['neighbor'][neighbor]

                    # Add address family to this neighbor
                    if 'address_family' not in nbr_dict:
                        nbr_dict['address_family'] = {}
                    if address_family not in nbr_dict['address_family']:
                        nbr_dict['address_family'][address_family] = {}
                    nbr_af_dict = nbr_dict['address_family'][address_family]

                p11 = re.compile(r'^\s*(?P<version>[0-9]+)'
                                    ' +(?P<as>[0-9]+) +(?P<msg_rcvd>[0-9]+)'
                                    ' +(?P<msg_sent>[0-9]+) +(?P<tbl_ver>[0-9]+)'
                                    ' +(?P<inq>[0-9]+) +(?P<outq>[0-9]+)'
                                    ' +(?P<up_down>[a-zA-Z0-9\:]+)'
                                    ' +(?P<state>[a-zA-Z0-9\(\)\s]+)$')
                m = p11.match(line)
                if m:
                    # Add keys for this address_family
                    nbr_af_dict['version'] = int(m.groupdict()['version'])
                    nbr_af_dict['as'] = int(m.groupdict()['as'])
                    nbr_af_dict['msg_rcvd'] = int(m.groupdict()['msg_rcvd'])
                    nbr_af_dict['msg_sent'] = int(m.groupdict()['msg_sent'])
                    nbr_af_dict['tbl_ver'] = int(m.groupdict()['tbl_ver'])
                    nbr_af_dict['input_queue'] = int(m.groupdict()['inq'])
                    nbr_af_dict['output_queue'] = int(m.groupdict()['outq'])
                    nbr_af_dict['up_down'] = str(m.groupdict()['up_down'])
                    nbr_af_dict['state_pfxrcd'] = str(m.groupdict()['state'])
                    nbr_af_dict['route_identifier'] = route_identifier
                    nbr_af_dict['local_as'] = local_as
                    nbr_af_dict['bgp_table_version'] = bgp_table_version
                    nbr_af_dict['routing_table_version'] = routing_table_version

                    try:
                        # Assign variables
                        if attribute_entries:
                            nbr_af_dict['attribute_entries'] = attribute_entries
                        if num_prefix_entries:
                            nbr_af_dict['prefixes'] = {}
                            nbr_af_dict['prefixes']['total_entries'] = num_prefix_entries
                            nbr_af_dict['prefixes']['memory_usage'] = num_memory_usage

                        if path_total_entries:
                            nbr_af_dict['path'] = {}
                            nbr_af_dict['path']['total_entries'] = path_total_entries
                            nbr_af_dict['path']['memory_usage'] = path_memory_usage

                        if total_memory:
                            nbr_af_dict['total_memory'] = total_memory

                        if activity_prefixes:
                            nbr_af_dict['activity_prefixes'] = activity_prefixes

                        if activity_paths:
                            nbr_af_dict['activity_paths'] = activity_paths

                        if scan_interval:
                            nbr_af_dict['scan_interval'] = int(scan_interval)

                        if len(cache_dict):
                            nbr_af_dict['cache_entries'] = cache_dict

                        if len(entries_dict):
                            nbr_af_dict['entries'] = entries_dict

                        if num_community_entries:
                            nbr_af_dict['community_entries'] = {}
                            nbr_af_dict['community_entries']['total_entries'] = num_community_entries
                            nbr_af_dict['community_entries']['memory_usage'] = community_memory_usage
                    except:
                        pass

                continue

        return sum_dict


class ShowBgpAllClusterIdsSchema(MetaParser):
    '''
        Schema for show bgp all cluster-ids
    '''
    schema = {
              'vrf':
                    {Any():
                        {
                           Optional('cluster_id'): str,
                           Optional('configured_id'): str,
                           Optional('reflection_all_configured'): str,
                           Optional('reflection_intra_cluster_configured'): str,
                           Optional('reflection_intra_cluster_used'): str,
                           Optional('list_of_cluster_ids'):
                               {Any():
                                    {
                                        Optional('num_neighbors'): int,
                                        Optional('client_to_client_reflection_configured'): str,
                                        Optional('client_to_client_reflection_used'): str,

                                    }

                               }
                        }
                    },

                }

class ShowBgpAllClusterIds(ShowBgpAllClusterIdsSchema):
    '''
       Parser for show bgp all cluster-ids
       Executing 'show vrf detail | inc \(VRF' to collect vrf names.

    '''

    def cli(self):
        # find vrf names
        # show vrf detail | inc \(VRF
        cmd_vrfs = 'show vrf detail | inc \(VRF'
        out_vrf = self.device.execute(cmd_vrfs)
        vrf_dict = {'0':'default'}

        for line in out_vrf.splitlines():
            if not line:
                continue
            else:
                line = line.rstrip()

            # VRF VRF1 (VRF Id = 1); default RD 300:1; default VPNID <not set>
            p = re.compile(r'^\s*VRF +(?P<vrf_name>[0-9a-zA-Z]+)'
                            ' +\(+VRF +Id += +(?P<vrf_id>[0-9]+)+\)+;'
                            ' +default +(?P<other_data>.+)$')
            m = p.match(line)
            if m:
                # Save variables for use later
                vrf_name = str(m.groupdict()['vrf_name'])
                vrf_id = str(m.groupdict()['vrf_id'])
                vrf_dict[vrf_id] = vrf_name.lower()
                continue


        # show bgp all cluster-ids
        cmd = 'show bgp all cluster-ids'
        out = self.device.execute(cmd)

        # Init vars
        sum_dict = {}
        cluster_id = None
        list_of_cluster_ids = dict()
        configured_id = ""
        reflection_all_configured = ""
        reflection_intra_cluster_configured = ""
        reflection_intra_cluster_used = ""


        for line in out.splitlines():
            if line.strip():
                line = line.rstrip()
            else:
                continue

            # Global cluster-id: 4.4.4.4 (configured: 0.0.0.0)
            p1 = re.compile(r'^\s*Global +cluster-id: +(?P<cluster_id>[0-9\.]+)'
                            ' +\(+configured: +(?P<configured>[0-9\.]+)+\)$')
            m = p1.match(line)
            if m:
                # Save variables for use later
                cluster_id = str(m.groupdict()['cluster_id'])
                configured_id = str(m.groupdict()['configured'])

                if 'vrf' not in sum_dict:
                    sum_dict['vrf'] = {}

                continue

            #   all (inter-cluster and intra-cluster): ENABLED
            p3 = re.compile(r'^\s*all +\(+inter-cluster +and +intra-cluster+\):'
                            ' +(?P<all_configured>[a-zA-Z]+)$')
            m = p3.match(line)
            if m:
                reflection_all_configured = m.groupdict()['all_configured'].lower()
                continue

            # intra-cluster:                         ENABLED       ENABLED
            p4 = re.compile(r'^\s*intra-cluster:\s+(?P<intra_cluster_configured>[a-zA-Z]+)'
                            ' +(?P<intra_cluster_used>[a-zA-Z]+)$')
            m = p4.match(line)
            if m:
                reflection_intra_cluster_configured = m.groupdict()['intra_cluster_configured'].lower()
                reflection_intra_cluster_used = m.groupdict()['intra_cluster_used'].lower()
                continue

            # List of cluster-ids
            # Cluster-id  #-neighbors C2C-rfl-CFG C2C-rfl-USE
            # 192.168.1.1                2 DISABLED    DISABLED
            p5 = re.compile(r'^\s*(?P<cluster_ids>[0-9\.]+)'
                        ' +(?P<num_neighbors>[0-9]+)'
                        ' +(?P<client_to_client_ref_configured>[a-zA-Z]+)'
                        ' +(?P<client_to_client_ref_used>[a-zA-Z]+)$')
            m = p5.match(line)
            if m:
                cluster_ids = m.groupdict()['cluster_ids']
                list_of_cluster_ids[cluster_ids] = cluster_ids
                list_of_cluster_ids[cluster_ids] = {}
                list_of_cluster_ids[cluster_ids]['num_neighbors'] = int(m.groupdict()['num_neighbors'])
                list_of_cluster_ids[cluster_ids]['client_to_client_reflection_configured'] = \
                    m.groupdict()['client_to_client_ref_configured'].lower()
                list_of_cluster_ids[cluster_ids]['client_to_client_reflection_used'] = \
                    m.groupdict()['client_to_client_ref_used'].lower()

                continue

        for vrf_id, vrf_name in vrf_dict.items():
            if 'vrf' not in sum_dict:
                sum_dict['vrf'] = {}
            if vrf_name not in sum_dict['vrf']:
                sum_dict['vrf'][vrf_name] = {}
            if 'cluster_id' not in sum_dict['vrf'][vrf_name]:
                if not cluster_id:
                    del sum_dict['vrf']
                if cluster_id:
                    sum_dict['vrf'][vrf_name]['cluster_id'] = cluster_id
                if configured_id:
                    sum_dict['vrf'][vrf_name]['configured_id'] = configured_id
                if reflection_all_configured:
                    sum_dict['vrf'][vrf_name]['reflection_all_configured'] = \
                        reflection_all_configured
                if reflection_intra_cluster_configured:
                    sum_dict['vrf'][vrf_name]['reflection_intra_cluster_configured'] = \
                        reflection_intra_cluster_configured
                if reflection_intra_cluster_used:
                    sum_dict['vrf'][vrf_name]['reflection_intra_cluster_used'] = \
                        reflection_intra_cluster_used
                if list_of_cluster_ids:
                    sum_dict['vrf'][vrf_name]['list_of_cluster_ids'] = list_of_cluster_ids
        return sum_dict


class ShowBgpAllNeighborsSchema(MetaParser):
    """
    Schema for:
            * show bgp all neighbors
    """

    schema = {
        'vrf':
            {Any():
                 {
                 'neighbor':
                      {Any():
                          {Optional('remote_as'): int,
                          Optional('link'): str,
                          Optional('bgp_version'): int,
                          Optional('router_id'): str,
                          Optional('session_state'): str,
                          Optional('shutdown'): bool,
                          Optional('bgp_negotiated_keepalive_timers'):
                              {
                               Optional('keepalive_interval'): int,
                               Optional('hold_time'): int,
                               },

                          Optional('bgp_session_transport'):
                              {Optional('connection'):
                                   {
                                    Optional('last_reset'): str,
                                    Optional('reset_reason'): str,
                                    Optional('established'): int,
                                    Optional('dropped'): int,
                                    },
                               Optional('transport'):
                                   {Optional('local_port'): str,
                                    Optional('local_host'): str,
                                    Optional('foreign_port'): str,
                                    Optional('foreign_host'): str,
                                    },
                               },
                          Optional('bgp_neighbor_counters'):
                              {Optional('messages'):
                                   {Optional('sent'):
                                        {
                                            Optional('opens'): int,
                                            Optional('updates'): int,
                                            Optional('notifications'): int,
                                            Optional('keepalives'): int,
                                            Optional('route_refresh'): int,
                                            Optional('total'): int,
                                         },
                                    Optional('received'):
                                        {
                                            Optional('opens'): int,
                                            Optional('updates'): int,
                                            Optional('notifications'): int,
                                            Optional('keepalives'): int,
                                            Optional('route_refresh'): int,
                                            Optional('total'): int,
                                         },
                                       Optional('input_queue'): int,
                                       Optional('output_queue'): int,
                                    },

                               },
                          Optional('bgp_negotiated_capabilities'):
                              {Optional('route_refresh'): str,
                               Optional('vpnv4_unicast'): str,
                               Optional('vpnv6_unicast'): str,
                               Optional('ipv4_unicast'): str,
                               Optional('ipv6_unicast'): str,
                               Optional('graceful_restart'): str,
                               Optional('enhanced_refresh'): str,
                               Optional('multisession'): str,
                               Optional('four_octets_asn'): str,
                               Optional('stateful_switchover'): str,
                               },
                           Optional('bgp_event_timer'):
                               {Optional('starts'):
                                   {
                                       Optional('retrans'): int,
                                       Optional('timewait'): int,
                                       Optional('ackhold'): int,
                                       Optional('sendwnd'): int,
                                       Optional('keepalive'): int,
                                       Optional('giveup'): int,
                                       Optional('pmtuager'): int,
                                       Optional('deadwait'): int,
                                       Optional('linger'): int,
                                       Optional('processq'): int,
                                   },
                                   Optional('wakeups'):
                                       {
                                           Optional('retrans'): int,
                                           Optional('timewait'): int,
                                           Optional('ackhold'): int,
                                           Optional('sendwnd'): int,
                                           Optional('keepalive'): int,
                                           Optional('giveup'): int,
                                           Optional('pmtuager'): int,
                                           Optional('deadwait'): int,
                                           Optional('linger'): int,
                                           Optional('processq'): int,

                                       },
                                   Optional('next'):
                                       {
                                           Optional('retrans'): str,
                                           Optional('timewait'): str,
                                           Optional('ackhold'): str,
                                           Optional('sendwnd'): str,
                                           Optional('keepalive'): str,
                                           Optional('giveup'): str,
                                           Optional('pmtuager'): str,
                                           Optional('deadwait'): str,
                                           Optional('linger'): str,
                                           Optional('processq'): str,
                                       },
                               },

                          Optional('address_family'):
                              {Any():
                                   {
                                       Optional('last_read'): str,
                                       Optional('last_written'): str,
                                       Optional('up_time'): str,
                               },
                          },
                     },
                 },
            },
        },
    }


class ShowBgpAllNeighbors(ShowBgpAllNeighborsSchema):
    '''
    Parser for:
         show bgp all neighbors
    '''

    def cli(self):

        cmd = 'show bgp all neighbors'
        out = self.device.execute(cmd)

        # Init vars
        parsed_dict = {}
        address_family_dict = {}

        for line in out.splitlines():
            if line:
                line = line.rstrip()
            else:
                continue

            # For address family: IPv4 Unicast
            p1 = re.compile(r'^\s*For +address +family:'
                            ' +(?P<address_family>[a-zA-Z0-9\-\s]+)$')
            m = p1.match(line)
            if m:
                af_name = m.groupdict()['address_family'].lower()
                continue

            # BGP neighbor is 2.2.2.2,  remote AS 100, internal link
            p2 = re.compile(r'^\s*BGP +neighbor +is +(?P<neghibor>[0-9\S]+),'
                            '\s+remote +AS +(?P<remote_as>[0-9]+),'
                            ' +(?P<link>[a-zA-Z]+) +link$')
            m = p2.match(line)
            if m:
                neighbor_id = m.groupdict()['neghibor']
                vrf_name = 'default'
                remote_as = int(m.groupdict()['remote_as'])
                link = m.groupdict()['link']  # internal / external

                if 'vrf' not in parsed_dict:
                    parsed_dict['vrf'] = {}
                if vrf_name not in parsed_dict['vrf']:
                    parsed_dict['vrf'][vrf_name] = {}

                if 'neighbor' not in parsed_dict['vrf']['default']:
                    parsed_dict['vrf']['default']['neighbor'] = {}

                if neighbor_id not in parsed_dict['vrf'][vrf_name]['neighbor']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] = {}
                    if remote_as is not None:
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['remote_as'] = remote_as
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['link'] = link

                if 'address_family' not in  parsed_dict['vrf']\
                        [vrf_name]['neighbor'][neighbor_id]:
                    parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['address_family'] = {}

                if af_name:
                    parsed_dict['vrf'][vrf_name]['neighbor'] \
                        [neighbor_id]['address_family'][af_name] = {}
                continue

            # BGP neighbor is 20.4.6.6,  vrf VRF2,  remote AS 400, external link
            p2_2 = re.compile(r'^\s*BGP +neighbor +is +(?P<neghibor>[0-9\S]+),'
                              ' +vrf +(?P<vrf_name>[a-zA-Z0-9]+),'
                              '\s+remote +AS +(?P<remote_as>[0-9]+),'
                              '\s+(?P<link>[a-zA-Z]+) +link$')
            m = p2_2.match(line)
            if m:
                neighbor_id = m.groupdict()['neghibor']
                vrf_name = m.groupdict()['vrf_name'].lower()
                remote_as = int(m.groupdict()['remote_as'])
                link = m.groupdict()['link']  # internal / external


                if 'vrf' not in parsed_dict:
                    parsed_dict['vrf'] = {}
                if vrf_name not in parsed_dict['vrf']:
                    parsed_dict['vrf'][vrf_name] = {}

                if 'neighbor' not in parsed_dict['vrf'][vrf_name]:
                    parsed_dict['vrf'][vrf_name]['neighbor'] = {}

                if neighbor_id not in parsed_dict['vrf'][vrf_name]['neighbor']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] = {}
                    if remote_as is not None:
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['remote_as'] = remote_as
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['link'] = link

                if 'address_family' not in  parsed_dict['vrf']\
                        [vrf_name]['neighbor'][neighbor_id]:
                    parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['address_family'] = {}

                if af_name:
                    parsed_dict['vrf'][vrf_name]['neighbor'] \
                        [neighbor_id]['address_family'][af_name] = {}
                continue


            # BGP version 4, remote router ID 2.2.2.2
            p3 = re.compile(r'^\s*BGP +version +(?P<bgp_version>[0-9]+),'
                            ' +remote +router +ID +(?P<remote_id>[0-9\.]+)$')
            m = p3.match(line)
            if m:
                bgp_version = int(m.groupdict()['bgp_version'])
                remote_router_id = m.groupdict()['remote_id']

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_version'] = bgp_version
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['router_id'] = remote_router_id
                continue

            # BGP state = Established, up for 01:10:35
            p4 = re.compile(r'^\s*BGP +state += +(?P<bgp_state>[a-zA-Z]+),'
                            ' +(?P<shutdown>\w+) +for +(?P<uptime>[0-9\:]+)$')
            m = p4.match(line)
            if m:
                bgp_state = m.groupdict()['bgp_state']
                shutdown = True if m.groupdict()['shutdown'] == 'down' else False
                uptime = m.groupdict()['uptime']

                parsed_dict['vrf'][vrf_name]['neighbor']\
                [neighbor_id]['session_state'] = bgp_state.lower()
                parsed_dict['vrf'][vrf_name]['neighbor']\
                [neighbor_id]['shutdown'] = shutdown

                if 'address_family' not in parsed_dict['vrf'] \
                        [vrf_name]['neighbor'][neighbor_id]:
                    parsed_dict['vrf'][vrf_name]['neighbor'] \
                        [neighbor_id]['address_family'] = {}

                if af_name not in parsed_dict['vrf'][vrf_name]['neighbor'] \
                        [neighbor_id]['address_family']:
                    parsed_dict['vrf'][vrf_name]['neighbor'] \
                        [neighbor_id]['address_family'][af_name] = {}

                parsed_dict['vrf'][vrf_name]['neighbor']\
                    [neighbor_id]['address_family'][af_name]['up_time'] = uptime

                continue

            # Last read 00:00:04, last write 00:00:09, hold time is 180, keepalive interval is 60 seconds
            p6 = re.compile(r'^\s*Last +read +(?P<last_read>[0-9\:]+),'
                            ' +last +write +(?P<last_write>[0-9\:]+),'
                            ' +hold +time +is +(?P<hold_time>[0-9]+),'
                            ' +keepalive +interval +is +(?P<keepalive_interval>[0-9]+)'
                            ' +seconds$')

            m = p6.match(line)
            if m:
                last_read = m.groupdict()['last_read']
                last_write = m.groupdict()['last_write']
                hold_time = int(m.groupdict()['hold_time'])
                keepalive_interval = int(m.groupdict()['keepalive_interval'])

                if 'bgp_negotiated_keepalive_timers' not in \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_keepalive_timers'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_keepalive_timers']['hold_time'] = hold_time

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_keepalive_timers']['keepalive_interval'] = keepalive_interval

                if 'address_family' not in parsed_dict['vrf']\
                        [vrf_name]['neighbor'][neighbor_id]:
                    parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['address_family'] = {}

                if af_name not in parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['address_family']:
                    parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['address_family'][af_name] = {}

                parsed_dict['vrf'][vrf_name]['neighbor']\
                    [neighbor_id]['address_family'][af_name]['last_read'] = last_read
                parsed_dict['vrf'][vrf_name]['neighbor'] \
                    [neighbor_id]['address_family'][af_name]['last_written'] = last_write


                continue

            # Neighbor sessions:
            #  1 active, is not multisession capable (disabled)
            p7 = re.compile(r'^\s*(?P<num_neighbor_sessions>[0-9]+),'
                            ' +(?P<multisession_capable>[a-zA-Z\s]+) +multisession +capable'
                            ' +\(+(?P<multisession_status>[a-zA-Z])+\)$')
            m = p7.match(line)
            if m:
                num_neighbor_sessions = int(m.groupdict()['num_neighbor_sessions'])
                multisession_capable = m.groupdict()['multisession_capable']
                multisession_status = m.groupdict()['multisession_status']
                continue
            # Neighbor capabilities:
            #  Route refresh: advertised and received(new)
            p8 = re.compile(r'^\s*Route +refresh:'
                            ' +(?P<route_refresh>[\w\s\S]+)$')
            m = p8.match(line)
            if m:
                route_refresh = m.groupdict()['route_refresh']
                if 'bgp_negotiated_capabilities' not in \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]:\
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_capabilities']['route_refresh'] = route_refresh
                continue

            #  Four-octets ASN Capability: advertised and received
            p9 = re.compile(r'^\s*Four-octets +ASN +Capability:'
                            ' +(?P<four_octets_asn_capability>[a-zA-Z\s]+)$')
            m = p9.match(line)
            if m:
                four_octets_asn_capability = m.groupdict()['four_octets_asn_capability']
                if 'bgp_negotiated_capabilities' not in \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]:\
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_capabilities']['four_octets_asn'] = four_octets_asn_capability
                continue

            #  Address family VPNv4 Unicast: advertised and received
            p10 = re.compile(r'^\s*Address +family'
                             ' +VPNv4 +Unicast:'
                             ' +(?P<address_family_status>[a-zA-Z\s]+)$')
            m = p10.match(line)
            if m:
                address_family_status = m.groupdict()['address_family_status']
                if 'bgp_negotiated_capabilities' not in \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]:\
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                    ['bgp_negotiated_capabilities']['vpnv4_unicast'] = address_family_status
                continue

            #  Address family VPNv6 Unicast: advertised and received
            p10_1 = re.compile(r'^\s*Address +family'
                             ' +VPNv6 +Unicast:'
                             ' +(?P<address_family_status>[a-zA-Z\s]+)$')
            m = p10_1.match(line)
            if m:
                address_family_status = m.groupdict()['address_family_status']
                if 'bgp_negotiated_capabilities' not in \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]:\
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_capabilities']['vpnv6_unicast'] = address_family_status
                continue
            #  Address family IPv6 Unicast: advertised and received
            p10_2 = re.compile(r'^\s*Address +family'
                               ' +IPv6 +Unicast:'
                               ' +(?P<address_family_status>[a-zA-Z\s]+)$')
            m = p10_2.match(line)
            if m:
                address_family_status = m.groupdict()['address_family_status']
                if 'bgp_negotiated_capabilities' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_capabilities']['ipv6_unicast'] = address_family_status
                continue

            #  Address family IPv4 Unicast: advertised and received
            p10_3 = re.compile(r'^\s*Address +family'
                               ' +IPv4 +Unicast:'
                               ' +(?P<address_family_status>[a-zA-Z\s]+)$')
            m = p10_3.match(line)
            if m:
                address_family_status = m.groupdict()['address_family_status']
                if 'bgp_negotiated_capabilities' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_capabilities']['ipv4_unicast'] = address_family_status
                continue

            #  Graceful Restart Capability: received
            p11 = re.compile(r'^\s*Graceful +Restart +Capability:'
                             ' +(?P<graceful_restart_capability>[a-zA-Z\s]+)$')
            m = p11.match(line)
            if m:
                graceful_restart_capability = \
                    m.groupdict()['graceful_restart_capability']
                if 'bgp_negotiated_capabilities' not in \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]:\
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_capabilities']['graceful_restart'] = graceful_restart_capability
                continue

            #   Remote Restart timer is 120 seconds
            p12 = re.compile(r'^\s*Remote +Restart +timer +is'
                             ' +(?P<remote_restart_timer>[0-9]+)$ +seconds')
            m = p12.match(line)
            if m:
                remote_restart_timer = int(m.groupdict()['remote_restart_timer'])
                if 'bgp_negotiated_capabilities' not in \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]:\
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                    ['bgp_negotiated_capabilities']['remote_restart_timer'] = remote_restart_timer
                continue

            #   Address families advertised by peer:
            #    VPNv4 Unicast (was not preserved, VPNv6 Unicast (was not preserved

            #  Enhanced Refresh Capability: advertised
            p13 = re.compile(r'^\s*Enhanced +Refresh +Capability:'
                             ' +(?P<enhanced_refresh_capability>[a-zA-Z\s]+)$')
            m = p13.match(line)
            if m:
                enhanced_refresh_capability = m.groupdict()['enhanced_refresh_capability']
                if 'bgp_negotiated_capabilities' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                    ['bgp_negotiated_capabilities']['enhanced_refresh'] = enhanced_refresh_capability
                continue

            #  Multisession Capability:
            p14 = re.compile(r'^\s*Multisession +Capability:'
                             ' +(?P<multisession>[a-zA-Z\s]+)$')
            m = p13.match(line)
            if m:
                multisession_capability = m.groupdict()['multisession']
                if 'bgp_negotiated_capabilities' not in \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                ['bgp_negotiated_capabilities']['multisession'] = multisession_capability
                continue

            #  Stateful switchover support enabled: NO for session 1
            p15 = re.compile(r'^\s*Stateful +switchover +support'
                             ' +(?P<stateful_switchover>[a-zA-Z]+):'
                             ' +NO +for +session (?P<no_session>[0-9]+)$')
            m = p15.match(line)
            if m:
                stateful_switchover = m.groupdict()['stateful_switchover']
                if 'bgp_negotiated_capabilities' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_negotiated_capabilities'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_negotiated_capabilities']['stateful_switchover'] = stateful_switchover
                continue

            # Message statistics:
            #  InQ depth is 0
            p18 = re.compile(r'^\s*InQ +depth +is'
                             ' +(?P<input_queue>[0-9]+)$')
            m = p18.match(line)
            if m:
                message_input_queue = int(m.groupdict()['input_queue'])
                if 'bgp_neighbor_counters' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_neighbor_counters'] = {}
                if 'messages' not in parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['bgp_neighbor_counters']: \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_neighbor_counters']['messages'] = {}
                if 'input_queue' not in parsed_dict['vrf'][vrf_name]\
                    ['neighbor'][neighbor_id]['bgp_neighbor_counters']['messages']:
                    parsed_dict['vrf'][vrf_name]\
                        ['neighbor'][neighbor_id]['bgp_neighbor_counters']['messages']\
                        ['input_queue'] = message_input_queue

                continue
            #  OutQ depth is 0
            p19 = re.compile(r'^\s*OutQ +depth +is'
                             ' +(?P<output_queue>[0-9]+)$')
            m = p19.match(line)
            if m:
                message_output_queue = int(m.groupdict()['output_queue'])
                if 'bgp_neighbor_counters' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_neighbor_counters'] = {}

                if 'messages' not in parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['bgp_neighbor_counters']: \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_neighbor_counters']['messages'] = {}

                if 'output_queue' not in parsed_dict['vrf'][vrf_name]\
                    ['neighbor'][neighbor_id]['bgp_neighbor_counters']['messages']:
                    parsed_dict['vrf'][vrf_name]\
                        ['neighbor'][neighbor_id]['bgp_neighbor_counters']['messages']\
                        ['output_queue'] = message_output_queue
                continue

            #                     Sent       Rcvd
            #  Opens:                  1          1
            #  Notifications:          0          0
            #  Updates:               11          6
            #  Keepalives:            75         74
            #  Route Refresh:          0          0
            #  Total:                 87         81
            p19_1 = re.compile(
                r'^\s*(?P<name>[a-zA-Z\s]+):\s+(?P<sent>[0-9]+) +(?P<received>[0-9]+)$')

            m = p19_1.match(line)
            if m:
                name = m.groupdict()['name'].replace(" ","_").lower()
                sent = int(m.groupdict()['sent'])
                received = int(m.groupdict()['received'])

                if 'bgp_neighbor_counters' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]['bgp_neighbor_counters'] = {}

                if 'messages' not in parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['bgp_neighbor_counters']: \
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_neighbor_counters']['messages'] = {}

                if 'sent' not in parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['bgp_neighbor_counters']['messages']: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                            ['bgp_neighbor_counters']['messages']['sent'] = {}
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_neighbor_counters']['messages']['sent'][name] = sent


                if 'received' not in parsed_dict['vrf'][vrf_name]['neighbor']\
                        [neighbor_id]['bgp_neighbor_counters']['messages']:\
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                            ['bgp_neighbor_counters']['messages']['received'] = {}
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_neighbor_counters']['messages']['received'][name] = received

                continue

            # Default minimum time between advertisement runs is 0 seconds
            p26 = re.compile(r'^\s*Default +minimum +time +between +advertisement +runs +is'
                             ' +(?P<minimum_time_between_advertisement>[0-9]+)'
                             ' +seconds$')
            m = p26.match(line)
            if m:
                minimum_time_between_advertisement = int(m.groupdict()['minimum_time_between_advertisement'])
                continue

            # Address tracking is enabled, the RIB does have a route to 2.2.2.2
            p27 = re.compile(r'^\s*Address +tracking +is'
                             ' +(?P<address_tracking_status>[a-zA-Z]+),'
                             ' +the +RIB +does +have +a +route +to'
                             ' +(?P<rib_route_ip>[0-9\.]+)$')
            m = p27.match(line)
            if m:
                address_tracking_status = m.groupdict()['address_tracking_status']
                rib_route_ip = m.groupdict()['rib_route_ip']
                continue

            # Connections established 1; dropped 0
            p28 = re.compile(r'^\s*Connections +established'
                             ' +(?P<num_connection_established>[0-9]+);'
                             ' +dropped +(?P<num_connection_dropped>[0-9]+)$')
            m = p28.match(line)
            if m:
                num_connection_established = int(m.groupdict()['num_connection_established'])
                num_connection_dropped = int(m.groupdict()['num_connection_dropped'])

                if 'bgp_session_transport' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                            ['bgp_session_transport'] = {}

                if 'connection' not in parsed_dict['vrf'][vrf_name]\
                        ['neighbor'][neighbor_id]['bgp_session_transport']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_session_transport']['connection'] = {}


                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_session_transport']['connection']['established']\
                        = num_connection_established

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                        ['bgp_session_transport']['connection']['dropped'] \
                        = num_connection_dropped
                continue

            # Last reset never
            p29 = re.compile(r'^\s*Last +reset'
                             ' +(?P<last_connection_reset>[a-zA-Z]+)$')
            m = p29.match(line)
            if m:
                last_connection_reset = m.groupdict()['last_connection_reset']
                if 'bgp_session_transport' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                            ['bgp_session_transport'] = {}

                if 'connection' not in parsed_dict['vrf'][vrf_name] \
                        ['neighbor'][neighbor_id]['bgp_session_transport']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                        ['bgp_session_transport']['connection'] = {}

                if last_connection_reset:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                        ['bgp_session_transport']['connection']['last_reset'] \
                        = last_connection_reset
                continue
            #Last reset 01:05:09, due to Active open failed
            p29_2 = re.compile(r'^\s*Last +reset'
                               ' +(?P<last_connection_reset>[0-9\:]+)\S'
                               ' +due +to (?P<reset_reason>[0-9a-zA-Z\s]+)$')
            m = p29_2.match(line)
            if m:
                last_connection_reset = m.groupdict()['last_connection_reset']
                reset_reason = m.groupdict()['reset_reason']
                if 'bgp_session_transport' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                            ['bgp_session_transport'] = {}

                if 'connection' not in parsed_dict['vrf'][vrf_name] \
                        ['neighbor'][neighbor_id]['bgp_session_transport']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_session_transport']['connection'] = {}

                if last_connection_reset:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                        ['bgp_session_transport']['connection']['last_reset'] \
                        = last_connection_reset

                if reset_reason:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                        ['bgp_session_transport']['connection']['reset_reason'] \
                        = reset_reason
                continue

            # Transport(tcp) path-mtu-discovery is enabled
            p30 = re.compile(r'^\s*Transport\(tcp\) +path-mtu-discovery +is'
                             ' +(?P<path_mtu_discovery_status>[a-zA-Z]+)$')
            m = p30.match(line)
            if m:
                path_mtu_discovery_status = m.groupdict()['path_mtu_discovery_status']
                continue

            # Graceful-Restart is disabled
            p31 = re.compile(r'^\s*Graceful-Restart +is'
                             ' +(?P<graceful_restart>[a-zA-Z]+)$')
            m = p31.match(line)
            if m:
                graceful_restart = m.groupdict()['graceful_restart']
                continue

            # Connection state is ESTAB, I/O status: 1, unread input bytes: 0
            p32 = re.compile(r'^\s*Connection +state +is'
                             ' +(?P<connection_state>[a-zA-Z]+),'
                             ' +I/O +status:(?P<num_io_status>[0-9]+),'
                             ' +unread +input +bytes:'
                             ' +(?P<num_unread_input_bytes>[0-9]+)$')
            m = p32.match(line)
            if m:
                connection_state = m.groupdict()['connection_state']
                num_io_state = int(m.groupdict()['num_io_status'])
                num_unread_input_bytes = int(m.groupdict()['num_unread_input_bytes'])
                continue
            # Connection is ECN Disabled, Mininum incoming TTL 0, Outgoing TTL 255
            p33 = re.compile(r'^\s*Connection +is +ECN'
                             ' +(?P<connection_ecn_state>[a-zA-Z]+),'
                             ' +Mininum +incoming +TTL +(?P<minimum_incoming_ttl>[0-9]+),'
                             ' +Outgoing +TTL'
                             ' +(?P<minimum_outgoing_ttl>[0-9]+)$')
            m = p33.match(line)
            if m:
                connection_ecn_state = m.groupdict()['connection_ecn_state']
                minimum_incoming_ttl = int(m.groupdict()['minimum_incoming_ttl'])
                minimum_outgoing_ttl = int(m.groupdict()['minimum_outgoing_ttl'])
                continue

            # Local host: 4.4.4.4, Local port: 35281
            p34 = re.compile(r'^\s*Local +host:'
                             ' +(?P<local_host>[0-9\S]+),'
                             ' +Local +port: +(?P<local_port>[0-9]+)$')
            m = p34.match(line)
            if m:
                local_host = m.groupdict()['local_host']
                local_port = m.groupdict()['local_port']

                if 'bgp_session_transport' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                            ['bgp_session_transport'] = {}

                if 'transport' not in parsed_dict['vrf'][vrf_name] \
                        ['neighbor'][neighbor_id]['bgp_session_transport']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_session_transport']['transport'] = {}


                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                   ['bgp_session_transport']['transport']['local_host'] = local_host

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id] \
                   ['bgp_session_transport']['transport']['local_port'] = local_port
                continue

            # Foreign host: 2.2.2.2, Foreign port: 179
            p35 = re.compile(r'^\s*Foreign +host:'
                             ' +(?P<foreign_host>[0-9\S]+),'
                             ' +Foreign +port: +(?P<foreign_port>[0-9]+)$')
            m = p35.match(line)
            if m:
                foreign_host = m.groupdict()['foreign_host']
                foreign_port = m.groupdict()['foreign_port']

                if 'bgp_session_transport' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]:\
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                            ['bgp_session_transport'] = {}

                if 'transport' not in parsed_dict['vrf'][vrf_name]\
                        ['neighbor'][neighbor_id]['bgp_session_transport']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_session_transport']['transport'] = {}

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_session_transport']['transport']['foreign_host'] = foreign_host

                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                    ['bgp_session_transport']['transport']['foreign_port'] = foreign_port
                continue

            # Connection tableid (VRF): 0
            p36 = re.compile(r'^\s*Connection +tableid +\(VRF\):'
                             ' +(?P<num_connection_tableid>[0-9]+)$')
            m = p36.match(line)
            if m:
                num_connection_tableid = int(m.groupdict()['num_connection_tableid'])
                continue

            # Maximum output segment queue size: 50
            p37 = re.compile(r'^\s*Maximum +output +segment +queue +size:'
                             ' +(?P<num_max_output_seg_queue_size>[0-9]+)$')
            m = p37.match(line)
            if m:
                num_max_output_seg_queue_size = int(m.groupdict()['num_max_output_seg_queue_size'])
                continue

            # Enqueued packets for retransmit: 0, input: 0  mis-ordered: 0 (0 bytes)
            p38 = re.compile(r'^\s*Enqueued +packets +for +retransmit:'
                             ' +(?P<enqueued_packets_for_retransmit>[0-9]+),'
                             ' +input: +(?P<enqueued_packets_for_input>[0-9]+)'
                             '\s+mis-ordered: +(?P<enqueued_packets_for_mis_ordered>[0-9]+)'
                             ' +\((?P<num_bytes>[0-9]+) +bytes+\)$')

            m = p38.match(line)
            if m:
                enqueued_packets_for_retransmit = int(m.groupdict()['enqueued_packets_for_retransmit'])
                enqueued_packets_for_input = int(m.groupdict()['enqueued_packets_for_input'])
                enqueued_packets_for_mis_ordered = int(m.groupdict()['enqueued_packets_for_mis_ordered'])
                num_bytes = int(m.groupdict()['num_bytes'])
                continue
            # Event Timers (current time is 0x530449):
            # Timer          Starts    Wakeups            Next
            # Retrans            86          0             0x0
            # TimeWait            0          0             0x0
            # AckHold            80         72             0x0
            # SendWnd             0          0             0x0
            # KeepAlive           0          0             0x0
            # GiveUp              0          0             0x0
            # PmtuAger            1          1             0x0
            # DeadWait            0          0             0x0
            # Linger              0          0             0x0
            # ProcessQ            0          0             0x0
            p39 = re.compile(
                r'^\s*(?P<name>\S+) +(?P<starts>[0-9]+) +(?P<wakeups>[0-9]+) +(?P<next>0x[0-9a-f]+)$')
            m = p39.match(line)
            if m:
                event_name = m.groupdict()['name'].lower()
                event_starts = int(m.groupdict()['starts'])
                event_wakeups = int(m.groupdict()['wakeups'])
                event_next = m.groupdict()['next']

                if 'bgp_event_timer' not in \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]: \
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                            ['bgp_event_timer'] = {}
                if 'starts' not in parsed_dict['vrf'][vrf_name] \
                        ['neighbor'][neighbor_id]['bgp_event_timer']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_event_timer']['starts'] = {}
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_event_timer']['starts'][event_name] = event_starts

                if 'wakeups' not in parsed_dict['vrf'][vrf_name] \
                        ['neighbor'][neighbor_id]['bgp_event_timer']:
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_event_timer']['wakeups'] = {}
                parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_event_timer']['wakeups'][event_name] = event_wakeups

                if event_next:
                    if 'next' not in parsed_dict['vrf'][vrf_name]\
                            ['neighbor'][neighbor_id]['bgp_event_timer']:
                        parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                            ['bgp_event_timer']['next'] = {}
                    parsed_dict['vrf'][vrf_name]['neighbor'][neighbor_id]\
                        ['bgp_event_timer']['next'][event_name] = event_next
                continue

            # iss:   55023811  snduna:   55027115  sndnxt:   55027115
            p40 = re.compile(r'^\s*iss:'
                             '\s+(?P<iss>[0-9]+)'
                             '\s+snduna: +(?P<snduna>[0-9]+)'
                             '\s+sndnxt: +(?P<sndnxt>[0-9]+)$')
            m = p40.match(line)
            if m:
                iss = m.groupdict()['iss']
                snduna = m.groupdict()['snduna']
                sndnxt = m.groupdict()['sndnxt']
                continue

            # irs:  109992783  rcvnxt:  109995158
            p41 = re.compile(r'^\s*irs:'
                             '\s+(?P<irs>[0-9]+)'
                             '\s+rcvnxt: +(?P<rcvnxt>[0-9]+)$')
            m = p41.match(line)
            if m:
                irs = m.groupdict()['irs']
                rcvnxt = m.groupdict()['rcvnxt']
                continue
            # sndwnd:  16616  scale:      0  maxrcvwnd:  16384
            p42 = re.compile(r'^\s*sndwnd:'
                             '\s+(?P<sndwnd>[0-9]+)'
                             '\s+scale: +(?P<send_scale>[0-9]+)'
                             '\s+maxrcvwnd: +(?P<maxrcvwnd>[0-9]+)$')
            m = p42.match(line)
            if m:
                sndwnd = m.groupdict()['sndwnd']
                send_scale = m.groupdict()['send_scale']
                maxrcvwnd = m.groupdict()['maxrcvwnd']
                continue
            # rcvwnd:  16327  scale:      0  delrcvwnd:     57
            p43 = re.compile(r'^\s*rcvwnd:'
                             '\s+(?P<rcvwnd>[0-9]+)'
                             '\s+scale:\s+(?P<rcv_scale>[0-9]+)'
                             '\s+delrcvwnd:\s+(?P<delrcvwnd>[0-9]+)$')
            m = p43.match(line)
            if m:
                rcvwnd = m.groupdict()['rcvwnd']
                rcv_scale = m.groupdict()['rcv_scale']
                delrcvwnd = m.groupdict()['delrcvwnd']
                continue
            # SRTT: 1000 ms, RTTO: 1003 ms, RTV: 3 ms, KRTT: 0 ms
            p44 = re.compile(r'^\s*SRTT:'
                             ' +(?P<srtt>[0-9]+) +ms,'
                             ' +RTTO: +(?P<rtto>[0-9]+) +ms,'
                             ' +RTV: +(?P<rtv>[0-9]+) +ms,'
                             ' +KRTT: +(?P<krtt>[0-9]+) +ms$')
            m = p44.match(line)
            if m:
                srtt = m.groupdict()['srtt']
                rtto = m.groupdict()['rtto']
                rtv = m.groupdict()['rtv']
                krtt = m.groupdict()['krtt']
                continue

            # minRTT: 4 ms, maxRTT: 1000 ms, ACK hold: 200 ms
            p45 = re.compile(r'^\s*minRTT:'
                             ' +(?P<min_rtt>[0-9]+) +ms,'
                             ' +maxRTT: +(?P<max_rtt>[0-9]+) +ms,'
                             ' +ACK +hold: +(?P<ack_hold>[0-9]+) +ms$')
            m = p45.match(line)
            if m:
                min_rtt = m.groupdict()['min_rtt']
                max_rtt = m.groupdict()['max_rtt']
                ack_hold = m.groupdict()['ack_hold']
                continue
            # uptime: 4236258 ms, Sent idletime: 4349 ms, Receive idletime: 4549 ms
            p46 = re.compile(r'^\s*uptime:'
                             ' +(?P<uptime>[0-9]+) +ms,'
                             ' +Sent +idletime: +(?P<send_idletime>[0-9]+) +ms,'
                             ' +Receive +idletime: +(?P<receive_idletime>[0-9]+) +ms$')
            m = p46.match(line)
            if m:
                uptime = m.groupdict()['uptime']
                send_idletime = m.groupdict()['send_idletime']
                receive_idletime = m.groupdict()['receive_idletime']
                continue
            # Status Flags: active open
            p47 = re.compile(r'^\s*Status +Flags:'
                             ' +(?P<flag_status_1>[a-zA-Z]+) (?P<flag_status_2>[a-zA-Z]+)$')
            m = p47.match(line)
            if m:
                flag_status_1 = m.groupdict()['flag_status_1']
                flag_status_2 = m.groupdict()['flag_status_2']
                continue
            # Option Flags: nagle, path mtu capable
            p48 = re.compile(r'^\s*Option +Flags:'
                             ' +(?P<option_flags>[a-zA-Z\s\,]+)$')
            m = p48.match(line)
            if m:
                option_flags = m.groupdict()['option_flags']
                continue

            # IP Precedence value : 6
            p49 = re.compile(r'^\s*IP +Precedence +value :'
                             ' +(?P<ip_precedence_value>[0-9]+)$')
            m = p49.match(line)
            if m:
                ip_precedence_value = m.groupdict()['ip_precedence_value']
                continue
            # Datagrams (max data segment is 536 bytes):
            p50 = re.compile(r'^\s*Datagrams +\(max +data +segment +is'
                             ' +(?P<datagram>[0-9]+) +bytes\):$')
            m = p50.match(line)
            if m:
                datagram = m.groupdict()['datagram']
                continue
            # Rcvd: 164 (out of order: 0), with data: 80, total data bytes: 2374
            p51 = re.compile(r'^\s*Rcvd: (?P<received>[0-9]+)'
                             ' \(out +of +order: +(?P<out_of_order>[0-9]+)\),'
                             ' +with +data: (?P<with_data>[0-9]+),'
                             ' +total +data +bytes: (?P<total_data>[0-9]+)$')
            m = p51.match(line)
            if m:
                received = m.groupdict()['received']
                out_of_order = m.groupdict()['out_of_order']
                with_data = m.groupdict()['with_data']
                total_data = m.groupdict()['total_data']
                continue
            # Sent: 166 (retransmit: 0, fastretransmit: 0, partialack: 0, Second Congestion: 0),
            #       with data: 87, total data bytes: 3303
            p52 = re.compile(r'^\s*Sent: (?P<sent>[0-9]+)'
                             ' \(retransmit: +(?P<retransmit>[0-9]+),'
                             ' +fastretransmit: +(?P<fastretransmit>[0-9]+),'
                             ' +partialack: +(?P<partialack>[0-9]+),'
                             ' +Second +Congestion: +(?P<second_congestion>[0-9]+)\),'
                             ' +with +data: (?P<sent_with_data>[0-9]+),'
                             ' +total +data +bytes: (?P<sent_total_data>[0-9]+)$')
            m = p52.match(line)
            if m:
                sent = m.groupdict()['sent']
                retransmit = m.groupdict()['retransmit']
                fastretransmit = m.groupdict()['fastretransmit']
                partialack = m.groupdict()['partialack']
                second_congestion = m.groupdict()['second_congestion']
                sent_with_data = m.groupdict()['sent_with_data']
                sent_total_data = m.groupdict()['sent_total_data']
                continue
            # Packets received in fast path: 0, fast processed: 0, slow path: 0
            p53 = re.compile(r'^\s*Packets +received +in +fast +path:'
                             ' +(?P<packet_received_in_fast_path>[0-9]+),'
                             ' +fast +processed: +(?P<fast_processed>[0-9]+),'
                             ' +slow +processed: +(?P<slow_processed>[0-9]+)$')
            m = p53.match(line)
            if m:
                packet_received_in_fast_path = m.groupdict()['packet_received_in_fast_path']
                fast_processed = m.groupdict()['fast_processed']
                slow_processed = m.groupdict()['slow_processed']
                continue
            # fast lock acquisition failures: 0, slow path: 0
            p54 = re.compile(r'^\s*fast +lock +acquisition +failures:'
                             ' +(?P<fast_lock_acquisition_failures>[0-9]+),'
                             ' +slow +path: +(?P<slow_path>[0-9]+)$')
            m = p54.match(line)
            if m:
                fast_lock_acquisition_failures = m.groupdict()['fast_lock_acquisition_failures']
                slow_path = m.groupdict()['slow_path']
                continue

            # TCP Semaphore      0x1286E7EC  FREE 
            p55 = re.compile(r'^\s*TCP +Semaphore'
                             ' +(?P<tcp_semaphore>0x[0-9a-fA-F]+)'
                             ' +(?P<tcp_status>[a-zA-Z]+)$')
            m = p55.match(line)
            if m:
                tcp_semaphore = m.groupdict()['tcp_semaphore']
                tcp_status = m.groupdict()['tcp_status']
                continue

        return parsed_dict