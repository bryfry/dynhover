import requests

class HoverAPI(object):
    def __init__(self, username, password):
        params = {"username": username, "password": password}
        r = requests.post("https://www.hover.com/signin", params=params)
        if not r.ok:
            raise Exception(r)
        self.cookies = {"hoverauth": r.cookies["hoverauth"]}
    def call(self, method, resource, data=None):
        url = "https://www.hover.com/api/{0}".format(resource)
        r = requests.request(method, url, data=data, cookies=self.cookies)
        if not r.ok:
            raise Exception(r)
        if r.content:
            return r.json()


client = HoverAPI("myusername", "mypassword")

# get details of a domains without DNS records
client.call("get", "domains")

# get all domains and DNS records
client.call("get", "dns")


# notice the "id" field of domains in the above calls - that's needed
# to address the domains individually, like so:

# get details of a specific domain without DNS records
client.call("get", "domains/dom123456")

# get DNS records of a specific domain:
client.call("get", "domains/dom123456/dns")

# create a new DNS record on a specific domain:
record = {"name": "mysubdomain", "type": "A", "content": "127.0.0.1"}
client.call("post", "domains/dom123456/dns", record)

# create a new SRV record
# note that content is "{priority} {weight} {port} {target}"
record = {"name": "mysubdomain", "type": "SRV", "content": "10 10 123 __service"}
client.call("post", "domains/dom123456/dns", record)

# create a new MX record
# note that content is "{priority} {host}"
record = {"name": "mysubdomain", "type": "MX", "content": "10 mail"}
client.call("post", "domains/dom123456/dns", record)


# notice the "id" field of DNS records in the above calls - that's needed
# to address the DNS records individually, like so:

# update an existing DNS record
client.call("put", "dns/dns1234567", {"content": "127.0.0.1"})

# delete a DNS record:
client.call("delete", "dns/dns1234567")