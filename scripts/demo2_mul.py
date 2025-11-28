import re
import time
import random
import threading
import uiautomator2 as ui2
from loguru import logger
from demo1 import DemoOne
from utils.errorProcess import raise_error
from utils.device_manager import DeviceManager

logger.add('../logs/log.log', encoding="utf-8", rotation="1 day", compression="zip")


class DemoTwo(DemoOne):
    """ 看广告得金币 """

    def __init__(self, android_device):
        self.android_device = android_device

        try:
            self.con = ui2.connect(android_device)
            _ = self.con.info
            logger.info(f"[{self.android_device}] ✓ 设备连接成功，atx-agent 已就绪")
        except Exception as e:
            logger.warning(f"[{self.android_device}] ✗ 连接失败或 atx-agent 未安装: {e}")
            logger.info(f"[{self.android_device}] 正在自动安装 atx-agent，请稍候...")

            from uiautomator2 import init
            init.Installer(android_device).install()
            self.con = ui2.connect(android_device)
            logger.info(f"[{self.android_device}] ✓ atx-agent 安装完成，设备连接成功")

        logger.info("*" * 50)
        logger.info(f"[{self.android_device}] 当前设备信息 {self.con.info}")
        self.video_count = 50

    def get_screen_content(self):
        """  返回界面内容 """
        time.sleep(random.uniform(1, 2))

        xml_data = self.con.dump_hierarchy()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)

        text_list = []
        location_xy = []
        for node in root.iter():
            text_val = node.attrib.get("text")
            if text_val:
                text_list.append(text_val)
                target_location = node.attrib.get("bounds")
                location_xy.append(target_location)

        return text_list, location_xy

    @raise_error
    def watch_signal_step_video(self, video_type):
        """ 观看单独视频 或直播视频"""
        time_data = random.uniform(1, 10)
        logger.info(f"[{self.android_device}] 模拟看{video_type}视频{time_data}s ".center(30, "="))
        time.sleep(time_data)

        x, y = (0.534, 0.084) if video_type == "视频" else (0.935, 0.07)
        self.con.click(x, y)
        text_list, point_list = self.get_screen_content()

        targets = {
            "继续观看": None,
            "领取奖励": None,
            "领取额外金币": [0.81, 0.376]
        }

        for target_text, fixed_point in targets.items():
            if target_text in text_list:
                if fixed_point:
                    return target_text, fixed_point
                indexs = [i for i, v in enumerate(text_list) if v == target_text]
                target_location = point_list[indexs[0]]
                point_xy = list(map(int, re.findall(r"\d+", target_location)))
                center_point = [
                    point_xy[0] + (point_xy[2] - point_xy[0]) / 2,
                    point_xy[1] + (point_xy[3] - point_xy[1]) / 2
                ]
                return target_text, center_point

        return None

    @raise_error
    def click_if_found(self, target_text, self_point=None):

        """查找目标存在及点击并点击（支持自定义点击坐标）"""

        self.find_target(target_text)
        if not self.point_list:
            return False

        if self_point:
            self.con.click(*self_point)
        else:
            self.con.click(*self.point_list)
        logger.info(f"[{self.android_device}] 当前界面中出现了 {target_text} ,已点击")
        time.sleep(random.uniform(1, 2))
        return True

    @raise_error
    def pre_function(self):
        """ 手机连接成功后的前期处理 """

        self.con.app_start("com.kuaishou.nebula", stop=True)
        time.sleep(random.uniform(1, 2))
        logger.info(f"[{self.android_device}] 当前应用信息 {self.con.app_current()}")
        logger.info("*" * 50)

        self.click_text("去赚钱")
        logger.info(f"[{self.android_device}] 点击去赚钱成功".center(30, "="))
        time.sleep(10)

        click_result = self.click_if_found("立即签到")
        if click_result:
            self.click_if_found("去看视频", [0.918, 0.185])

        time.sleep(random.uniform(1, 3))
        self.con.swipe(0.5, 0.8, 0.5, 0.6)  # 向下滑动一点点

        self.find_target("看广告得金币")
        self.con.click(*self.point_list)
        # time.sleep(random.uniform(1, 5))

    def main_function(self):
        self.pre_function()
        while self.video_count > 0:
            try:
                try:
                    video_type = self.con.xpath(
                        '//*[@resource-id="com.kuaishou.nebula.live_audience_plugin:id/live_follow_text"]'
                    ).get_text()
                    video_type = "关注" if video_type == "关注" else "视频"
                except Exception:
                    video_type = "视频"

                watching_result = self.watch_signal_step_video(video_type)
                if not watching_result:
                    if video_type == "视频":
                        # 目前已知的是 限时金币暴涨、立即投币报名、看广告的金币(可能直接点叉之后回到了该界面了)
                        logger.error(f"[{self.android_device}] 点击叉进行试探时,出现了特殊情况")

                        self.click_if_found("限时金币暴涨")
                        self.click_if_found("立即投币报名", [0.067, 0.12])  # 点击瓜分金币

                        self.find_target("看广告得金币")  # 在重新查找 看广告得金币 先对限时金币暴涨进行点击
                        self.con.click(*self.point_list)
                        logger.warning(f"[{self.android_device}] 模拟时间到,点叉却返回了 '看广告得金币得界面'")
                        continue
                    else:
                        self.find_target("看广告得金币")  # 在重新查找 看广告得金币 先对限时金币暴涨进行点击
                        self.con.click(*self.point_list)
                        logger.warning(f"[{self.android_device}] 上一个直播点叉之后直接回 '看广告得金币得界面',模拟时间到,点叉却返回了 '看广告得金币得界面'")
                        continue

                match watching_result[0]:
                    case "继续观看":
                        self.con.click(*watching_result[1])
                    case "领取奖励":
                        self.video_count = self.video_count - 1
                        self.con.click(*watching_result[1])
                        logger.info(
                            f"[{self.android_device}] 当前{50 - self.video_count + 1}, 已经看完一个视频,领取一次奖励☺ ".center(40, "="))
                        time.sleep(random.uniform(1, 3))
                    case "领取额外金币":
                        self.video_count = self.video_count - 1
                        self.con.click(*watching_result[1])
                        time.sleep(random.uniform(1, 3))

                        self.find_target("看广告得金币")
                        self.con.click(*self.point_list)
                        logger.warning(f"[{self.android_device}] 出现了 '领取额外金币' 点击叉之后再一次点击看广告得金币 重新进入 🙂")
            except Exception as error:
                logger.error(f"[{self.android_device}] 这个视频出现了错误,我将重启APP应用重新进入APP 再执行任务" + str(error))
                self.main_function()
        return "success"


