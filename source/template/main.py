import time

from lib.config import Config
from lib.lib import static
# 导入我们刚刚创建的框架级资源加载器
from lib.support_lib import get_plugin_resource


class AFEDIUMPlugin:
    # 定义默认配置，其中包括外部资源目录的名称
    default_config = {
        "loop_interval": 5
    }

    def __init__(self, info, config):
        self.info = info
        self.config = config
        self.id = info["id"]
        self.img = None

    def setup(self):
        print(f"模块 '{self.info['name']}' 正在执行 setup...")
        # 在 setup 阶段加载资源
        # 插件只需要告诉框架“我是谁(self.id)”和“我需要什么('src/img.png')”
        self.img = get_plugin_resource(self.id, 'src/img.png')
        if self.img:
            print(f"[{self.info['name']}] 成功加载了资源，大小: {len(self.img)} 字节")
        else:
            print(f"[{self.info['name']}] 警告: 未能加载资源")

    def main_loop(self):
        static["running"][self.id] = True
        try:
            while static["running"].get(self.id, False):
                time.sleep(self.config.conf.get("loop_interval"))
        finally:
            self.teardown()

    def teardown(self):
        print(f"模块 '{self.info.get('name')}' 已退出。")
