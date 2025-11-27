import re
import time
import random
import uiautomator2 as ui2
from loguru import logger
from demo1 import DemoOne
from utils.errorProcess import raise_error


class DemoTwo(DemoOne):
    """ 看广告得金币 """

    def __int__(self, android_device):
        self.con = ui2.connect(android_device) if android_device else ui2.connect()
        logger.info("*" * 50)
        logger.info(f"当前设备信息 {self.con.info}")
        self.video_count = 50

    def get_screen_content(self):
        """  返回界面内容 """
        point_list = []

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

        return text_list, point_list

    @raise_error
    def watch_signal_step_video(self):
        """观看单独视频"""

        time.sleep(random.uniform(1, 10))
        self.con.click(0.534, 0.084)  # 点击叉试探一下

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

    def main_function(self):
        self.con.app_start("com.kuaishou.nebula", stop=True)
        time.sleep(1)
        logger.info(f"当前应用信息 {self.con.app_current()}")

        self.click_text("去赚钱")
        time.sleep(10)

        if self.has_target_content("立即签到"):
            self.con(text="立即签到").click()
            logger.warning(f"看广告之前出现了 '立即签到',已清除")

            time.sleep(random.uniform(1, 3))
            if self.has_target_content("去看视频"):
                self.con.click(0.918, 0.185)
                logger.warning(f"点击立即签到之后出现了 '去看视频',已清除")

        time.sleep(random.uniform(1, 10))
        self.con.swipe(0.5, 0.8, 0.5, 0.6)  # 向下滑动一点点

        self.find_target("看广告得金币")
        self.con.click(*self.point_list)
        time.sleep(random.uniform(1, 5))

        while self.video_count > 0:
            watching_result = self.watch_signal_step_video()
            if not watching_result:
                logger.error(f"点击叉进行试探时,出现了特殊情况")
                raise Exception(f"在看视频的过程中,点叉试探时出现了特殊情况,请及时处理！！！")

            match watching_result[0]:
                case "继续观看":
                    self.con.click(watching_result[1][0], watching_result[1][1])
                case "领取奖励":
                    self.video_count = self.video_count - 1
                    self.con.click(watching_result[1][0], watching_result[1][1])
                    logger.info("已经看完一个视频,领取一次奖励☺".center(20, "="))
                    time.sleep(random.uniform(1, 3))
                case "领取额外金币":
                    self.video_count = self.video_count - 1
                    self.con.click(watching_result[1][0], watching_result[1][1])
                    time.sleep(random.uniform(1, 3))

                    self.find_target("看广告得金币")
                    self.con.click(self.point_list[0], self.point_list[1])
                    logger.warning(f"出现了 '领取额外金币' 点击叉之后再一次点击看广告得金币 重新进入 🙂")
        return "success"


if __name__ == "__main__":
    demo_two = DemoTwo()
    final_result = demo_two.main_function()
    print(final_result)
