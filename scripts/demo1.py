import re
import time
import random
import uiautomator2
import uiautomator2 as ui2
from loguru import logger
from utils.errorProcess import raise_error
from utils.common_utils import judge_cha_by_xpath


class DemoOne():
    """ 看特定广子刷币 """

    def __init__(self, android_device=None):
        self.con = ui2.connect(android_device) if android_device else ui2.connect()
        logger.info("*" * 50)
        logger.info(f"当前设备信息 {self.con.info}")

    def has_target_content(self, target_sr):
        """  界面找出target_str """
        self.point_list = []

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
        if target_sr in text_list:
            indexs = [i for i, v in enumerate(text_list) if v == target_sr]
            target_location = location_xy[indexs[0]]
            point_xy = list(map(int, re.findall(r"\d+", target_location)))
            self.point_list = [point_xy[0] + (point_xy[2] - point_xy[0]) / 2,
                               point_xy[1] + (point_xy[3] - point_xy[1]) / 2]

        elif "领取额外金币" in text_list:
            self.point_list = [0.81, 0.376]

        return self.point_list

    def find_target(self, target_str):
        """  滑动找出界面内容 """

        count = 3  # 滑动 3次 找不到就退出
        while not self.has_target_content(target_str)[0]:
            self.con.swipe(0.5, 0.8, 0.5, 0.3)

            if count <= 0:
                raise Exception(f"滑动{count}次,没找到{target_str}字段按钮")
            count = count - 1

        logger.info(f" 找到了{target_str}字段 ".center(20, "="))
        return self.point_list

    @raise_error
    def click_xpath(self, xpath_str):
        """ 通过xpath点击 """

        video_xpath = self.con.xpath(xpath_str)
        if not video_xpath:
            video_xpath.click()
            logger.info(f"通过xpath点击{video_xpath.get_text()} 成功")

    @raise_error
    def click_text(self, target_text):
        """ 通过text点击 """

        self.con(text=target_text).click()

    @raise_error
    def watch(self):
        """ 模拟看视频 """

        time.sleep(random.uniform(1, 12))
        self.con.swipe(0.5, 0.8, 0.5, random.uniform(0.2, 0.5))  # 模拟人机滑动一次

        current_video_count = self.con.xpath(
            '//*[@resource-id="com.kuaishou.nebula.commercial_neo:id/award_shopping_count_text_view"]').get_text()
        current_index = current_video_count.split("/")[0]  # 初始的视频量
        all_index = current_video_count.split("/")[1]

        logger.info(f" 当前视频任务进度{current_index}/{all_index} ".center(10, "-"))

        try:
            current_video_user_name = self.con.xpath(
                '//*[@resource-id="com.kuaishou.nebula:id/user_name_text_view"]').get_text()
        except uiautomator2.exceptions.XPathElementNotFoundError:
            self.con.swipe(0.5, 0.8, 0.5, 0.2)
            current_video_user_name = "直播 User"

        logger.info(f" 当前视频用户为 {current_video_user_name} ".center(10, "="))
        if current_index == all_index:
            return True
        else:
            return False

    @raise_error
    def main_function(self):
        """ 主函数逻辑 """

        self.con.app_start("com.kuaishou.nebula", stop=True)
        time.sleep(1)
        logger.info(f"当前应用信息 {self.con.app_current()}")

        self.click_text("去赚钱")
        time.sleep(10)

        self.con.swipe(0.5, 0.8, 0.5, 0.6)
        self.find_target("刷广告看金币")
        self.con.click(*self.point_list)

        # 看视频界面偶尔会有叉
        xpath_str = "//android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.widget.ImageView[2]"
        judge_cha_by_xpath(self.con, xpath_str)

        while not self.watch():
            logger.info(f" 滑动一次视频,开始下一次")
        return "success"


if __name__ == "__main__":
    demo_one = DemoOne()
    final_result = demo_one.main_function()
    print(final_result)
