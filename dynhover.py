#!/usr/bin/python

import ConfigParser
import requests
import optparse
import sys


class HoverException(Exception):
    pass


class HoverAPI(object):
    def __init__(self, username, password):
        params = {"username": username, "password": password}
        r = requests.post("https://www.hover.com/signin", params=params)
        if not r.ok or "hoverauth" not in r.cookies:
            raise HoverException(r)
        self.cookies = {"hoverauth": r.cookies["hoverauth"]}
    def call(self, method, resource, data=None):
        url = "https://www.hover.com/api/{0}".format(resource)
        r = requests.request(method, url, data=data, cookies=self.cookies)
        if not r.ok:
            raise HoverException(r)
        if r.content:
            return r.json()


def get_public_ip():
    return requests.get("http://api.exip.org/?call=ip").content


def update_dns(username, password, fqdn):
    try:
        client = HoverAPI(username, password)
    except HoverException as e:
        raise HoverException("Authentication failed")
    dns = client.call("get", "dns")
    dns_id = None
    for domain in dns["domains"]:
        if fqdn == domain["domain_name"]:
            fqdn = "@.{domain_name}".format(**domain)
        for entry in domain["entries"]:
            if entry["type"] != "A": continue
            if "{0}.{1}".format(entry["name"], domain["domain_name"]) == fqdn:
                dns_id = entry["id"]
                break
    if dns_id is None:
        raise HoverException("No DNS record found for {0}".format(fqdn))

    my_ip = get_public_ip()

    response = client.call("put", "dns/{0}".format(dns_id), {"content": my_ip})
    
    if "succeeded" not in response or response["succeeded"] is not True:
        raise HoverException(response)
    

def main():
    usage = "usage: %prog (-c CONF|-u USERNAME -p PASSWORD -d DOMAIN)"
    description = "Update a hover.com DNS record with the current IP of this machine."
    parser = optparse.OptionParser(usage=usage, description=description)
    parser.add_option("-c", "--conf", default=None, help="The conf file that contains your username, password, and fully qualified domain name")
    parser.add_option("-u", "--username", default=None, help="Your hover.com username")
    parser.add_option("-p", "--password", default=None, help="Your hover.com password")
    parser.add_option("-d", "--domain", default=None, help="The fully qualified domain name you're updating")
    (options, args) = parser.parse_args()

    def get_conf(filename):
        config = ConfigParser.ConfigParser()
        config.read(filename)
        items = dict(config.items("dynhover"))
        return items["username"], items["password"], items["domain"]

    if options.conf is None:
        if not all((options.username, options.password, options.domain)):
            parser.error("You must specifiy either a conf file, or a username, password, and domain")
        else:
            username, password, domain = options.username, options.password, options.domain
    else:
        username, password, domain = get_conf(options.conf)

    update_dns(username, password, domain)


if __name__ == "__main__":
    try:
        main()
    except HoverException as e:
        print "Unable to update DNS: {0}".format(e)
        sys.exit(1)
    sys.exit(0)        
