import json
import os
import evtx
from statistics import median_low

# TODO: comment your crap, christian



def initialize():
    EVTX_LOCATION = os.fspath(r"\\DCVM-WEB\c$\Windows\System32\winevt\Logs\Application.evtx")

    parser = evtx.PyEvtxParser(EVTX_LOCATION)
    records = parser.records_json()

    # Decode the event log from json strings to a dict, with complete disregard to the inefficiency of doing it this way
    record_list = []
    for record in records:
        record_json = json.loads(record['data'])
        try:
            if record_json['Event']['System']['Level'] <= 3:
                record_list.append(record_json['Event']['EventData']['Data']['#text'][0])
        except:
            pass

    record_dict = {}

    for item in record_list:
        if record_dict.__contains__(item):
            record_dict[item] += 1
        else:
            record_dict[item] = 1

    median = median_low(record_dict.values())

    high_errors = []
    for item in record_dict.items():
        if item[1] >= median:
            high_errors.append(item)

    return high_errors.sort(key=lambda x: x[1], reverse=True), median
