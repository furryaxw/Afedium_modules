import io
import os
from tkinter import *
from lib.lib import *
from PIL import Image, ImageTk

from lib.support_lib import get_plugin_resource

# 插件自己管理自己的UI元素
files: dict = {}
layer: list = []
d_window: list = []
canvas: list = []
screen_width = 0
screen_height = 0


class AFEDIUMPlugin:
    default_config = {
        "num_display": 1,
        "Layer": {"eyeball": 1},
        "addon": {}
    }

    def __init__(self, info, config):
        self.info = info
        self.config = config
        self.id = info["id"]
        self.tk_root = None  # 用于存储从core获取的Tk根实例

    def setup(self):
        dynamic[self.info["id"]] = []

    def main_loop(self):
        self.tk_root = static.get('tk_root')
        # 检查 tk_root 是否已成功获取
        if not self.tk_root:
            print(f"错误：插件 '{self.id}' 未能获取到Tkinter主实例，无法创建窗口。")
            return

        # 声明使用全局变量
        global files, layer, screen_width, screen_height, canvas

        # 遍历配置中指定的显示数量，创建对应的窗口和画布
        for d in range(self.config.conf["num_display"]):
            dynamic[self.id].insert(d, {})

            # 使用从 core 获取的 tk_root 来创建 Toplevel 窗口
            win = Toplevel(self.tk_root)
            d_window.insert(d, win)

            # 获取屏幕尺寸并设置窗口属性
            screen_width = win.winfo_screenwidth()
            screen_height = win.winfo_screenheight()
            win.overrideredirect(True)
            win.config(cursor="none")
            win.geometry(f'{screen_width}x{screen_height}+{screen_width * d}+0')

            # 创建画布
            cv = Canvas(win, width=screen_width * self.config.conf["num_display"], height=screen_height)
            canvas.insert(d, cv)

            # 根据操作系统设置窗口全屏状态
            if static["SYS_INFO"] == "Windows":
                win.state('zoom')
            else:
                win.state('normal')
                win.attributes("-fullscreen", True)

            # 放置画布
            cv.place(x=0, y=0, width=screen_width, height=screen_height)

        # 加载在配置中定义的图层资源
        for f in self.config.conf["Layer"].keys():
            self.load(f, self.config.conf["Layer"][f])

        # 加载在配置中定义的附加资源
        for f in self.config.conf["addon"].keys():
            for d in self.config.conf["addon"][f][1]:
                try:
                    self.load(f, self.config.conf["addon"][f][0], d, self.config.conf["addon"][f][2])
                except IndexError:
                    self.load(f, self.config.conf["addon"][f][0], d)

        static["running"][self.id] = True
        try:
            while static["running"].get(self.id, False):
                for d in range(self.config.conf["num_display"]):
                    for i in layer[d].keys():
                        if dynamic[self.info["id"]][d][i]["enabled"]:
                            x = int(dynamic[self.info["id"]][d][i]["x"] * screen_width / 2 + screen_width / 2 - files[i][
                                dynamic[self.info["id"]][d][i]["selected"]].width() / 2)
                            y = int(dynamic[self.info["id"]][d][i]["y"] * screen_height / 2 + screen_height / 2 - files[i][
                                dynamic[self.info["id"]][d][i]["selected"]].height() / 2)
                            dynamic[self.info["id"]][d][i]["nx"] = (int(
                                canvas[d].coords(layer[d][i][dynamic[self.info["id"]][d][i]["selected"]])[0]) - screen_width / 2 +
                                                           files[i][
                                                               dynamic[self.info["id"]][d][i][
                                                                   "selected"]].width() / 2) / screen_width * 2
                            dynamic[self.info["id"]][d][i]["ny"] = (int(
                                canvas[d].coords(layer[d][i][dynamic[self.info["id"]][d][i]["selected"]])[1]) - screen_height / 2 +
                                                           files[i][
                                                               dynamic[self.info["id"]][d][i][
                                                                   "selected"]].height() / 2) / screen_height * 2
                            if len(layer[d][i]) > 1:
                                for j in layer[d][i]:
                                    canvas[d].moveto(j, screen_width, screen_height)
                            canvas[d].moveto(layer[d][i][dynamic[self.info["id"]][d][i]["selected"]], x, y)
                        else:
                            for j in layer[d][i]:
                                canvas[d].moveto(j, screen_width, screen_height)
                    d_window[d].update()
                sleep(0.02)
        finally:
            self.teardown()

    def teardown(self):
        # 4. 【必须修改】插件在退出时，需要负责销毁自己创建的窗口
        for win in d_window:
            if win.winfo_exists():
                win.destroy()

        # 清理列表，防止重载时出错
        d_window.clear()
        canvas.clear()
        layer.clear()
        files.clear()

        print(f"模块 '{self.info.get('name')}' 已清理其所有窗口资源。")

    def load(self, name, size, on_display=-1, as_f=""):
        global files, layer

        content = None
        file_suffix = ""
        plugin_id = self.info["id"]

        # 创建一个尝试列表来模拟原始的 glob 搜索 (src/name, 然后是 src/name.*)
        # 这会依次尝试 name (可能自带后缀), name.png, name.jpg, name.gif
        potential_filenames = [name, f"{name}.png", f"{name}.jpg", f"{name}.jpeg", f"{name}.gif"]

        for filename in potential_filenames:
            # 约定资源都存放在 'src' 目录下
            resource_path = os.path.join('src', filename).replace('\\', '/')
            # 调用插件资源加载器
            _content = get_plugin_resource(plugin_id, resource_path, mode='rb')
            if _content:
                content = _content
                file_suffix = os.path.splitext(filename)[1].lower()
                break  # 找到后立即退出循环

        # 如果 content 依然是 None，说明所有尝试都失败了
        if content is None:
            print(f"File {name} not found")
            return -1

        f_name = name
        if as_f != "":
            name = as_f
        if on_display == -1:
            for d in range(self.config.conf["num_display"]):
                dynamic[self.info["id"]][d][name] = {}
                dynamic[self.info["id"]][d][name]["x"] = 0
                dynamic[self.info["id"]][d][name]["y"] = 0
                dynamic[self.info["id"]][d][name]["nx"] = 0
                dynamic[self.info["id"]][d][name]["ny"] = 0
                dynamic[self.info["id"]][d][name]["selected"] = 0
                dynamic[self.info["id"]][d][name]["enabled"] = False
        else:
            dynamic[self.info["id"]][on_display][name] = {}
            dynamic[self.info["id"]][on_display][name]["x"] = 0
            dynamic[self.info["id"]][on_display][name]["y"] = 0
            dynamic[self.info["id"]][on_display][name]["nx"] = 0
            dynamic[self.info["id"]][on_display][name]["ny"] = 0
            dynamic[self.info["id"]][on_display][name]["selected"] = 0
            dynamic[self.info["id"]][on_display][name]["enabled"] = False
        scale = int(float(size) * screen_height)
        try:
            if name in list(layer[on_display].keys()):
                for i in range(len(layer[on_display][name])):
                    if on_display == -1:
                        for d in range(self.config.conf["num_display"]):
                            canvas[d].delete(layer[d][name][i])
                    else:
                        canvas[on_display].delete(layer[on_display][name][i])
        except IndexError:
            pass

        if file_suffix == ".png" or file_suffix == ".jpg":
            files[f_name] = []
            if on_display == -1:
                for d in range(self.config.conf["num_display"]):
                    try:
                        layer[d][name] = []
                    except IndexError:
                        layer.insert(d, {})
                        layer[d][name] = []
            else:
                try:
                    layer[on_display][name] = []
                except IndexError:
                    layer.insert(on_display, {})
                    layer[on_display][name] = []

            img = Image.open(io.BytesIO(content))
            img = img.resize((int(img.size[0] * scale / img.size[1]), scale))
            files[f_name].insert(0, ImageTk.PhotoImage(img))
            if on_display == -1:
                for d in range(self.config.conf["num_display"]):
                    layer[d][name].insert(0, canvas[d].create_image(0, 0, image=files[f_name][0], anchor=NW))
                    canvas[d].moveto(layer[d][name][0], screen_width / 2 - files[f_name][0].width() / 2,
                                     screen_height / 2 - files[f_name][0].height() / 2)
            else:
                layer[on_display][name].insert(0,
                                               canvas[on_display].create_image(0, 0, image=files[f_name][0], anchor=NW))
                canvas[on_display].moveto(layer[on_display][name][0], screen_width / 2 - files[f_name][0].width() / 2,
                                          screen_height / 2 - files[f_name][0].height() / 2)
                return None
        elif file_suffix == ".gif":
            img = Image.open(io.BytesIO(content))
            files[f_name] = []
            if on_display == -1:
                for d in range(self.config.conf["num_display"]):
                    try:
                        layer[d][name] = []
                    except IndexError:
                        layer.insert(d, {})
                        layer[d][name] = []
            else:
                try:
                    layer[on_display][name] = []
                except IndexError:
                    layer.insert(on_display, {})
                    layer[on_display][name] = []
            for i in range(img.n_frames):
                img.seek(i)
                frame = img.resize((int(img.size[0] * scale / img.size[1]), scale))
                files[f_name].insert(i, ImageTk.PhotoImage(frame))
                if on_display == -1:
                    for d in range(self.config.conf["num_display"]):
                        layer[d][name].insert(i, canvas[d].create_image(0, 0, image=files[f_name][i], anchor=NW))
                        canvas[d].moveto(layer[d][name][i], screen_width / 2 - files[f_name][i].width() / 2,
                                         screen_height / 2 - files[f_name][i].height() / 2)
                else:
                    layer[on_display][name].insert(i, canvas[on_display].create_image(0, 0, image=files[f_name][i],
                                                                                      anchor=NW))
                    canvas[on_display].moveto(layer[on_display][name][i],
                                              screen_width / 2 - files[f_name][i].width() / 2,
                                              screen_height / 2 - files[f_name][i].height() / 2)
        else:
            print(f"Not supported file type: {file_suffix}")
            return None
