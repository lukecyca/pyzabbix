"""
Desenvolvimento: WagPTech

Programa para incluir Item no Zabbix em um Host específico.

Sintaxe: python ZBXadditem.py host_name arquivo.csv

Entrar com login e senha do zabbix (necessário ser ADM)

Formato do arquivo:
key
item1
item2
...
"""

import csv
import getpass
import os
import sys

from pyzabbix import ZabbixAPI, ZabbixAPIException

host_name = sys.argv[1]
arquivo = sys.argv[2]
open(arquivo, newline="", encoding="utf-8")

# Zabbix server

zapi = ZabbixAPI("http://30.0.0.47/zabbix")

# Login com o Zabbix API

login = input("Insira seu login: ")
passwd = getpass.getpass("Digite sua senha: ")

zapi.login(login, passwd)

add = int(0)
nadd = int(0)

hosts = zapi.host.get(filter={"host": host_name}, selectInterfaces=["interfaceid"])
if hosts:
    host_id = hosts[0]["hostid"]
    print("host_name " + host_name + " @ host id {0}".format(host_id))
    with open(
        arquivo, newline="", encoding="utf-8"
    ) as csvfile:  # sys.argv[2]/'zbx_l15_k10.csv'
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # print ("Add Item: " + row['key'])
                item = zapi.item.create(
                    hostid=host_id,
                    name=row["key"],
                    key_=row["key"],
                    type=2,  # 0-Zabbix agent; 2-Zabbix trapper; 3-simple check; 5-Zabbix internal;
                    # 7-Zabbix agent (active); 8-Zabbix aggregate; 9-web item;
                    # 10-external check; 11-database monitor; 12-IPMI agent;
                    # 13-SSH agent; 14-TELNET agent; 15-calculated;
                    # 16-JMX agent; 17-SNMP trap; 18-Dependent item; 19-HTTP agent; 20-SNMP agent; 21-Script.
                    value_type=3,  # 0-numeric float; 1-character; 2-log; 3-numeric unsigned; 4-text.
                    interfaceid=hosts[0]["interfaces"][0]["interfaceid"],
                    delay=60,
                    status=1,  # 0-enabled item; 1-disabled item.
                )
                add = add + 1
                if add > 0:
                    print("Adicionados: " + str(add))
            except ZabbixAPIException as error:
                nadd = nadd + 1
                if nadd > 0:
                    print("Recusados: " + str(nadd))
                # print(error)
        if add > 0:
            print("Total de itens adicionados: " + str(add) + " itens.")
        if nadd > 0:
            print("Total de itens recusados: " + str(nadd) + " itens.")
        sys.exit()
else:
    print("No hosts found")