def run_single_device(device_serial):
    """单设备运行模式（保留原有功能）"""
    demo_two = DemoTwo(android_device=device_serial)
    final_result = demo_two.main_function()
    print(final_result)


def run_multi_devices():
    """多设备运行模式示例"""
    # 创建设备管理器
    manager = DeviceManager()

    # 添加设备 - 直接使用设备序列号
    # manager.add_device(device_serial="127.0.0.1:5555", device_class=DemoTwo)
    # manager.add_device(device_serial="127.0.0.1:5556", device_class=DemoTwo)
    # manager.add_device(device_serial="192.168.1.100:5555", device_class=DemoTwo)

    # 如果只有一个设备，直接传入序列号
    # manager.add_device(device_serial="你的设备序列号", device_class=DemoTwo)

    # 等待3秒后动态添加更多设备（模拟运行中添加设备）
    def add_devices_later():
        """模拟在运行过程中动态添加设备"""
        time.sleep(3)
        logger.info("\n" + "=" * 60)
        logger.info("演示：动态添加新设备（不影响已运行的设备）")
        logger.info("=" * 60)

        # 这里可以添加更多设备
        # manager.add_device(device_serial="127.0.0.1:5557", device_class=DemoTwo)
        # manager.add_device(device_serial="192.168.1.100:5555", device_class=DemoTwo)

    # 在后台线程中添加设备
    add_thread = threading.Thread(target=add_devices_later, daemon=True)
    add_thread.start()

    # 打印状态（每30秒一次）
    def print_status_periodically():
        while True:
            time.sleep(30)
            manager.print_status()

    status_thread = threading.Thread(target=print_status_periodically, daemon=True)
    status_thread.start()

    # 等待所有设备任务完成
    manager.wait_all_complete()


if __name__ == "__main__":

    device_count = input("请输入要添加的设备数量: ").strip()
    manager = DeviceManager()

    if device_count and device_count.isdigit() and int(device_count) > 0:
        for i in range(int(device_count)):
            serial = input(f"请输入第{i + 1}个设备的序列号: ").strip()
            if serial:
                manager.add_device(
                    device_serial=serial,
                    device_class=DemoTwo
                )
            else:
                print(f"跳过第{i + 1}个设备（未输入序列号）")

    if manager.get_total_count() == 0:
        print("错误：至少需要添加一个设备")
    else:
        def status_monitor():
            while True:
                time.sleep(30)
                manager.print_status()


        status_thread = threading.Thread(target=status_monitor, daemon=True)
        status_thread.start()
        manager.wait_all_complete()  # 等待所有线程任务执行完成
