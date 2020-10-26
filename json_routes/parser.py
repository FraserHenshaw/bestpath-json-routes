import json
import logging
import re
import ndjson

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('json_routes.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

newline_pattern = r"(\s+)"

# Standard naming for protocols
_protocols = {
    'bgp': 'bgp',
    'ospf': 'ospf',
    'isis': 'isis',
    'rip': 'rip',
    'static': 'static',
    'eigrp': 'eigrp',
    'local': 'local',
    'connected': 'connected'
}

_route_types = {
}

class RouteParser(object):
    def __init__(self, args):
        self.device_type = args.get('device')
        self.file_location = args.get('file')
        self.file_name = ''
        self.file_as_list =  []
        self.data = []

        self.handle_file()

    def get_parser(self):
        """Method to handle getting the right parser based on the device type"""
        if self.device_type == 'nxos':
            logger.debug('Cisco NXOS device specified')
            self.parse_cisconexus()
        elif self.device_type == 'ios':
            logger.debug('Cisco IOS device specified')
            self.parse_ciscoios()
        elif self.device_type == 'fortinet':
            logger.debug('Fortinet device specified')
            self.parse_fortinet()

    def handle_file(self):
        """
        Method to handle oepning and closing the file
        It will call the relevant device Parser based on the device
        """
        logger.debug(f'Trying to open file at: {self.file_location}')
        try:
            with open(self.file_location) as file:
                self.file_name = file.name.split('/')[-1].strip('.txt')
                logger.debug('Loading file into local variable.')
                self.file_as_list = file.readlines()

                if len(self.file_as_list) == 0:
                    raise ValueError('Parsed file has 0 lines.')
                    logger.exception('Parsed file has 0 lines.')

                logger.debug('passing file to parsers')
                self.get_parser()

                result = [json.dumps(record) for record in self.data]
                logger.debug('parsing complete enter file name')
                filename = input('Save File as: ')
                with open(f'{filename}.json', 'w+') as savefile:
                    logger.debug('formatting JSON as newline delimted')
                    writer = ndjson.writer(savefile, ensure_ascii=False)
                    for route in self.data:
                        writer.writerow(route)

        except IOError as e:
            logger.exception('Unable to open the file')

    def build_dict(self, name='', vrf='', prefix='', nexthops=[]):
        """Method to build the datastructure"""

        data = {
            "device": name,
            "vrf": vrf,
            "prefix": prefix,
            "nexthop": []
        }

        for nexthop in nexthops:

            nexthop_data = {
                "ip": nexthop['ip'],
                "ifname": nexthop['ifname'],
                "ad": nexthop['ad'],
                "metric": nexthop['metric'],
                "protocol": nexthop['protocol'],
                "process": nexthop['process'],
                "type": nexthop['type'],
                "tag": nexthop['tag'],
                "age": nexthop['age']
            }

            data['nexthop'].append(nexthop_data)

        self.data.append(data)

    def parse_cisconexus(self):
        """Handle parsing text file for cisco Nexus switches"""

        vrf_pattern = re.compile(r"\"(.*?)\"")
        prefix_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}")
        ip_pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|Null0")
        ad_metric_pattern = re.compile(r"\[(.*?)\]")

        nexthops = []
        prefix = None
        vrf = None

        for line in self.file_as_list:
            if line.startswith('IP Route Table for VRF'):
                # This is needed to build the last Route entry before a new VEF is discovered.
                if prefix:
                    self.build_dict(name=self.file_name, vrf=vrf, prefix=prefix, nexthops=nexthops)
                    nexthops = []
                #  Check if this is a new VRF
                if vrf:
                    if vrf != vrf_pattern.findall(line)[0]:
                        prefix = None

                vrf = vrf_pattern.findall(line)[0]


            # Match IP Prefix
            prefix_match = prefix_pattern.findall(line)
            if prefix_match:
                if prefix:
                    if prefix_match[0] != prefix:
                        """Check if prefix matches pre existing prefix if No this is a new route and previous data is complete and can be sent to data
                        dict"""
                        self.build_dict(name=self.file_name, vrf=vrf, prefix=prefix, nexthops=nexthops)
                        nexthops = []

                prefix = prefix_match[0]

            # Match Unicast Next Hope
            if '*via' in line:
                nexthop_dict = {
                    "ip": '',
                    "ifname": '',
                    "ad": '',
                    "metric": '',
                    "protocol": '',
                    "process": '',
                    "type": '',
                    "tag": '',
                    "age": ''
                }
                # Cleanup newline characters
                raw_line = re.sub(newline_pattern, '', line)
                raw_nexthop = raw_line.split(',')

                #  Get nexthop IP
                try:
                    nh_ip = ip_pattern.findall(line)[0]
                except IndexError:
                    # No IP found in string
                    print('here')
                    print(raw_nexthop[0])
                    nh_ip = ''
                    logger.exception(f'No Nexthop IP found in string {raw_nexthop[0]}')

                nexthop_dict.update({
                    'ip': nh_ip
                })

                # Get AD and Metric
                try:
                    ad_metric = ad_metric_pattern.findall(raw_line)[0].split('/')
                    ad = ad_metric[0]
                    metric = ad_metric[1]
                except IndexError:
                    ad = ''
                    metric = ''
                    logger.exception(f'No Nexthop IP found in string {raw_line[0]}')

                nexthop_dict.update({
                    'ad': ad,
                    'metric': metric
                })

                # Protocol, Type, Age, Tag and Interface positions vary depending on the route type
                if len(raw_nexthop) <= 4:
                    protocol = raw_nexthop[-1]
                    age = raw_nexthop[-2]
                    if_name = ''
                    tag = ''
                    route_type = ''
                elif len(raw_nexthop) == 5:
                    protocol = raw_nexthop[-1]
                    age = raw_nexthop[-2]
                    if_name = raw_nexthop[1]
                    tag = ''
                    route_type = ''
                elif len(raw_nexthop) == 6:
                    # Check if if name is presant
                    if_check = ad_metric_pattern.findall(raw_nexthop[1])
                    if len(if_check) == 0:
                        if_name = raw_nexthop[1]
                    else:
                        if_name = ''

                    # Deal with routes with tags
                    if 'tag' in raw_nexthop[-1]:
                        tag = raw_nexthop[-1].replace('tag', '')
                        protocol = raw_nexthop[-3]
                        route_type = raw_nexthop[-2]
                        age = raw_nexthop[-4]
                    else:
                        tag = ''
                        protocol = raw_nexthop[-2]
                        route_type = raw_nexthop[-1]
                        age = raw_nexthop[-3]

                #  Split the protocol and process
                raw_protocol = protocol.split('-')
                protocol = raw_protocol[0]
                process = raw_protocol[-1]

                # TODO fixup and put protocols here

                nexthop_dict.update({
                    "ifname": if_name,
                    "protocol": protocol,
                    "process": process,
                    "type": route_type,
                    "tag": tag,
                    "age": age
                })

                nexthops.append(nexthop_dict)

    def parse_ciscoios(self):
        """Handle parsing text file for cisco IOS switches"""

        vrf_pattern = re.compile(r"(?<=Routing Table: ).*")
        prefix_pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}")
        ip_pattern = re.compile(r"(?!\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|Null0)")
        ad_metric_pattern = re.compile(r"\[(.*?)\]")

        nexthops = []
        prefix = None

        for line in self.file_as_list:
            print(line)
            if 'variably subnetted' in line:
                # Skip lines that provide no data
                continue
            if line.startswith('Routing Table:'):
                vrf = vrf_pattern.findall(line)[0]

            # Get the protocol and type
            elif line.startswith('B'):
                protocol = _protocols['bgp']
                if_name = ''
                age = line.split(',')[-1].replace(' ', '')
            elif line.startswith('S'):
                protocol = _protocols['static']
                if_name = ''
                age = ''
            elif line.startswith('C') and not line.startswith('Codes'):
                protocol = _protocols['connected']
                if_name = line.split(',')[-1].replace(' ', '')
                age = ''
            elif line.startswith('L'):
                protocol = _protocols['local']
                if_name = line.split(',')[-1].replace(' ', '')
                age = ''
            elif line.startswith('O'):
                protocol = _protocols['ospf']
                if_name = ''
                age = line.split(',')[-1].replace(' ', '')
            elif line.startswith('D'):
                protocol = _protocols['eigrp']
                if_name = ''
                age = line.split(',')[-1].replace(' ', '')
            elif line.startswith('R') and not line.startswith('RoutingTable'):
                protocol = _protocols['rip']
                if_name = ''
                age = line.split(',')[-1].replace(' ', '')
            elif line.startswith('i'):
                protocol = _protocols['isis']
                if_name = ''
                age = line.split(',')[-1].replace(' ', '')

            # Match IP Prefix
            prefix_match = prefix_pattern.findall(line)
            if prefix_match:
                if prefix:
                    if prefix_match[0] != prefix:
                        """Check if prefix matches pre existing prefix if No this is a new route and previous data is complete and can be sent to data
                        dict"""
                        self.build_dict(name=self.file_name, vrf=vrf, prefix=prefix, nexthops=nexthops)
                        nexthops = []

                prefix = prefix_match[0]

            # Match Unicast Next Hope
            if 'via' in line or 'connected' in line and not line.startswith('Codes'):
                print('here')
                nexthop_dict = {
                    "ip": '',
                    "ifname": '',
                    "ad": '',
                    "metric": '',
                    "protocol": '',
                    "process": '',
                    "type": '',
                    "tag": '',
                    "age": ''
                }
                # Cleanup newline characters
                raw_line = re.sub(newline_pattern, '', line)
                raw_nexthop = raw_line.split(',')

                #  Get nexthop IP
                try:
                    nh_ip = ip_pattern.findall(line)[0]
                except IndexError:
                    # No IP found in string
                    nh_ip = ''
                    logger.exception(f'No Nexthop IP found in string {raw_nexthop[0]}')

                nexthop_dict.update({
                    'ip': nh_ip
                })

                # Get AD and Metric
                try:
                    ad_metric = ad_metric_pattern.findall(raw_line)[0].split('/')
                    ad = ad_metric[0]
                    metric = ad_metric[1]
                except IndexError:
                    ad = ''
                    metric = ''
                    logger.exception(f'No Nexthop IP found in string {raw_line[0]}')

                nexthop_dict.update({
                    'ad': ad,
                    'metric': metric
                })

                # Protocol, Type, Age, Tag and Interface positions vary depending on the route type
                nexthop_dict.update({
                    "ifname": if_name,
                    "protocol": protocol,
                    # "type": route_type,
                    # "tag": tag,
                    "age": age
                })

                nexthops.append(nexthop_dict)


    def parse_fortinet(self):
        """Handle parsing text file for Fortinet Firewalls"""

        prefix_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}")
        ip_pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        ad_metric_pattern = re.compile(r"\[(.*?)\]")

        nexthops = []
        prefix = None

        nexthops = []
        prefix = None
        vrf = ''
        for line in self.file_as_list:
            prefix_match = prefix_pattern.findall(line)
            if prefix_match:
                if prefix:
                    if prefix_match[0] != prefix:
                        """Check if prefix matches pre existing prefix if No this is a new route and previous data is complete and can be sent to data
                        dict"""
                        self.build_dict(name=self.file_name, vrf=vrf, prefix=prefix, nexthops=nexthops)
                        nexthops = []

                prefix = prefix_match[0]
