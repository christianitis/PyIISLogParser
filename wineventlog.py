import os
import evtx
import json

# TODO: comment your crap christian

EVTX_LOCATION = os.fspath(r"\\DCVM-WEB\c$\Windows\System32\winevt\Logs\Application.evtx")

class Event:
    def __init__(self, jsonstr: str):


def initialize():
    parser = evtx.PyEvtxParser(EVTX_LOCATION)
    records = parser.records_json()

    # Decode the event log from json strings to a dict, with complete disregard to the inefficiency of doing it this way
    record_list = []
    for record in records:
        record_list.append(json.loads(record['data']))



    for record in record_list:



