from secrets import token_hex
from time import sleep
from typing import Tuple

import pytest

from pyzabbix.api import ZabbixAPI
from pyzabbix.sender import ZabbixMetric, ZabbixSender

HOST = "Zabbix server"
ITEM_NAME = "PyZabbix"


@pytest.fixture(name="trapper_item")
def setup_trapper_item(zapi: ZabbixAPI):
    item_key = f"pyzabbix.test{token_hex(4)}"

    host_id = zapi.host.get(filter={"host": [HOST]})[0]["hostid"]
    items = zapi.item.get(hostids=host_id, search={"key_": item_key})
    if items:
        item_id = items[0]["itemid"]
    else:
        item_id = zapi.item.create(
            hostid=host_id,
            name=ITEM_NAME,
            key_=item_key,
            type=2,
            value_type=3,
        )["itemids"][0]

    # Wait for new item to be fully set
    sleep(2)

    yield item_id, item_key

    # Cleanup testing item
    zapi.item.delete(item_id)


def test_sending_metrics(zapi: ZabbixAPI, trapper_item: Tuple[str, str]) -> None:
    item_id, item_key = trapper_item

    metrics = [
        ZabbixMetric(host=HOST, key=item_key, clock=1659038600, ns=704032939, value=1),
        ZabbixMetric(host=HOST, key=item_key, clock=1659038611, ns=704038405, value=2),
        ZabbixMetric(host=HOST, key=item_key, clock=1659038622, ns=704042624, value=3),
        ZabbixMetric(host=HOST, key=item_key, clock=1659038633, ns=822621787, value=4),
        ZabbixMetric(host=HOST, key=item_key, clock=1659038644, ns=822627425, value=5),
        ZabbixMetric(host=HOST, key=item_key, clock=1659038655, ns=822631996, value=6),
        ZabbixMetric(host=HOST, key=item_key, clock=1659038666, ns=453824511, value=7),
        ZabbixMetric(host=HOST, key=item_key, clock=1659038677, ns=453830345, value=8),
    ]

    sender = ZabbixSender()
    response = sender.send(metrics)
    assert response.processed == 8
    assert response.failed == 0
    assert response.total == 8
    assert response.batch_count == 1

    # Wait for new data to be ingested
    sleep(2)

    history = zapi.history.get(
        itemids=item_id,
        sortfield="clock",
        sortorder="ASC",
        limit=10,
    )
    assert len(history) == len(metrics)
    assert history == list(
        map(
            lambda m: {
                "itemid": item_id,
                "clock": str(m.clock),
                "ns": str(m.ns),
                "value": str(m.value),
            },
            metrics,
        )
    )
