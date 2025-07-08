from lib.lib import *


default = {
    # 默认配置文件
    "default": None
}


Info = {
    "name": "模板",  # 模块名称
    "id": "template",  # 模块ID
    "version": "1.0.0",  # 模块版本
    "author": "Axw",  # 模块作者
    "url": "template/module_template.py",  # 模块URL
    "description": "AFEDIUM模块示例模板",  # 模块简介
    "type": "module",  # 模块类型
    "dependencies": [],  # 对其他模块依赖
    "pip_dependencies": [],  # PIP库依赖
    "linux_dependencies": []  # Linux包依赖
}


def __init__():
    config = Config("template", default)
    # 初始化

    static["running"][Info["id"]] = True  # 初始化完成，标注为已启动
    while static["running"][Info["id"]]:
        # 主循环

        time.sleep(1)

    # 终止
    return
