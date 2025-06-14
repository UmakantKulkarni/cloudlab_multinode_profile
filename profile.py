# -*- coding: utf-8 -*-
"""Paramaterized profile to create a multisite experiment. 
"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.igext as ig
import geni.rspec.emulab as emulab

# --- Portal setup ---
pc = portal.Context()
request = pc.makeRequestRSpec()

def findName(list, key):
    for pair in list:
        if pair[0] == key:
            return pair[1]
    return None

# A list of aggregates.
Aggregates = [
    ('',                  "None"),
    ('urn:publicid:IDN+emulab.net+authority+cm',   "Emulab"),
    ('urn:publicid:IDN+utah.cloudlab.us+authority+cm',  "Utah"),
    ('urn:publicid:IDN+wisc.cludlab.us.net+authority+cm', "Wisconsin"),
    ('urn:publicid:IDN+clemson.cludlab.us.net+authority+cm',"Clemson"),
]

# Common OS‐image list
imageList = [
    ('default', 'Default Image'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:ztx_ubuntu22','UBUNTU 22.04 ZTX'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:p4_sdn',       'P4-SDN UBUNTU22'),
    ('urn:publicid:IDN+cloudlab.umass.edu+image+sfcs-PG0:BG_QOE_PRED_P4_SDN','QOE-PRED-P4-SDN'),
    # …etc…
]

# Optional hardware‐type list (you can also leave this empty to let the mapper choose)
hwTypes = [
    ("",        "Default"),
    ("pc3000",  "pc3000"),
    ("d710",    "d710"),
    # …etc…
]

# Define a multi‐value struct for each cluster+node
ps = pc.defineStructParameter(
    "clusters", "Clusters / Nodes", [],
    multiValue   = True,
    min           = 1,
    multiValueTitle = "Add another cluster block",
    members = [
        portal.Parameter("cluster", "Cluster (aggregate)", 
                         portal.ParameterType.STRING, Aggregates[0], Aggregates),
        portal.Parameter("count",   "Number of Nodes", 
                         portal.ParameterType.INTEGER, 1),
        portal.Parameter("lan",     "Create a LAN?", 
                         portal.ParameterType.BOOLEAN, False,
                         longDescription="If you want your nodes in this block on a LAN"),
        # <<< added per‐node OS choice
        portal.Parameter("osImage", "OS Image for each node",
                         portal.ParameterType.IMAGE, imageList[0], imageList,
                         longDescription="Select the OS image to use on these nodes"),
        # <<< added per‐node hardware choice
        portal.Parameter("hwType",  "Hardware type for each node",
                         portal.ParameterType.NODETYPE, hwTypes[0], hwTypes,
                         longDescription="Specify the hardware type (or leave default)"),
    ]
)

# Retrieve user selections
params = pc.bindParameters()

# --- Validation (unchanged except for struct) ---
for idx, cluster in enumerate(params.clusters):
    if cluster.cluster == "":
        pc.reportError(portal.ParameterError(
            f"Entry #{idx+1}: must select a cluster", [f"clusters[{idx}].cluster"]))
    if cluster.count < 1:
        pc.reportError(portal.ParameterError(
            f"Entry #{idx+1}: count must be >= 1", [f"clusters[{idx}].count"]))

pc.verifyParameters()

# --- Build the RSpec ---
for cluster in params.clusters:
    if cluster.cluster == "":
        continue

    # optional LAN
    lan = None
    if cluster.count > 1 and cluster.lan:
        lan = request.Link() if cluster.count == 2 else request.LAN()

    for i in range(cluster.count):
        # Node naming
        basename = findName(Aggregates, cluster.cluster)
        name = f"{basename}-{i}"

        # RawPC vs XenVM (keep your existing logic if you need VMs)
        node = request.RawPC(name)

        # assign to that aggregate
        node.component_manager_id = cluster.cluster

        # per‐node OS
        if cluster.osImage and cluster.osImage != "default":
            node.disk_image = cluster.osImage

        # per‐node hardware
        if cluster.hwType:
            node.hardware_type = cluster.hwType

        # start VNC (you had this before)
        node.startVNC()

        # add to LAN
        if lan:
            iface = node.addInterface("eth1")
            lan.addInterface(iface)

# done
pc.printRequestRSpec(request)
