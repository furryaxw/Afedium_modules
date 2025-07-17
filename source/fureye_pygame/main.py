import io
import os
import pygame
from PIL import Image
from typing import Union
from lib.lib import *
from lib.support_lib import get_plugin_resource

files: dict = {}
layer: list = []
screen_width: int = 0
screen_height: int = 0

# Pygame 特有的全局对象
screen: Union[pygame.Surface, None] = None
clock: Union[pygame.time.Clock, None] = None


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

    def setup(self):
        dynamic[self.info["id"]] = []

    def main_loop(self):
        # 声明将要使用的全局变量
        global screen, screen_width, screen_height, clock, layer, files

        pygame.init()

        # 获取屏幕尺寸信息
        display_info = pygame.display.Info()
        screen_width = display_info.current_w
        screen_height = display_info.current_h

        num_display = self.config.conf["num_display"]
        total_width = screen_width * num_display

        # 创建一个横跨所有显示器的大窗口并赋值给全局变量
        screen = pygame.display.set_mode((total_width, screen_height), pygame.NOFRAME | pygame.FULLSCREEN)

        pygame.mouse.set_visible(False)
        clock = pygame.time.Clock()

        # 为每个虚拟显示器初始化动态数据和图层结构
        for d in range(num_display):
            dynamic[self.id].insert(d, {})
            layer.insert(d, {})

        # 加载资源
        for f in self.config.conf["Layer"].keys():
            self.load(f, self.config.conf["Layer"][f])

        for f in self.config.conf["addon"].keys():
            for d in self.config.conf["addon"][f][1]:
                try:
                    self.load(f, self.config.conf["addon"][f][0], d, self.config.conf["addon"][f][2])
                except IndexError:
                    self.load(f, self.config.conf["addon"][f][0], d)

        static["running"][self.id] = True
        try:
            while static["running"].get(self.id, False):
                # 1. 事件处理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        static["running"][self.id] = False

                # 2. 渲染准备 (清空屏幕)
                screen.fill((0, 0, 0))

                # 3. 更新和绘制所有元素
                for d in range(num_display):
                    if d >= len(dynamic[self.id]): continue

                    for layer_name in list(layer[d].keys()):
                        layer_data = dynamic[self.id][d].get(layer_name)

                        if layer_data and layer_data["enabled"]:
                            selected_frame = layer_data["selected"]

                            # 确保文件和帧已加载
                            if layer_name not in files or selected_frame >= len(files[layer_name]):
                                continue

                            image_surface = files[layer_name][selected_frame]
                            img_width, img_height = image_surface.get_size()

                            # 计算坐标
                            x = int(layer_data["x"] * screen_width / 2 + screen_width / 2 - img_width / 2)
                            y = int(layer_data["y"] * screen_height / 2 + screen_height / 2 - img_height / 2)

                            layer_data["nx"] = (x - screen_width / 2 + img_width / 2) / screen_width * 2
                            layer_data["ny"] = (y - screen_height / 2 + img_height / 2) / screen_height * 2

                            # 计算在整个大窗口上的实际绘制位置
                            blit_x = x + d * screen_width

                            screen.blit(image_surface, (blit_x, y))

                # 4. 更新显示
                pygame.display.flip()

                # 5. 控制帧率
                clock.tick(60)

        finally:
            self.teardown()

    def teardown(self):
        global files, layer, screen, clock

        pygame.quit()

        # 清理全局变量，与原版行为保持一致
        files.clear()
        layer.clear()
        screen = None
        clock = None

        print(f"模块 '{self.info.get('name')}' 已清理其所有 Pygame 资源。")

    def load(self, name, size, on_display=-1, as_f=""):
        global files, layer, screen_height

        content = None
        file_suffix = ""
        plugin_id = self.id

        potential_filenames = [name, f"{name}.png", f"{name}.jpg", f"{name}.jpeg", f"{name}.gif"]
        for filename in potential_filenames:
            resource_path = os.path.join('src', filename).replace('\\', '/')
            _content = get_plugin_resource(plugin_id, resource_path, mode='rb')
            if _content:
                content = _content
                file_suffix = os.path.splitext(filename)[1].lower()
                break

        if content is None:
            print(f"文件 {name} 未找到，已跳过加载。")
            return -1

        f_name = name
        layer_name = as_f if as_f else name

        displays_to_load = range(self.config.conf["num_display"]) if on_display == -1 else [on_display]
        for d in displays_to_load:
            if d < len(dynamic[self.id]):
                dynamic[self.id][d][layer_name] = {
                    "x": 0, "y": 0, "nx": 0, "ny": 0,
                    "selected": 0,
                    "enabled": False
                }

        scale_height = int(float(size) * screen_height)

        try:
            pil_img = Image.open(io.BytesIO(content))
        except Exception as e:
            print(f"使用 PIL 打开文件 {name} 失败: {e}")
            return None

        files[f_name] = []

        if file_suffix in [".png", ".jpg", ".jpeg"]:
            aspect_ratio = pil_img.size[0] / pil_img.size[1]
            scale_width = int(aspect_ratio * scale_height)
            resized_img = pil_img.resize((scale_width, scale_height), Image.LANCZOS)
            mode = resized_img.mode
            img_data = resized_img.tobytes()
            py_surface = pygame.image.fromstring(img_data, resized_img.size, mode).convert_alpha()
            files[f_name].append(py_surface)

        elif file_suffix == ".gif":
            for i in range(pil_img.n_frames):
                pil_img.seek(i)
                frame = pil_img.convert("RGBA")
                aspect_ratio = frame.size[0] / frame.size[1]
                scale_width = int(aspect_ratio * scale_height)
                resized_frame = frame.resize((scale_width, scale_height), Image.LANCZOS)
                frame_data = resized_frame.tobytes()
                py_surface = pygame.image.fromstring(frame_data, resized_frame.size, "RGBA")
                files[f_name].append(py_surface)
        else:
            print(f"不支持的文件类型: {file_suffix}")
            return None

        for d in displays_to_load:
            if d < len(layer):
                layer[d][layer_name] = True

        return None
