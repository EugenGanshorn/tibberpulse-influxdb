#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio
import calendar
import os
from functools import partial

import aiohttp
import tibber
import tibber.const
import urllib3
from dateutil.parser import parse
from influxdb import InfluxDBClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def str_to_bool(v: str) -> bool:
    # Interpret string as bool
    return v.lower() in ("yes", "true", "t", "1")


print("TibberPulse-InfluxDB")

# settings from EnvironmentValue
influxhost = os.getenv('INFLUXDB_HOST', "localhost")
influxssl = str_to_bool(os.getenv('INFLUXDB_SSL', "False"))
influxverifyssl = str_to_bool(os.getenv('INFLUXDB_SSL_VERIFY', "False"))
influxport = os.getenv('INFLUXDB_PORT', 8086)
influxuser = os.getenv('INFLUXDB_USER', "root")
influxpw = os.getenv('INFLUXDB_PW', "root")
influxdb = os.getenv('INFLUXDB_DATABASE', "tibberPulse")
tibbertoken = os.getenv('TIBBER_TOKEN', "NO-TOKEN")
tibberhomeid = os.getenv('TIBBER_HOMEID', "NO-ID")
verbose = str_to_bool(os.getenv("VERBOSE", "False"))

influx_client = InfluxDBClient(host=influxhost, port=influxport, username=influxuser, password=influxpw,
                               database=influxdb, ssl=influxssl, verify_ssl=influxverifyssl)


def if_string_zero(val):
    val = str(val).strip()
    if val.replace('.', '', 1).isdigit():
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
        hourMultiplier = timeObj.hour + 1
        daysInMonth = calendar.monthrange(timeObj.year, timeObj.month)[1]

        output = [
            {
                "measurement": "pulse",
                "time": timestamp,
                "tags": {
                    "address": home.home_id
                },
                "fields": {
                    "power": if_string_zero(measurement['power']),
                    "minPower": if_string_zero(measurement['minPower']),
                    "maxPower": if_string_zero(measurement['maxPower']),
                    "averagePower": if_string_zero(measurement['averagePower']),
                    "powerProduction": if_string_zero(measurement['powerProduction']),
                    "powerReactive": if_string_zero(measurement['powerReactive']),
                    "accumulatedConsumption": if_string_zero(measurement['accumulatedConsumption']),
                    "accumulatedProduction": if_string_zero(measurement['accumulatedProduction']),
                    "accumulatedConsumptionLastHour": if_string_zero(measurement['accumulatedConsumptionLastHour']),
                    "accumulatedProductionLastHour": if_string_zero(measurement['accumulatedProductionLastHour']),
                    "accumulatedCost": if_string_zero(measurement['accumulatedCost']),
                    "accumulatedReward": if_string_zero(measurement['accumulatedReward']),
                    "currency": if_string_zero(measurement['currency']),
                    "voltagePhase1": if_string_zero(measurement['voltagePhase1']),
                    "voltagePhase2": if_string_zero(measurement['voltagePhase2']),
                    "voltagePhase3": if_string_zero(measurement['voltagePhase3']),
                    "currentL1": if_string_zero(measurement['currentL1']),
                    "currentL2": if_string_zero(measurement['currentL2']),
                    "currentL3": if_string_zero(measurement['currentL3']),
                    "powerFactor": if_string_zero(measurement['powerFactor']),
                    "lastMeterConsumption": if_string_zero(measurement['lastMeterConsumption']),
                    "lastMeterProduction": if_string_zero(measurement['lastMeterProduction']),
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
        tibber_connection = tibber.Tibber(tibbertoken, websession=session, user_agent="GrafanaLogger")
        await tibber_connection.update_info()

    homes = tibber_connection.get_homes()
    for home in homes:
        # await home.update_info()
        await home.rt_subscribe(partial(console_handler, home=home))

    while True:
        await asyncio.sleep(10)


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(run())
finally:
    influx_client.close()
    loop.close()
