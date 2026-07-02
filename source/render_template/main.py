import os

from lib.common import comm_lib, static
from lib.plugin import AfediumPluginBase
from lib.scene_builder import Scene


class AFEDIUMPlugin(AfediumPluginBase):
    default_config = {}

    def setup(self):
        # 获取当前物理路径
        self.plugin_path = os.path.dirname(os.path.abspath(__file__))

        # 模块加载的第一件事：先清空之前可能残留的图层！
        display = static.get("display")
        if display:
            display.send_cmd({"cmd": "clear_layer", "layer_name": "hardcore_3d_layer"})

        cmd = comm_lib.register("test3d", description="高级渲染管线测试")
        cmd.subcommand("hard", self.start_render, "注入底层着色器与3D模型")
        cmd.subcommand("simple", self.start_simple, "测试 JSON 驱动管线")

        return True

    def main_loop(self):
        static["running"][self.id] = True
        self.stop_event.wait()

    def teardown(self):
        # 模块被卸载或热重载时：通知 GPU 销毁我们创建的所有画面！
        display = static.get("display")
        if display:
            display.send_cmd({"cmd": "clear_layer", "layer_name": "hardcore_3d_layer"})
        comm_lib.unregister("test3d")

    def start_render(self, ctx, args):
        display = static.get("display")
        if not display: return "错误：显示驱动未就绪"

        script_path = os.path.join(self.plugin_path, "view.py")
        # 重新挂载
        display.send_cmd({
            "cmd": "load_advanced",
            "layer_name": "hardcore_3d_layer",
            "z_index": 50,
            "script_path": script_path,
            "class_name": "TestShaderView"
        })
        return "主进程指令下达：已注入高级 Shader 脚本！"

    def start_simple(self, ctx, args):
        display = static.get("display")
        if not display: return "错误：显示驱动未就绪"

        # 1. 实例化场景，传入 plugin_id 以便底层挂载 VFS 资源
        scene = Scene("test_simple_scene", self.id)

        # 2. 添加一张 2D 贴图 (测试正交矩阵与基础图像解析)
        scene.add_image("assets/test.png", x=100, y=100, scale=1.0)

        # 3. 添加 3D 模型 (测试透视矩阵与模型解析)
        scene.add_model("assets/test.obj", x=0, y=0, z=-500, scale=1.0)

        # 4. 发送 JSON 指令
        scene.show()
        return "主进程指令下达：已发送 Scene JSON 数据！"
