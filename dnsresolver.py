import dns.message
import dns.query
import dns.rdatatype
import dns.exception
import random

"""
dns libray from dnspython
dns.message     : Helps create the actual DNS query message.
dns.query       : Handles sending the query over the network (in this case, using UDP).
dns.rdatatype   : Contains constants for different DNS record types, like A (IPv4 address), NS (Name Server), or CNAME (Canonical Name).
dns.exception   : Used for handling errors, like a Timeout.

standard library
random  : to pick random nameserver from a list to query.
"""

# Root servers (IPv4 list) https://en.wikipedia.org/wiki/Root_name_server
ROOT_SERVERS = [
    "198.41.0.4",      # a.root-servers.net
    "199.9.14.201",    # b.root-servers.net
    "192.33.4.12",     # c.root-servers.net
    "199.7.91.13",     # d.root-servers.net
    "192.203.230.10",  # e.root-servers.net
    "192.5.5.241",     # f.root-servers.net
    "192.112.36.4",    # g.root-servers.net
    "198.97.190.53",   # h.root-servers.net
    "192.36.148.17",   # i.root-servers.net
    "192.58.128.30",   # j.root-servers.net
    "193.0.14.129",    # k.root-servers.net
    "199.7.83.42",     # l.root-servers.net
    "202.12.27.33"     # m.root-servers.net
]

def resolve(domain, qtype=dns.rdatatype.A):

    # Recursive resolver implementation.

    nameservers = ROOT_SERVERS[:]
    visited = []

    while True:
        if not nameservers:
            raise Exception("No more nameservers to query.")

        ns = random.choice(nameservers)
        visited.append(ns)

        try:
            query = dns.message.make_query(domain, qtype)
            response = dns.query.udp(query, ns, timeout=3)

            # 1. Check ANSWER
            """
            If the answer type matches what we asked for (qtype), it prints the query path and returns the answer, ending the loop.
            If the answer is a CNAME (a nickname for another domain), the resolver must start the whole process over again for the 
            new domain name. It does this by calling itself recursively: return resolve(cname, qtype).
            """
            if response.answer:
                for ans in response.answer:
                    if ans.rdtype == qtype:
                        print(" --> ".join(visited))
                        return ans
                    elif ans.rdtype == dns.rdatatype.CNAME:
                        cname = str(ans[0].target)
                        print(f"CNAME found: {cname}")
                        return resolve(cname, qtype)


            # 2. Check ADDITIONAL (gives us IPs of NS)
            """
            If there was no final answer, the server is referring us to other nameservers. 
            Often, to be helpful, the server will provide the IP addresses (A records) of those next-level nameservers in the 
            "additional" section, these are called glue records.
            This code extracts those IP addresses, sets them as the nameservers for the next iteration 
            of the loop, and uses continue to start the loop again, querying these new servers.
            """
            new_ns = []
            for add in response.additional:
                if add.rdtype == dns.rdatatype.A:
                    for item in add:
                        new_ns.append(item.address)
            if new_ns:
                nameservers = new_ns
                continue

            # 3. Check AUTHORITY (gives us hostnames of NS)
            """
            If there was no final answer and no glue records, the server gives us a referral in the "authority" section.
            However, this section usually contains the domain names of the next nameservers (e.g., a.gtld-servers.net), 
            not their IP addresses.
            The code first collects these names. It must now resolve each of these nameserver domain names into an IP address.
            It does this by making a recursive call: ns_ans = resolve(ns_name, dns.rdatatype.A).
            Once it has the IPs of the next-level servers, it updates the nameservers list and continues the main loop.
            """
            ns_names = []
            for auth in response.authority:
                if auth.rdtype == dns.rdatatype.NS:
                    for item in auth:
                        ns_names.append(str(item.target))

            # Resolve NS names to IPs
            new_ns = []
            for ns_name in ns_names:
                ns_ans = resolve(ns_name, dns.rdatatype.A)
                if ns_ans:
                    for r in ns_ans:
                        new_ns.append(r.address)
            if new_ns:
                nameservers = new_ns
                continue
            """
            If a query to a server times out or fails for another reason, the script prints an error, removes the failed server from the list, 
            and the while loop continues, trying another server from the list.
            """
        except dns.exception.Timeout:
            print(f"Timeout querying {ns}, trying another...")
            nameservers.remove(ns)
        except Exception as e:
            print(f"Error: {e}")
            nameservers.remove(ns)


# calls resolve function for domain.
if __name__ == "__main__":
    domain = input()
    answer = resolve(domain)
    print("\nFinal Answer:")
    print(answer)
