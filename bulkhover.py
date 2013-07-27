#!/usr/bin/python

import ConfigParser
import requests
import optparse
import sys


# This is a command-line script to import and export DNS records for a
# single domain into or out of a hover account. Run it like so:
# ./bulkhover.py -u USERNAME -p PASSWORD (import|export) DOMAIN DNS_FILE
# or create a config file like this:
#
# [hover]
# username=USERNAME
# password=PASSWORD
#
# and run it like this:
# ./bulkhover.py -c PATH_TO_CONF (import|export) DOMAIN DNS_FILE
#
# The DNS file should have one record per line, in the format:
# {name} {type} {content}
#
# For example:
#
# www A 127.0.0.1
# @ MX 10 example.com
# 
# You can even copy the entire contents of one domain to another, like so:
# ./bulkhover.py -c CONF export example.com - | ./bulkhover.py -c CONF -f import other.com -


class HoverException(Exception):
    pass


class HoverAPI(object):
    def __init__(self, username, password):
        params = {"username": username, "password": password}
        r = requests.post("https://www.hover.com/api/login", params=params)
        if not r.ok or "hoverauth" not in r.cookies:
            raise HoverException(r)
        self.cookies = {"hoverauth": r.cookies["hoverauth"]}
    def call(self, method, resource, data=None):
        url = "https://www.hover.com/api/{0}".format(resource)
        r = requests.request(method, url, data=data, cookies=self.cookies)
        if not r.ok:
            raise HoverException(r)
        if r.content:
            body = r.json()
            if "succeeded" not in body or body["succeeded"] is not True:
                raise HoverException(body)
            return body


def import_dns(username, password, domain, filename, flush=False):
    try:
        client = HoverAPI(username, password)
    except HoverException as e:
        raise HoverException("Authentication failed")
    if flush:
        records = client.call("get", "domains/{0}/dns".format(domain))["domains"][0]["entries"]
        for record in records:
            client.call("delete", "dns/{0}".format(record["id"]))
            print "Deleted {name} {type} {content}".format(**record)
    
    domain_id = client.call("get", "domains/{0}".format(domain))["domain"]["id"]
    
    if filename == "-": filename = "/dev/stdin"
    with open(filename, "r") as f:
        for line in f:
            parts = line.strip().split(" ", 2)
            record = {"name": parts[0], "type": parts[1], "content": parts[2]}
            client.call("post", "domains/{0}/dns".format(domain), record)
            print "Created {name} {type} {content}".format(**record)

def export_dns(username, password, domain, filename):
    try:
        client = HoverAPI(username, password)
    except HoverException as e:
        raise HoverException("Authentication failed")
    records = client.call("get", "domains/{0}/dns".format(domain))["domains"][0]["entries"]
    
    if filename == "-": filename = "/dev/stdout"
    with open(filename, "w") as f:
        for record in records:
            f.write("{name} {type} {content}\n".format(**record))
    

def main():
    usage = "usage: %prog (-c CONF|-u USERNAME -p PASSWORD) (import|export) DOMAIN DNS_FILE"
    description = "Import or export DNS records for a single domain in a hover account."
    parser = optparse.OptionParser(usage=usage, description=description)
    parser.add_option("-c", "--conf", default=None, help="The conf file that contains your username and password")
    parser.add_option("-u", "--username", default=None, help="Your hover.com username")
    parser.add_option("-p", "--password", default=None, help="Your hover.com password")
    parser.add_option("-f", "--flush", default=False, action="store_true", help="Flush all DNS records associated with the domain before importing")
    (options, args) = parser.parse_args()
    
    if len(args) < 3:
        parser.error("You must specify an operation, a domain, and a file")
    
    operation, domain, filename = args
    
    if operation not in ("import", "export"):
        parser.error("Invalid operation: {0} - Valid operations are import and export".format(operation))
    
    def get_conf(filename):
        config = ConfigParser.ConfigParser()
        config.read(filename)
        items = dict(config.items("hover"))
        return items["username"], items["password"]

    if options.conf is None:
        if not all((options.username, options.password)):
            parser.error("You must specifiy either a conf file, or a username and password")
        else:
            username, password = options.username, options.password
    else:
        username, password = get_conf(options.conf)

    if operation == "import":
        import_dns(username, password, domain, filename, options.flush)
    elif operation == "export":
        export_dns(username, password, domain, filename)


if __name__ == "__main__":
    try:
        main()
    except HoverException as e:
        print "Failed while importing DNS: {0}".format(e)
        sys.exit(1)
    sys.exit(0)
