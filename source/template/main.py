# main.py
from lib.Event import Event
from lib.common import static, comm_lib
from lib.logger import log
from lib.plugin import AfediumPluginBase
from lib.support_lib import get_plugin_resource


class AFEDIUMPlugin(AfediumPluginBase):
    # 1. 【接口演示：默认配置】
    # 框架会自动合并这些配置到 config/<你的插件ID>.json，并提供 self.config 访问
    default_config = {
        "loop_interval": 5,
        "welcome_message": "这是V2架构演示插件"
    }

    def setup(self):
        # 2. 【接口演示：标准日志】
        log.info(f"[{self.id}] 正在执行 setup...")

        self.interval = self.config.conf.get("loop_interval", 5)

        # 3. 【接口演示：跨环境资源加载】
        # 自动在外部 plugin_data/ 目录和内部 .pyz 压缩包中寻找资源，mode='rb' 为读取二进制
        self.img_data = get_plugin_resource(self.id, 'src/img.png', mode='rb')
        if self.img_data:
            log.info(f"[{self.id}] 成功加载资源，大小: {len(self.img_data)} 字节")
        else:
            log.warning(f"[{self.id}] 警告: 未能加载资源 src/img.png")

        # 4. 【接口演示：指令注册】
        # 获取根指令对象，并挂载一个默认的缺省处理器
        cmd_demo = comm_lib.register("demo", self.command_default, "V2架构演示指令组")

        # 链式派生子指令，彻底告别 if/elif
        cmd_demo.subcommand("info", self.cmd_demo_info, "查看演示插件的详细运行信息")
        cmd_demo.subcommand("edit", self.cmd_demo_edit, "动态修改配置文件并落盘")

        # 5. 【接口演示：事件总线】
        static["event_handler"].register_event("ExternalIO_IN", self.on_message_received)

        return True  # 必须返回 True，框架才会启动 main_loop

    def main_loop(self):
        log.info(f"[{self.id}] 进入后台主循环。")
        static["running"][self.id] = True

        # 6. 【接口演示：协作式优雅退出】
        # 严禁使用 time.sleep()！使用 self.stop_event.wait(timeout) 可以随时被系统的关闭指令唤醒
        while not self.stop_event.is_set():
            # 这里写你的后台周期性任务
            pass

            self.stop_event.wait(timeout=self.interval)

    def teardown(self):
        # 7. 【接口演示：资源清理】
        # 在退出时务必注销指令和事件，防止内存泄漏和路由冲突
        comm_lib.unregister("demo")
        static["event_handler"].unregister_event("ExternalIO_IN", self.on_message_received)
        log.info(f"[{self.id}] 模块已安全释放并退出。")

    # ================= 业务方法演示 =================

    def command_default(self, ctx, args: list):
        """处理纯输入 'demo' 时的缺省逻辑"""
        msg = self.config.conf.get("welcome_message")
        ctx.reply(f"当前配置消息: {msg}")
        return "输入 'help' 查看所有可用指令树"

    def cmd_demo_info(self, ctx, args: list):
        """对应 'demo info'"""
        ctx.reply("这是一个指令上下文演示。")
        if ctx.client_id:
            ctx.reply(f"您的客户端连接对象是: {ctx.client_id.remote_address}")
        return "信息打印完毕"

    def cmd_demo_edit(self, ctx, args: list):
        """对应 'demo edit'"""
        # 8. 【接口演示：安全覆写配置】
        self.config.conf["welcome_message"] = "配置已被动态修改！"
        self.config.update()
        return "配置已成功更新"

    def on_message_received(self, event: Event):
        """
        当触发 ExternalIO_IN 事件时被调用
        """
        message = event.data.get("message")
        client = event.data.get("client_id")

        # 避免日志刷屏，仅在消息是文本且包含特定词时捕获
        if isinstance(message, str) and "测试" in message:
            log.info(f"[{self.id}] 侦听到了来自 {client.remote_address} 的测试消息！")
