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

from functools import partial
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

def console_handler(data, home):
    data = data['data']
    if 'liveMeasurement' in data:
        measurement = data['liveMeasurement']

        timestamp = measurement['timestamp']
        timeObj = parse(timestamp)
        hourMultiplier = timeObj.hour+1
        daysInMonth = calendar.monthrange(timeObj.year, timeObj.month)[1]
        adr = home.home_id

        output = [
        {
            "measurement": "pulse",
            "time": timestamp,
            "tags": {
                "address": adr
            },
            "fields": {
                "power": ifStringZero(measurement['power']),
                "minPower": ifStringZero(measurement['minPower']),
                "maxPower": ifStringZero(measurement['maxPower']),
                "averagePower": ifStringZero(measurement['averagePower']),
                "powerProduction": ifStringZero(measurement['powerProduction']),
                "powerReactive": ifStringZero(measurement['powerReactive']),
                "accumulatedConsumption": ifStringZero(measurement['accumulatedConsumption']),
                "accumulatedProduction": ifStringZero(measurement['accumulatedProduction']),
                "accumulatedConsumptionLastHour": ifStringZero(measurement['accumulatedConsumptionLastHour']),
                "accumulatedProductionLastHour": ifStringZero(measurement['accumulatedProductionLastHour']),
                "accumulatedCost": ifStringZero(measurement['accumulatedCost']),
                "accumulatedReward": ifStringZero(measurement['accumulatedReward']),
                "currency": ifStringZero(measurement['currency']),
                "voltagePhase1": ifStringZero(measurement['voltagePhase1']),
                "voltagePhase2": ifStringZero(measurement['voltagePhase2']),
                "voltagePhase3": ifStringZero(measurement['voltagePhase3']),
                "currentL1": ifStringZero(measurement['currentL1']),
                "currentL2": ifStringZero(measurement['currentL2']),
                "currentL3": ifStringZero(measurement['currentL3']),
                "powerFactor": ifStringZero(measurement['powerFactor']),
                "lastMeterConsumption": ifStringZero(measurement['lastMeterConsumption']),
                "lastMeterProduction": ifStringZero(measurement['lastMeterProduction']),
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
#        await home.update_info()
        await home.rt_subscribe(partial(console_handler, home=home))

    while True:
      await asyncio.sleep(10)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
