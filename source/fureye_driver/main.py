from lib.lib import *
import random


class AFEDIUMPlugin:
    default_config = {
        "Limit": [-0.05, 0.05],
        "Time": [0.5, 1]
    }

    def __init__(self, info, config):
        self.info = info
        self.config = config
        self.config_t = Config("fureye")
        self.id = info["id"]
        self.mdata = []
    
    def setup(self):
        return None

    def main_loop(self):
        while True:
            time.sleep(0.1)
            try:
                if static["running"]["fureye"]:
                    break
            except KeyError:
                pass
        for i in range(self.config_t.conf["num_display"]):
            self.mdata.append(dynamic["fureye"][i]["eyeball"])
            self.mdata[i]["enabled"] = True
        static["running"][self.id] = True
        try:
            while static["running"].get(self.id, False):
                x = random.uniform(self.config.conf["Limit"][0], self.config.conf["Limit"][1])
                y = random.uniform(self.config.conf["Limit"][0], self.config.conf["Limit"][1])
                schedule = time.time() + random.uniform(self.config.conf["Time"][0], self.config.conf["Time"][1])
                while time.time() <= schedule:
                    for i in range(self.config_t.conf["num_display"]):
                        self.mdata[i]["x"] += (x - self.mdata[i]["nx"]) / 20
                        self.mdata[i]["y"] += (y - self.mdata[i]["ny"]) / 20
                    time.sleep(0.01)
        finally:
            self.teardown()

    def teardown(self):
        print(f"模块 '{self.info.get('name')}' 已退出。")
