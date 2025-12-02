import re
import time
import random
import subprocess
import uiautomator2 as ui2
from loguru import logger
from demo1 import DemoOne
from utils.errorProcess import raise_error

logger.add('../logs/log.log', encoding="utf-8", rotation="1 day", compression="zip")


class DemoTwo(DemoOne):
    """ 看广告得金币 """

    def __init__(self, android_device=None):
        try:
            self.con = ui2.connect(android_device) if android_device else ui2.connect()
            _ = self.con.info
            logger.info("✓ 设备连接成功，atx-agent 已就绪")
        except Exception as error:
            logger.info("atx-aget 可能未安装,正在安装。请打开手机开发者模式" +  str(error))
            try:
                cmd = ["python", "-m", "uiautomator2", "init"]
                if android_device:
                    cmd.extend(["--serial", android_device])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    logger.info("✓ atx-agent 安装完成")
                else:
                    logger.error(f"atx-agent 安装失败: {result.stderr}")
                    raise RuntimeError("atx-agent 安装失败")

                time.sleep(2)
                self.con = ui2.connect(android_device) if android_device else ui2.connect()
                logger.info("✓ 重新连接设备连接成功")
            except subprocess.TimeoutExpired:
                logger.error("安装 atx-agent 超时，请手动运行: python -m uiautomator2 init")
                raise
            except Exception as install_error:
                logger.error(f"安装失败: {install_error}")
                logger.info("请手动运行命令安装 atx-agent: python -m uiautomator2 init")
                raise

        logger.info("*" * 50)
        logger.info(f"当前设备信息 {self.con.info}")
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
        logger.info(f" 模拟看{video_type}视频{time_data}s ".center(20, "="))
        time.sleep(time_data)

        xpath_str = '//*[@resource-id="com.kuaishou.nebula.commercial_neo:id/video_countdown_end_icon"]'
        #x, y = (0.534, 0.084) if video_type == "视频" else (0.935, 0.07)
        x, y = (0.935, 0.07)
        if video_type == "视频":
            self.con.xpath(xpath_str).click()
        else:
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

    # @raise_error
    # def click_if_found(self, target_text, self_point=None):
    #
    #     """查找目标存在及点击并点击（支持自定义点击坐标）"""
    #
    #     self.find_target(target_text)
    #     if not self.point_list:
    #         return False
    #
    #     if self_point:
    #         self.con.click(*self_point)
    #     else:
    #         self.con.click(*self.point_list)
    #     logger.info(f" 当前界面中出现了 {target_text} ,已点击")
    #     time.sleep(random.uniform(1, 2))
    #     return True

    @raise_error
    def pre_function(self):
        """ 手机连接成功后的前期处理 """

        self.con.app_start("com.kuaishou.nebula", stop=True)
        time.sleep(random.uniform(1, 2))
        logger.info(f"当前应用信息 {self.con.app_current()}")
        logger.info("*" * 50)

        self.click_text("去赚钱")
        logger.info(" 点击去赚钱成功".center(20, "="))
        time.sleep(10)

        click_result = self.click_if_found("立即签到")
        if click_result:
            self.click_if_found("去看视频", [0.918, 0.185])

        time.sleep(random.uniform(1, 3))
        self.con.swipe(0.5, 0.8, 0.5, 0.6)  # 向下滑动一点点

        self.find_target("看广告得金币")
        self.con.click(*self.point_list)
        logger.info(f"点击了 看广告得金币 字段")
        # time.sleep(random.uniform(1, 5))

    def main_function(self):
        self.pre_function()

        while self.video_count > 0:
            try:
                if self.find_target("冷却中"):
                    return "广子状态是冷却中,稍后再试!!"

                try:
                    video_type = self.con.xpath(
                        '//*[@resource-id="com.kuaishou.nebula.live_audience_plugin:id/live_follow_text"]'
                    ).get_text()
                    video_type = "关注" if video_type == "关注" else "视频"
                except Exception as e:
                    video_type = "视频"

                logger.info(f"当前{250 - self.video_count + 1}, 已经看完一个视频,领取一次奖励☺ ".center(20, "="))
                watching_result = self.watch_signal_step_video(video_type)
                if not watching_result:
                    if video_type == "视频":
                        # 目前已知的是 限时金币暴涨、立即投币报名、看广告的金币(可能直接点叉之后回到了该界面了)
                        logger.error(f"点击叉进行试探时,出现了特殊情况")

                        self.click_if_found("限时金币暴涨")
                        self.click_if_found("立即投币报名", [0.067, 0.12])  # 点击瓜分金币

                        self.find_target("看广告得金币")  # 在重新查找 看广告得金币 先对限时金币暴涨进行点击
                        self.con.click(*self.point_list)
                        logger.warning(f"模拟时间到,点叉却返回了 '看广告得金币得界面'")
                        continue
                    else:
                        self.find_target("看广告得金币")  # 在重新查找 看广告得金币 先对限时金币暴涨进行点击
                        self.con.click(*self.point_list)
                        logger.warning(f"上一个直播点叉之后直接回 '看广告得金币得界面',模拟时间到,点叉却返回了 '看广告得金币得界面'")
                        continue

                match watching_result[0]:
                    case "继续观看":
                        self.con.click(*watching_result[1])
                    case "领取奖励":
                        self.video_count = self.video_count - 1
                        self.con.click(*watching_result[1])
                        time.sleep(random.uniform(1, 3))
                    case "领取额外金币":
                        self.video_count = self.video_count - 1
                        self.con.click(*watching_result[1])
                        time.sleep(random.uniform(1, 3))

                        self.find_target("看广告得金币")
                        self.con.click(*self.point_list)
                        logger.warning(f"出现了 '领取额外金币' 点击叉之后再一次点击看广告得金币 重新进入 🙂")
            except Exception as error:
                logger.error("这个视频出现了错误,我将重启APP应用重新进入APP 再执行任务" + str(error))
                # raise error
                self.main_function()
        return "success"


if __name__ == "__main__":
    demo_two = DemoTwo()
    final_result = demo_two.main_function()
    print(final_result)
