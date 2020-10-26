### Readme

Python script to convert raw show ip route text output from various platforms to newline-delimited JSON for use in Elastic Search and Kibana.

##### Arguments
- -f file
- -d device


##### File formats

##### Output
- Normal JSON
```json
[
    {
        "device": "CORE_SWITCH",
        "vrf": "CORE",
        "prefix": "10.1.0.0/16",
        "nexthop": [
            {
                "ip": "10.254.1.1",
                "ifname": "Po2.321",
                "ad": "110",
                "metric": "210",
                "protocol": "ospf-220",
                "type": "intra",
                "tag": "",
                "age": "34w1d"
            },
            {
                "ip": "10.254.1.2",
                "ifname": "Po2.322",
                "ad": "110",
                "metric": "210",
                "protocol": "ospf-220",
                "type": "intra",
                "tag": "",
                "age": "34w1d"
            }
        ]
    },
    {
        "device": "CORE_SWITCH",
        "vrf": "CORE",
        "prefix": "10.2.0.0/16",
        "nexthop": [
            {
                "ip": "10.254.1.1",
                "ifname": "Po2.321",
                "ad": "110",
                "metric": "210",
                "protocol": "ospf",
                "process": "220",
                "type": "intra",
                "tag": "",
                "age": "34w1d"
            },
            {
                "ip": "10.254.1.2",
                "ifname": "Po2.322",
                "ad": "110",
                "metric": "210",
                "protocol": "ospf",
                "process": "220",
                "type": "intra",
                "tag": "",
                "age": "34w1d"
            }
        ]
    }
]
```

- newline-delimited JSON
```
{"device": "CORE_SWITCH", "prefix": "10.1.0.0/16", "nexthop": [{"age": "34w1d", "tag": "", "protocol": "ospf-220", "ad": "110", "ip": "10.254.1.1", "ifname": "Po2.321", "type": "intra", "metric": "210"}, {"age": "34w1d", "tag": "", "protocol": "ospf-220", "ad": "110", "ip": "10.254.1.2", "ifname": "Po2.322", "type": "intra", "metric": "210"}], "vrf": "CORE"}\n{"device": "CORE_SWITCH", "prefix": "10.2.0.0/16", "nexthop": [{"age": "34w1d", "tag": "", "protocol": "ospf-220", "ad": "110", "ip": "10.254.1.1", "ifname": "Po2.321", "type": "intra", "metric": "210"}, {"age": "34w1d", "tag": "", "protocol": "ospf-220", "ad": "110", "ip": "10.254.1.2", "ifname": "Po2.322", "type": "intra", "metric": "210"}], "vrf": "CORE"}
```