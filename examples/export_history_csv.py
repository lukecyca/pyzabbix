# The research leading to these results has received funding from the
# European Commission's Seventh Framework Programme (FP7/2007-13)
# under grant agreement no 257386.
# 	http://www.bonfire-project.eu/
# Copyright 2012 Yahya Al-Hazmi, TU Berlin
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

import argparse
import datetime
import sys
import time

from pyzabbix import ZabbixAPI


def login(zapi, username, password):
    try:
        zapi.login(username, password)
        print("login succeed.")
    except:
        print("zabbix server is not reachable: ")
        sys.exit()


def getHostId(zapi, hostname, server):
    if hostname == "":
        print("hostname is missed")
        sys.exit()
    host = zapi.host.get(filter={"host": hostname}, output="extend")
    if len(host) == 0:
        print(f"hostname: {hostname} not found in zabbix server: {server}, exit")
        sys.exit()
    else:
        return host[0]["hostid"]


def getItems(zapi, key, hostid, hostname):
    items = zapi.item.get(search={"key_": key}, hostids=hostid, output="extend")
    if len(items) == 0:
        print(f"item key: {key} not found in hostname: {hostname}")
        sys.exit()
    else:
        return items


def convertTimeStamp(inputTime):
    if inputTime == "":
        return ""
    try:
        tmpDate = datetime.datetime.strptime(inputTime, "%Y-%m-%d %H:%M:%S")
        timestamp = int(time.mktime(tmpDate.timetuple()))
    except:
        print("time data %s does not match format Y-m-d H:M:S, exit" % (datetime))
        sys.exit()

    return timestamp


def generateOutputFilename(output, hostname, key):
    if output == "":
        return hostname + "_" + key + ".csv"
    else:
        return output


def exportToCSV(historys, key, output):
    f = open(output, "w")
    inc = 0
    f.write("key;timestamp;valuei\n")  # csv header
    for history in historys:
        f.write("{};{};{}\n".format(key, history["clock"], history["value"]))
        inc = inc + 1
    print("exported %i history to %s" % (inc, output))
    f.close()


def assignTimeRange(inputParameters, datetime1, datetime2):
    timestamp1 = convertTimeStamp(datetime1)
    timestamp2 = convertTimeStamp(datetime2)

    # only timestamp1
    if timestamp1 and not timestamp2:
        inputParameters["time_from"] = timestamp1
        inputParameters["time_till"] = convertTimeStamp(time.time())  # current time
    # only timestamp2
    elif not timestamp1 and timestamp2:
        inputParameters["time_from"] = timestamp2
        inputParameters["time_till"] = timestamp2
    # no inserted both timestamps
    elif not timestamp1 and not timestamp2:
        inputParameters["time_from"] = convertTimeStamp(time.time())  # current time
        inputParameters["time_till"] = convertTimeStamp(time.time())  # current time
    # inserted both timestamps
    else:
        inputParameters["time_from"] = timestamp1
        inputParameters["time_till"] = timestamp2


def fetch_to_csv(
    username, password, server, hostname, key, output, datetime1, datetime2, debuglevel
):
    print("login to zabbix server %s" % server)
    zapi = ZabbixAPI(server + "/zabbix")
    login(zapi, username, password)
    hostid = getHostId(zapi, hostname, server)

    # find itemid using key
    print("key is: %s" % (key))
    items = getItems(zapi, key, hostid, hostname)
    item = items[0]

    # parameter validation
    inputParameters = {}
    inputParameters["history"] = item["value_type"]
    inputParameters["output"] = "extend"
    inputParameters["itemids"] = [item["itemid"]]

    assignTimeRange(inputParameters, datetime1, datetime2)

    # get history
    print("get history using this parameter")
    print(inputParameters)
    history = zapi.history.get(**inputParameters)

    # export to File
    output = generateOutputFilename(output, hostname, key)
    exportToCSV(history, key, output)


# Parsing Parameters
parser = argparse.ArgumentParser(
    description="Fetch history from aggregator and save it into CSV file"
)
parser.add_argument("-s", dest="server_IP", required=True, help="aggregator IP address")
parser.add_argument(
    "-n", dest="hostname", required=True, help="name of the monitored host"
)
parser.add_argument(
    "-u",
    dest="username",
    default="Admin",
    required=True,
    help="zabbix username, default Admin",
)
parser.add_argument(
    "-p", dest="password", default="zabbix", required=True, help="zabbix password"
)
parser.add_argument(
    "-k",
    dest="key",
    default="",
    required=True,
    help="zabbix item key, if not specified the script will fetch all keys for the specified hostname",
)
parser.add_argument(
    "-o", dest="output", default="", help="output file name, default hostname.csv"
)
parser.add_argument(
    "-t1",
    dest="datetime1",
    default="",
    help="begin date-time, use this pattern '2011-11-08 14:49:43' if only t1 specified then time period will be t1-now ",
)
parser.add_argument(
    "-t2",
    dest="datetime2",
    default="",
    help="end date-time, use this pattern '2011-11-08 14:49:43'",
)
parser.add_argument(
    "-v", dest="debuglevel", default=0, type=int, help="log level, default 0"
)
args = parser.parse_args()

# Calling fetching function
fetch_to_csv(
    args.username,
    args.password,
    args.server_IP,
    args.hostname,
    args.key,
    args.output,
    args.datetime1,
    args.datetime2,
    args.debuglevel,
)
