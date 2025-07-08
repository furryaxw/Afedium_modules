from lib.lib import *
import random

default = {
    "Limit": [-0.05, 0.05],
    "Time": [0.5, 1]
}


Info = {
    "name": "fureye_driver",
    "id": "fureye_driver",
    "version": "1.0.0",
    "author": "Axw",
    "type": "module",
    "dependencies": ["fureye"],
    "pip_dependencies": [],
    "linux_dependencies": []
}


def __init__():
    config = Config("display_pos", default)
    config_t = Config("display")

    while True:
        time.sleep(0.1)
        try:
            if static["running"]["fureyev1"]:
                break
        except KeyError:
            pass
    mdata = []
    for i in range(config_t.conf["num_display"]):
        mdata.append(dynamic["eyes"][i]["eyeball"])
        mdata[i]["enabled"] = True
    static["running"][Info["id"]] = True
    while static["running"][Info["id"]]:
        x = random.uniform(config.conf["Limit"][0], config.conf["Limit"][1])
        y = random.uniform(config.conf["Limit"][0], config.conf["Limit"][1])
        schedule = time.time() + random.uniform(config.conf["Time"][0], config.conf["Time"][1])
        while time.time() <= schedule:
            for i in range(config_t.conf["num_display"]):
                mdata[i]["x"] += (x - mdata[i]["nx"]) / 20
                mdata[i]["y"] += (y - mdata[i]["ny"]) / 20
            time.sleep(0.01)
    return
