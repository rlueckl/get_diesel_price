#!/usr/bin/env python3

import socket
import argparse
import requests

from bs4 import BeautifulSoup
from time import time

# Favorite gas stations a.k.a. configuration
STATIONS = {'bft_Karlsruhe_WillyBrandtAlle3': 'http://www.clever-tanken.de/tankstelle_details/26052',
            'ESSO_Karlsruhe_Brauerstr1b'    : 'http://www.clever-tanken.de/tankstelle_details/17123',
            'bft_Ettlingen_Landstr1'        : 'http://www.clever-tanken.de/tankstelle_details/33149',
            'bft_Ettlingen_Hertzstr2'       : 'http://www.clever-tanken.de/tankstelle_details/49375'
           }

CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003

def send_metric(message):
    sock = socket.socket()
    sock.connect((CARBON_SERVER, CARBON_PORT))
    sock.sendall(message)
    sock.close()

def main(dry_run):
    for gas_station in STATIONS:
        # Load the HTML into BeautifulSoup.
        html_page = requests.get(STATIONS[gas_station])
        html_soup = BeautifulSoup(html_page.content, 'html.parser')

        # Search for the <div> containing the prices.
        for div in html_soup.find_all('div', {'class': 'fuel-price-entry'}):
            # We need only the price for diesel.
            if div.span.contents[0] == 'Diesel':
                # Search for the price tag...
                for span in div.find_all('span', {'ng-bind':'display_preis'}):
                    fuel_price = span.contents[0]
                # ...and the second part of the price.
                for sup in div.find_all('sup', {'ng-bind':'suffix'}):
                    fuel_extra = sup.contents[0]

        full_price = fuel_price.strip() + fuel_extra.strip()
        path_elem = gas_station.split('_')
        metric_path = 'diesel' + '.' + path_elem[0] + '.' + path_elem[1] + '.' + path_elem[2]

        if dry_run:
            print('{0} {1} {2}'.format(metric_path, float(full_price), int(time())))
        else:
            message = metric_path + " " + full_price + " " + str(time()).split('.')[0] + "\n"
            send_metric(message)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get diesel price from clever-tanken.de')
    parser.add_argument('-d', '--dry-run', dest='dry_run', action='store_true',
                        help='print to stdout instead of sending the metrics to Graphite')
    args = parser.parse_args()
    main(args.dry_run)
