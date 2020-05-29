from requests import get
from xml.etree import ElementTree as ET
from datetime import datetime
from re import sub


class HamNetlogger():
    '''
    A python class to handle the netlogger.org api, which will query active and past net and their checkins.

    API details can be found. Please ensure that you're following netlogger's rules for usage of their API:
    http://www.netlogger.org/api/The%20NetLogger%20XML%20Data%20Service%20Interface%20Specification.pdf

    Justin Sligh, 2020
    '''

    def __init__(self):
        self.baseurl = 'http://www.netlogger.org/api/'
        self.headers = {'Content-Type': 'application/xml', 'Cache-Control': 'no-cache'}
        self.servers = []
        self.nets = []
        self.date_format = '%Y-%m-%d %H:%M:%S'
        self.user_agent = 'HamNetlogger/0.0.1'  # This must be unique to your application

    def cleanup_details(self, details):

        # Frequency is not rigid. Could be anything. This attempts to create a float
        if 'Frequency' in details:

            frequency_raw = details['Frequency']

            # Strip out text
            frequency_digits = sub(r'[a-z]', '', frequency_raw)

            try:
                frequency = float(frequency_digits)
            except ValueError:
                frequency = frequency_digits

            details['Frequency'] = frequency

        # Convert string to time object
        if 'Date' in details:
            d = details['Date']

            d = datetime.strptime(d, self.date_format)

            details['Date'] = d

        # -----Additional Fields in Past Nets

        if 'LastActivity' in details:
            d = details['LastActivity']

            d = datetime.strptime(d, self.date_format)

            details['LastActivity'] = d

        if 'ClosedAt' in details:
            d = details['ClosedAt']

            d = datetime.strptime(d, self.date_format)

            details['ClosedAt'] = d

        return details

    def get_nets(self, endpoint):

        url = self.baseurl + endpoint

        response = get(url, headers=self.headers)

        if response.status_code == 200:

            # Convert to workable XML
            response_xml = ET.fromstring(response.content)

            for server in response_xml.iter('ServerName'):
                self.servers.append(server.text)

            if self.servers:

                for server in self.servers:

                    for net in response_xml.findall("./ServerList/Server[ServerName='" + server + "']/Net"):

                        net_details = {}

                        net_details['Server'] = server

                        for detail in net.iter():
                            if detail.tag != 'Net':
                                net_details[detail.tag] = detail.text

                        # Cleanup details
                        net_details_clean = self.cleanup_details(net_details)

                        self.nets.append(net_details_clean)

            else:
                return None

            return self.nets

        else:
            print('Error in HamNetlogger: HTML Error Code ' + str(response.status_code))

    def get_active_nets(self):
        endpoint = 'GetActiveNets.php'
        nets = self.get_nets(endpoint=endpoint)
        return nets

    def get_active_net_checkins(self, server, net):

        endpoint = 'GetCheckins.php'

        checkins = self.get_checkins(endpoint=endpoint, server=server, net=net)

        return checkins

    def get_past_net_checkins(self, server, net, net_id):

        checkins = self.get_checkins(endpoint='GetPastNetCheckins.php', server=server, net=net, net_id=net_id)

        return checkins

    def get_checkins(self, endpoint, server, net, net_id=''):

        net = net.replace(' ', '%20')

        if endpoint == 'GetCheckins.php':
            url = self.baseurl + endpoint + '?ServerName=' + server + '&NetName=' + net

        elif endpoint == 'GetPastNetCheckins.php':

            if net_id:

                url = self.baseurl + endpoint + '?ServerName=' + server + '&NetName=' + net + '&NetID=' + str(net_id)

            else:
                print('Error in HamNetlogger get_checkins. Needs net id for past net checkins')
                return None

        else:
            print('Error in HamNetlogger. Unknown endpoint')
            return None

        print(url)

        response = get(url, headers=self.headers)

        if response.status_code == 200:

            # Convert to workable XML
            response_xml = ET.fromstring(response.content)

            checkins = []

            for station in response_xml.findall("./CheckinList/Checkin"):

                checkin_details = {}

                for detail in station.iter():
                    if detail.tag != 'Checkin':
                        checkin_details[detail.tag] = detail.text

                # TODO: Cleanup details
                checkin_details_clean = checkin_details

                checkins.append(checkin_details_clean)

            return checkins

        else:
            print('Error in HamNetlogger: HTML Error Code ' + str(response.status_code))

    def get_past_nets(self, interval=''):

        if interval:
            endpoint = 'GetPastNets.php?Interval=' + str(interval)

        else:
            endpoint = 'GetPastNets.php'

        nets = self.get_nets(endpoint=endpoint)

        return nets

    def get_past_checkins(self, server, net):
        pass


if __name__ == "__main__":
    h = HamNetlogger()
