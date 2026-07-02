import math
import os
import random

import pyglet
from pyglet.gl import *
from pyglet.math import Mat4, Vec3

# 极简的 Shader，自己掌控矩阵
vertex_source = """#version 330 core
in vec3 position;
in vec2 tex_coords;
out vec2 v_tex_coords;
uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;
void main() {
    gl_Position = projection * view * model * vec4(position, 1.0);
    v_tex_coords = tex_coords;
}
"""

fragment_source = """#version 330 core
in vec2 v_tex_coords;
out vec4 final_color;
uniform sampler2D our_texture;
uniform float time;
void main() {
    vec4 tex_color = texture(our_texture, v_tex_coords);
    float pulse = 0.5 + 0.5 * sin(time * 3.0);
    final_color = vec4(tex_color.rgb * vec3(1.0, pulse, pulse), tex_color.a);
}
"""

part_vertex_source = """#version 330 core
in vec3 position;
in vec4 color;
out vec4 v_color;
uniform mat4 projection;
uniform mat4 view;
void main() {
    gl_Position = projection * view * vec4(position, 1.0);
    v_color = color;
}
"""
part_fragment_source = """#version 330 core
in vec4 v_color;
out vec4 final_color;
void main() {
    final_color = v_color; // 纯色加 Alpha 通道
}
"""


class TestShaderView:
    def on_mount(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(self.base_dir, "assets")
        if assets_dir not in pyglet.resource.path:
            pyglet.resource.path.append(assets_dir)
            pyglet.resource.reindex()

        self.time = 0.0

        self.model_batch = pyglet.graphics.Batch()
        self.quad_batch = pyglet.graphics.Batch()

        # --- 准备 TRS 方块与模型 ---
        try:
            self.shader = pyglet.graphics.shader.ShaderProgram(
                pyglet.graphics.shader.Shader(vertex_source, "vertex"),
                pyglet.graphics.shader.Shader(fragment_source, "fragment")
            )
            self.texture = pyglet.resource.image("test.png").get_texture()
            # 三角形拼成的 2D 方块顶点 (物理放大 50 倍)
            self.vertex_list = self.shader.vertex_list(
                6, GL_TRIANGLES,
                position=('f', [-50, -50, 0, 50, -50, 0, 50, 50, 0, -50, -50, 0, 50, 50, 0, -50, 50, 0]),
                tex_coords=('f', [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1])
            )
            # 加载庞大的 3D 模型
            self.model = pyglet.resource.model("test.obj", batch=self.model_batch)
        except Exception as e:
            print(f"[ShaderView] 资源加载失败: {e}")

        # --- 初始化硬核粒子系统 ---
        self.num_particles = 1000
        self.part_phases = []  # 给每个粒子一个独立的闪烁相位
        part_positions = []
        part_colors = []

        # 编译粒子着色器
        try:
            self.part_shader = pyglet.graphics.shader.ShaderProgram(
                pyglet.graphics.shader.Shader(part_vertex_source, "vertex"),
                pyglet.graphics.shader.Shader(part_fragment_source, "fragment")
            )
            # 在 CPU 层面预先算出 1000 个随机顶点数据
            for _ in range(self.num_particles):
                part_positions.extend([random.uniform(-400, 400), random.uniform(-400, 400), random.uniform(-1000, 0)])
                part_colors.extend([1.0, 0.0, 0.0, 1.0])
                self.part_phases.append(random.uniform(0.0, math.pi * 2))

            # 创建最纯粹的点(POINTS)类型的顶点列表，我们在 CPU 阶段预先算出 1000 个随机位置和颜色。
            self.part_list = self.part_shader.vertex_list(
                self.num_particles, GL_POINTS,
                position=('f', part_positions),
                color=('f', part_colors)
            )
            glPointSize(4.0)
        except Exception as e:
            print(f"[ShaderView] 粒子加载失败: {e}")
            self.part_list = None

    def update(self, dt):
        self.time += dt

        # --- 高性能粒子位置更新算法 ---
        if getattr(self, 'part_list', None):
            pos = list(self.part_list.position)
            col = list(self.part_list.color)

            for i in range(self.num_particles):
                idx3 = i * 3
                idx4 = i * 4

                # 粒子向摄像机(Z轴正方向)和上方(Y轴正方向)运动
                pos[idx3 + 1] += dt * 60.0
                pos[idx3 + 2] += dt * 250.0

                # 修复 math.sin
                col[idx4 + 3] = 0.5 + 0.5 * math.sin(self.time * 5.0 + self.part_phases[i])

                # 越界重置机制
                if pos[idx3 + 2] > 100:
                    pos[idx3] = random.uniform(-400, 400)
                    pos[idx3 + 1] = random.uniform(-400, 400)
                    pos[idx3 + 2] = random.uniform(-1000, -800)

            # 写回 GPU 显存
            self.part_list.position = pos
            self.part_list.color = col

    def on_draw(self, window):
        glEnable(GL_DEPTH_TEST)
        window.projection = Mat4.perspective_projection(window.aspect_ratio, z_near=0.1, z_far=2000, fov=45)

        # 1. 绘制庞大的 3D 模型
        if getattr(self, 'model', None):
            try:
                # 【诊断修复】：应对重心偏离的 test.obj
                # 如果你的模型在软件里没有居中，单纯的 from_rotation 就会造成公转。
                # 临时解法：在你的模型中寻找一个反向补偿偏移 (需手动调整)，然后再自转，最后推到世界坐标系。
                # 为了不让代码变复杂，这里提供标准的原地自转 TRS：
                model_mat = Mat4.from_translation(Vec3(-100, 0, -500)) @ Mat4.from_rotation(self.time, Vec3(0, 1, 0))
                self.model.matrix = model_mat
                self.model_batch.draw()
            except Exception as e:
                pass

        # 2. 绘制带动态 Shader 的测试方块
        if getattr(self, 'shader', None) and getattr(self, 'texture', None) and getattr(self, 'vertex_list', None):
            try:
                # 只给它位移，绝对不给它自转了！
                quad_mat = Mat4.from_translation(Vec3(100, 0, -500))

                self.shader.bind()
                self.shader["projection"] = window.projection
                self.shader["view"] = window.view
                self.shader["model"] = quad_mat
                self.shader["time"] = self.time

                glActiveTexture(GL_TEXTURE0)
                glBindTexture(self.texture.target, self.texture.id)

                self.vertex_list.draw(GL_TRIANGLES)

                glBindTexture(self.texture.target, 0)
                self.shader.unbind()
            except Exception as e:
                pass

        # 3. 绘制硬核粒子系统
        if getattr(self, 'part_list', None) and getattr(self, 'part_shader', None):
            try:
                self.part_shader.bind()
                self.part_shader["projection"] = window.projection
                self.part_shader["view"] = window.view

                # 开启混合（实现透明粒子效果）
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

                self.part_list.draw(GL_POINTS)

                glDisable(GL_BLEND)
                self.part_shader.unbind()
            except Exception as e:
                pass

        glDisable(GL_DEPTH_TEST)

    def on_destroy(self):
        # 生命周期闭环：模块关闭或重载时，清理掉我们留下的资源
        print("[ShaderView] 接到销毁指令，正在释放 GPU 资源...")
        if getattr(self, 'vertex_list', None): self.vertex_list.delete()
        if getattr(self, 'part_list', None): self.part_list.delete()
