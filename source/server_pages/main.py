import hashlib
import threading
import time

from lib.common import static
from lib.logger import log
from lib.plugin import AfediumPluginBase
from lib.server_pages import register_page_provider, unregister_page_provider
from lib.stream_channel import register_stream_provider, unregister_stream_provider
from lib.support_lib import get_plugin_resource


class AFEDIUMPlugin(AfediumPluginBase):
    default_config = {
        "enabled": True,
    }

    def setup(self):
        if not self.config.conf.get("enabled", True):
            return False

        self._camera_sessions = {}
        self._camera_lock = threading.RLock()
        self._realtime_demo_sessions = {}
        self._realtime_demo_lock = threading.RLock()

        register_page_provider(
            self.id,
            self._build_pages(),
            provider_version=self.info.get("version", "0.1.0"),
            asset_loader=self._load_asset,
            open_handler=self._open_instance,
            invoke_handler=self._invoke,
            client_event_handler=self._handle_client_event,
            close_handler=self._close_instance,
        )
        register_stream_provider(
            self._camera_stream_provider_id,
            provider_version=self.info.get("version", "0.1.0"),
            open_handler=self._camera_open,
            message_handler=self._camera_message,
            close_handler=self._camera_close,
        )
        log.info(f"[{self.id}] 已注册服务端页面 demo provider")
        return True

    @property
    def _camera_stream_provider_id(self):
        return f"{self.id}.camera_stream"

    def main_loop(self):
        static["running"][self.id] = True
        self.stop_event.wait()

    def teardown(self):
        self._stop_all_realtime_demo_sessions()
        self._stop_all_camera_sessions()
        unregister_stream_provider(self._camera_stream_provider_id)
        unregister_page_provider(self.id)
        log.info(f"[{self.id}] 服务端页面 demo provider 已释放")

    def _load_asset(self, asset_id):
        asset_paths = {
            "web-demo/index.html": "assets/web-demo/index.html",
            "stream-demo/index.html": "assets/stream-demo/index.html",
            "camera-demo/index.html": "assets/camera-demo/index.html",
        }
        resource_path = asset_paths.get(asset_id)
        if resource_path is None:
            return None
        content = get_plugin_resource(self.id, resource_path, mode="rb")
        if content is None:
            return None
        return {
            "asset_id": asset_id,
            "encoding": "base64",
            "mime": "text/html; charset=utf-8",
            "bytes": content,
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    def _open_instance(self, context):
        state = {
            "opened_at": context["opened_at"],
            "page_id": context["page_id"],
        }
        if context["page_id"].endswith(".status"):
            state.update(self._declarative_state("页面已打开"))
        return state

    def _invoke(self, action, payload, context):
        if action == "refresh_status":
            return {
                "state_patch": self._declarative_state("服务端状态已刷新")
            }
        if action == "echo":
            return {"state_patch": {"echo": payload}}
        if action == "start_realtime_push":
            return self._start_realtime_demo(context, payload)
        if action == "stop_realtime_push":
            self._stop_realtime_demo(context["instance_id"])
            return {
                "state_patch": {
                    "server_push_running": False,
                    "message": "服务端主动推送已停止",
                    "server_push_stopped_at": time.time(),
                }
            }
        raise ValueError(f"未知页面动作: {action}")

    def _close_instance(self, context):
        self._stop_realtime_demo(context.get("instance_id"))

    def _handle_client_event(self, event, payload, context):
        if event == "ping":
            received_at = time.time()
            event_time = time.strftime("%H:%M:%S", time.localtime(received_at))
            return {
                "state_patch": {
                    "last_realtime_event": {
                        "event": event,
                        "payload": payload,
                        "received_at": received_at,
                    },
                    "last_event_summary": f"{event} @ {event_time}",
                    "recent_events": [
                        {
                            "title": "收到客户端实时事件",
                            "subtitle": f"payload={payload}",
                            "trailing": event_time,
                            "tone": "success",
                            "icon": "event",
                        },
                        {
                            "title": "状态补丁已回写",
                            "subtitle": "declarative 页面使用同一套状态合并逻辑刷新",
                            "trailing": "0x31",
                            "tone": "primary",
                            "icon": "sync",
                        },
                    ],
                    "message": "实时事件已收到",
                }
            }
        return {
            "state_patch": {
                "last_realtime_event": {
                    "event": event,
                    "payload": payload,
                    "received_at": time.time(),
                }
            }
        }

    def _declarative_state(self, message):
        now = time.time()
        running = static.get("running", {})
        running_plugins = sorted(
            plugin_id for plugin_id, is_running in running.items() if is_running
        )
        stopped_plugins = sorted(
            plugin_id for plugin_id, is_running in running.items() if not is_running
        )
        total_plugins = len(running)
        running_count = len(running_plugins)
        health_ratio = running_count / total_plugins if total_plugins else 1
        status_tone = "success" if not stopped_plugins else "warning"
        status_text = "正常" if not stopped_plugins else "有插件未运行"
        plugin_rows = [
            {
                "name": plugin_id,
                "status": "running" if is_running else "stopped",
                "tone": "success" if is_running else "warning",
                "role": "system" if plugin_id in {"server_pages", "stream_channel"} else "plugin",
            }
            for plugin_id, is_running in sorted(running.items())
        ]
        if not plugin_rows:
            plugin_rows = [
                {
                    "name": self.id,
                    "status": "demo",
                    "tone": "primary",
                    "role": "plugin",
                }
            ]
        recent_events = [
            {
                "title": message,
                "subtitle": "由 declarative 页面状态补丁更新",
                "trailing": time.strftime("%H:%M:%S", time.localtime(now)),
                "tone": status_tone,
                "icon": "event",
            },
            {
                "title": "页面实例可接收 0x31 实时事件",
                "subtitle": "点击发送实时事件后，状态会通过同一个实例回写",
                "trailing": "ready",
                "tone": "primary",
                "icon": "sync",
            },
        ]
        return {
            "last_refresh": now,
            "message": message,
            "health": {
                "status": status_text,
                "tone": status_tone,
                "ratio": round(health_ratio, 2),
                "running_plugins": running_count,
                "total_plugins": total_plugins,
                "stopped_plugins": len(stopped_plugins),
            },
            "status_items": [
                {
                    "label": "页面实例",
                    "value": "active",
                    "tone": "success",
                    "icon": "pages",
                },
                {
                    "label": "实时通道",
                    "value": "subscribed",
                    "tone": "success",
                    "icon": "sync",
                },
                {
                    "label": "服务端插件",
                    "value": status_text,
                    "tone": status_tone,
                    "icon": "plugin",
                },
            ],
            "plugin_rows": plugin_rows,
            "recent_events": recent_events,
            "last_event_summary": "尚未收到客户端实时事件",
        }

    def _camera_open(self, context):
        return {
            "mode": "camera_stream",
            "opened_at": context["opened_at"],
            "provider_id": context["provider_id"],
        }

    def _camera_message(self, event, payload, context):
        if event == "start":
            return self._start_camera_stream(context, payload)
        if event == "stop":
            self._stop_camera_session(context["session_id"])
            return {
                "event": event,
                "session_id": context["session_id"],
                "stopped": True,
            }
        return {
            "event": event,
            "session_id": context["session_id"],
            "accepted": False,
        }

    def _camera_close(self, context):
        self._stop_camera_session(context.get("session_id"))

    def _start_camera_stream(self, context, payload):
        session_id = context["session_id"]
        self._stop_camera_session(session_id)

        stop_event = threading.Event()
        config = {
            "camera_index": int(payload.get("camera_index", 0) or 0),
            "fps": max(1, min(30, int(payload.get("fps", 8) or 8))),
            "width": max(160, min(1920, int(payload.get("width", 640) or 640))),
            "height": max(120, min(1080, int(payload.get("height", 360) or 360))),
            "jpeg_quality": max(20, min(95, int(payload.get("jpeg_quality", 70) or 70))),
        }
        thread = threading.Thread(
            target=self._camera_stream_loop,
            name=f"{self.id}-camera-{session_id[:8]}",
            args=(context, config, stop_event),
            daemon=True,
        )
        with self._camera_lock:
            self._camera_sessions[session_id] = {
                "stop_event": stop_event,
                "thread": thread,
            }
        thread.start()
        return {
            "event": "start",
            "session_id": session_id,
            "accepted": True,
            "config": config,
        }

    def _camera_stream_loop(self, context, config, stop_event):
        session_id = context["session_id"]
        capture = None
        frame_count = 0
        started_at = time.time()
        last_stats_at = started_at

        try:
            try:
                import cv2
            except Exception as exc:
                context["send_event"](
                    "camera_error",
                    {
                        "message": "服务端缺少 OpenCV，无法打开摄像头",
                        "error": str(exc),
                        "hint": "安装 opencv-python 后重载插件",
                    },
                )
                return

            capture = cv2.VideoCapture(config["camera_index"])
            if not capture.isOpened():
                context["send_event"](
                    "camera_error",
                    {
                        "message": f"服务端摄像头不可用: index={config['camera_index']}",
                    },
                )
                return

            capture.set(cv2.CAP_PROP_FRAME_WIDTH, config["width"])
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config["height"])
            frame_delay = 1.0 / config["fps"]
            context["send_event"]("camera_started", {"config": config})

            while not stop_event.is_set():
                loop_started = time.time()
                ok, frame = capture.read()
                if not ok or frame is None:
                    context["send_event"](
                        "camera_error",
                        {"message": "服务端摄像头读取失败"},
                    )
                    break

                encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), config["jpeg_quality"]]
                encoded_ok, encoded = cv2.imencode(".jpg", frame, encode_params)
                if not encoded_ok:
                    context["send_event"](
                        "camera_error",
                        {"message": "服务端摄像头帧编码失败"},
                    )
                    break

                payload = encoded.tobytes()
                context["send_binary"](payload)
                frame_count += 1

                now = time.time()
                if now - last_stats_at >= 1.0:
                    elapsed = max(0.001, now - started_at)
                    context["send_event"](
                        "camera_stats",
                        {
                            "frames": frame_count,
                            "fps": round(frame_count / elapsed, 2),
                            "last_frame_bytes": len(payload),
                            "timestamp": now,
                        },
                    )
                    last_stats_at = now

                remaining = frame_delay - (time.time() - loop_started)
                if remaining > 0:
                    stop_event.wait(remaining)
        except Exception as exc:
            context["send_event"](
                "camera_error",
                {
                    "message": "服务端摄像头流异常",
                    "error": str(exc),
                },
            )
        finally:
            if capture is not None:
                capture.release()
            context["send_event"](
                "camera_stopped",
                {
                    "frames": frame_count,
                    "duration": round(time.time() - started_at, 3),
                },
            )
            with self._camera_lock:
                current = self._camera_sessions.get(session_id)
                if current and current.get("stop_event") is stop_event:
                    self._camera_sessions.pop(session_id, None)

    def _stop_camera_session(self, session_id):
        if not session_id:
            return
        with self._camera_lock:
            current = self._camera_sessions.pop(str(session_id), None)
        if current:
            current["stop_event"].set()

    def _stop_all_camera_sessions(self):
        with self._camera_lock:
            sessions = list(self._camera_sessions.values())
            self._camera_sessions.clear()
        for session in sessions:
            session["stop_event"].set()

    def _start_realtime_demo(self, context, payload):
        instance_id = context["instance_id"]
        self._stop_realtime_demo(instance_id)

        config = {
            "count": max(1, min(100, int(payload.get("count", 8) or 8))),
            "interval_ms": max(50, min(10000, int(payload.get("interval_ms", 1000) or 1000))),
            "message": str(payload.get("message") or "服务端主动推送"),
        }
        stop_event = threading.Event()
        thread = threading.Thread(
            target=self._realtime_demo_loop,
            name=f"{self.id}-push-{instance_id[:8]}",
            args=(context, config, stop_event),
            daemon=True,
        )
        with self._realtime_demo_lock:
            self._realtime_demo_sessions[instance_id] = {
                "stop_event": stop_event,
                "thread": thread,
            }
        thread.start()
        return {
            "state_patch": {
                "server_push_running": True,
                "server_push_config": config,
                "message": "服务端主动推送已启动",
                "server_push_started_at": time.time(),
            }
        }

    def _realtime_demo_loop(self, context, config, stop_event):
        instance_id = context["instance_id"]
        sent = 0
        started_at = time.time()
        try:
            if stop_event.wait(0.1):
                return
            for index in range(1, config["count"] + 1):
                if stop_event.is_set():
                    break
                now = time.time()
                payload = {
                    "message": config["message"],
                    "index": index,
                    "count": config["count"],
                    "sent_at": now,
                }
                context["emit"](
                    "server_push",
                    payload=payload,
                    state_patch={
                        "server_push_running": True,
                        "server_push_count": index,
                        "last_server_push": payload,
                        "message": f"{config['message']} {index}/{config['count']}",
                    },
                )
                sent = index
                if index < config["count"]:
                    stop_event.wait(config["interval_ms"] / 1000.0)
        except Exception as exc:
            log.warning(f"[{self.id}] 0x31 realtime push demo failed: {exc}")
            try:
                context["emit"](
                    "server_push_error",
                    payload={"message": str(exc), "sent": sent},
                    state_patch={
                        "server_push_running": False,
                        "message": "服务端主动推送异常",
                    },
                )
            except Exception:
                pass
        finally:
            with self._realtime_demo_lock:
                current = self._realtime_demo_sessions.get(instance_id)
                if current and current.get("stop_event") is stop_event:
                    self._realtime_demo_sessions.pop(instance_id, None)
            if not stop_event.is_set():
                try:
                    context["emit"](
                        "server_push_finished",
                        payload={
                            "sent": sent,
                            "duration": round(time.time() - started_at, 3),
                        },
                        state_patch={
                            "server_push_running": False,
                            "server_push_finished_at": time.time(),
                            "message": "服务端主动推送已完成",
                        },
                    )
                except Exception:
                    pass

    def _stop_realtime_demo(self, instance_id):
        if not instance_id:
            return
        with self._realtime_demo_lock:
            current = self._realtime_demo_sessions.pop(str(instance_id), None)
        if current:
            current["stop_event"].set()

    def _stop_all_realtime_demo_sessions(self):
        if not hasattr(self, "_realtime_demo_lock"):
            return
        with self._realtime_demo_lock:
            sessions = list(self._realtime_demo_sessions.values())
            self._realtime_demo_sessions.clear()
        for session in sessions:
            session["stop_event"].set()

    def _build_pages(self):
        declarative_page = {
            "schema_version": 1,
            "page_id": f"{self.id}.status",
            "title": "声明式状态面板",
            "render_mode": "declarative",
            "revision": "2",
            "permissions": ["server_pages.rpc", "server_pages.realtime"],
            "entry": {"type": "declarative"},
            "layout": {
                "type": "stack",
                "gap": 14,
                "blocks": [
                    {
                        "type": "text",
                        "variant": "headline",
                        "text": "声明式状态面板",
                    },
                    {
                        "type": "text",
                        "variant": "body",
                        "text": "这个页面不加载 WebView，由客户端按服务端声明的布局数据原生渲染。",
                    },
                    {
                        "type": "alert",
                        "tone": "info",
                        "icon": "info",
                        "title": "运行模式",
                        "binding": "message",
                    },
                    {
                        "type": "metric_grid",
                        "min_width": 142,
                        "metrics": [
                            {
                                "label": "运行插件",
                                "binding": "health.running_plugins",
                                "suffix": " 个",
                                "icon": "plugin",
                                "tone": "success",
                            },
                            {
                                "label": "总插件数",
                                "binding": "health.total_plugins",
                                "suffix": " 个",
                                "icon": "dashboard",
                                "tone": "primary",
                            },
                            {
                                "label": "异常插件",
                                "binding": "health.stopped_plugins",
                                "suffix": " 个",
                                "icon": "alert",
                                "tone": "warning",
                            },
                            {
                                "label": "页面状态",
                                "binding": "health.status",
                                "icon": "health",
                                "tone": "success",
                            },
                        ],
                    },
                    {
                        "type": "progress",
                        "label": "运行健康度",
                        "binding": "health.ratio",
                        "max": 1,
                        "format": "percent",
                        "tone": "success",
                    },
                    {
                        "type": "button_group",
                        "buttons": [
                            {
                                "label": "刷新状态",
                                "icon": "refresh",
                                "action": "refresh_status",
                                "variant": "primary",
                            },
                            {
                                "label": "发送实时事件",
                                "icon": "event",
                                "event": "ping",
                                "payload": {"source": "declarative"},
                                "variant": "secondary",
                            },
                        ],
                    },
                    {
                        "type": "section",
                        "title": "实例状态",
                        "subtitle": "这些行读取服务端状态补丁中的字段。",
                        "blocks": [
                            {
                                "type": "status_list",
                                "items_binding": "status_items",
                            },
                            {
                                "type": "text",
                                "variant": "caption",
                                "binding": "last_event_summary",
                            },
                        ],
                    },
                    {
                        "type": "table",
                        "title": "插件运行表",
                        "subtitle": "DataTable 区块，适合少量结构化状态。",
                        "rows_binding": "plugin_rows",
                        "columns": [
                            {"key": "name", "label": "插件"},
                            {"key": "role", "label": "类型"},
                            {"key": "status", "label": "状态", "type": "status"},
                        ],
                    },
                    {
                        "type": "list",
                        "title": "最近事件",
                        "items_binding": "recent_events",
                    },
                    {
                        "type": "divider",
                        "label": "调试数据",
                    },
                    {
                        "type": "json_view",
                        "title": "health",
                        "binding": "health",
                    },
                ],
            },
            "actions": {
                "refresh_status": {
                    "type": "rpc",
                    "method": "invoke",
                }
            },
        }
        web_page = {
            "schema_version": 1,
            "page_id": f"{self.id}.web_demo",
            "title": "Web 运行时示例",
            "render_mode": "web_runtime",
            "revision": "1",
            "permissions": ["server_pages.rpc", "server_pages.web_runtime", "server_pages.realtime"],
            "entry": {
                "type": "asset",
                "asset_id": "web-demo/index.html",
            },
            "assets": [
                {
                    "asset_id": "web-demo/index.html",
                    "mime": "text/html; charset=utf-8",
                }
            ],
            "bridge_permissions": ["invoke"],
            "csp": "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';",
        }
        stream_page = {
            "schema_version": 1,
            "page_id": f"{self.id}.stream_demo",
            "title": "实时推送测试",
            "render_mode": "web_runtime",
            "revision": "2",
            "permissions": [
                "server_pages.rpc",
                "server_pages.web_runtime",
                "server_pages.realtime",
            ],
            "entry": {
                "type": "asset",
                "asset_id": "stream-demo/index.html",
            },
            "assets": [
                {
                    "asset_id": "stream-demo/index.html",
                    "mime": "text/html; charset=utf-8",
                }
            ],
            "bridge_permissions": ["invoke"],
            "realtime": {
                "control_code": "0x31",
                "push_uid": "PUSH",
                "direction": "server_to_client",
            },
            "csp": "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';",
        }
        camera_page = {
            "schema_version": 1,
            "page_id": f"{self.id}.camera_demo",
            "title": "摄像头视频流",
            "render_mode": "web_runtime",
            "revision": "1",
            "permissions": [
                "server_pages.web_runtime",
                "stream_channel.control",
                "stream_channel.binary",
            ],
            "entry": {
                "type": "asset",
                "asset_id": "camera-demo/index.html",
            },
            "assets": [
                {
                    "asset_id": "camera-demo/index.html",
                    "mime": "text/html; charset=utf-8",
                }
            ],
            "bridge_permissions": ["stream"],
            "stream": {
                "provider_id": self._camera_stream_provider_id,
                "mode": "camera_jpeg",
                "control_code": "0x32",
                "direction": "server_to_client",
                "encoding": "image/jpeg",
            },
            "csp": "default-src 'none'; img-src blob: data:; style-src 'unsafe-inline'; script-src 'unsafe-inline';",
        }
        return [declarative_page, web_page, stream_page, camera_page]
