#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import ssl
import json
import _thread
import time
import datetime
import calendar
import os
import logging
import tibber.const
import asyncio
import aiohttp
import tibber

from influxdb import InfluxDBClient
from dateutil.parser import parse

def str_to_bool(v: str) -> bool:
    # Interpret string as bool
    return v.lower() in ("yes", "true", "t", "1")

print("tibberpulse-influxdb")

# settings from EnvionmentValue
influxhost=os.getenv('INFLUXDB_HOST', "localhost")
influxssl=str_to_bool(os.getenv('INFLUXDB_SSL', "False"))
influxverifyssl=str_to_bool(os.getenv('INFLUXDB_SSL_VERIFY', "False"))
influxport=os.getenv('INFLUXDB_PORT', 8086)
influxuser=os.getenv('INFLUXDB_USER', 'root')
influxpw=os.getenv('INFLUXDB_PW', 'root')
influxdb=os.getenv('INFLUXDB_DATABASE', 'tibberPulse')
tibbertoken=os.getenv('TIBBER_TOKEN', 'NOTOKEN')
tibberhomeid=os.getenv('TIBBER_HOMEID', 'NOID')
verbose = str_to_bool(os.getenv("VERBOSE", "False"))

global adr
adr = "DEFAULT"

influx_client = InfluxDBClient(host=influxhost, port=influxport, username=influxuser, password=influxpw, database=influxdb, ssl=influxssl, verify_ssl=influxverifyssl)

def ifStringZero(val):
    val = str(val).strip()
    if val.replace('.','',1).isdigit():
      res = float(val)
    else:
      res = None
    return res

def console_handler(data):
    data = data['data']
    if 'liveMeasurement' in data:
        measurement = data['liveMeasurement']
        timestamp = measurement['timestamp']
        timeObj = parse(timestamp)
        hourMultiplier = timeObj.hour+1
        daysInMonth = calendar.monthrange(timeObj.year, timeObj.month)[1]
        power = measurement['power']
        #min_power = measurement['minPower']
        #max_power = measurement['maxPower']
        #avg_power = measurement['averagePower']
        accumulated = measurement['accumulatedConsumption']
        accumulated_cost = measurement['accumulatedCost']
        #currency = measurement['currency']
        voltagePhase1 = measurement['voltagePhase1']
        voltagePhase2 = measurement['voltagePhase2']
        voltagePhase3 = measurement['voltagePhase3']
        currentL1 = measurement['currentL1']
        currentL2 = measurement['currentL2']
        currentL3 = measurement['currentL3']
        lastMeterConsumption = measurement['lastMeterConsumption']
        output = [
        {
            "measurement": "pulse",
            "time": timestamp,
            "tags": {
                "address": adr
            },
            "fields": {
                "power": ifStringZero(power),
                "consumption": ifStringZero(accumulated),
                "cost": ifStringZero(accumulated_cost),
                "voltagePhase1": ifStringZero(voltagePhase1),
                "voltagePhase2": ifStringZero(voltagePhase2),
                "voltagePhase3": ifStringZero(voltagePhase3),
                "currentL1": ifStringZero(currentL1),
                "currentL2": ifStringZero(currentL2),
                "currentL3": ifStringZero(currentL3),
                "lastMeterConsumption": ifStringZero(lastMeterConsumption),
                "hourmultiplier": hourMultiplier,
                "daysInMonth": daysInMonth
            }
        }
        ]
        if verbose:
           print(output)
        influx_client.write_points(output)
    else:
        print(data)

async def run():
    async with aiohttp.ClientSession() as session:
        tibber_connection = tibber.Tibber(tibbertoken, websession=session, user_agent="grafanalogger")
        await tibber_connection.update_info()

    homes = tibber_connection.get_homes()
    for home in homes:
        await home.rt_subscribe(console_handler)

    while True:
      await asyncio.sleep(10)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
