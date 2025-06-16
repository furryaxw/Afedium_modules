from lib.lib import *


default = {
    # 默认配置文件
    "default": None
}


class Info:
    name = "template"  # 模块名称
    version = "1.0.0"  # 模块版本
    url = ""  # 模块本体URL
    dependencies = []  # 对其他模块依赖
    pip_dependencies = []  # PIP库依赖
    linux_dependencies = []  # Linux包依赖


def __init__():
    config = Config("template", default)
    # 初始化

    static["running"][Info.name] = True  # 初始化完成，标注为已启动
    while static["running"][Info.name]:
        # 主循环

        time.sleep(1)

    # 终止
    return
