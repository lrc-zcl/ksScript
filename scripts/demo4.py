import re
import time
import random
import uiautomator2 as ui2
from loguru import logger
from demo1 import DemoOne
from utils.errorProcess import raise_error

logger.add('./logs/log.log', encoding="utf-8", rotation="1 day", compression="zip")


class DemoTwo(DemoOne):
    """ 看50次直播领金币 """

    def __init__(self, android_device=None):
        try:
            self.con = ui2.connect(android_device) if android_device else ui2.connect()
            _ = self.con.info
            logger.info("✓ 设备连接成功，atx-agent 已就绪")
        except Exception as e:
            logger.warning(f"✗ 连接失败或 atx-agent 未安装: {e}")
            logger.info("正在自动安装 atx-agent，请稍候...")

            from uiautomator2 import init
            device_serial = android_device if android_device else None
            init.Installer(device_serial).install()
            self.con = ui2.connect(android_device) if android_device else ui2.connect()
            logger.info("✓ atx-agent 安装完成，设备连接成功")

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
    def watch_signal_step_video(self):
        """观看单独视频"""
        xpath_str = '//*[@resource-id="com.kuaishou.nebula.live_audience_plugin:id/live_follow_text"]'
        time_data = random.uniform(3, 4)
        time.sleep(time_data)
        r = random.uniform(0.2, 0.5)
        self.con.click(0.249 + r, 0.482 + r)
        logger.info("点击了第一个位置的直播".center(20, "="))
        time.sleep(2)
        try:
            video_type = self.con.xpath(xpath_str).get_text()  # 关注按钮 标识
        except Exception as e:
            video_type = "视频"
        if video_type == "关注":
            result_list = []
            count = 6  # 因为已领取字段有时效性  所以只尝五次
            while True:
                if count < 0:
                    logger.warning(f" 模拟操作直播间6次,假设时常已到 ".center(20, "="))
                    return [0.935, 0.073]  # 超过5次 默认观看完成
                time_data = random.uniform(1, 10)
                time.sleep(time_data)
                logger.info(f"直播视频模拟观看{time_data}s")
                text_list, point_list = self.get_screen_content()

                if "已领取" in text_list:  # 待确定
                    result_list = [0.935, 0.073]
                    break
                else:
                    logger.info(f"直播领币时间还没到,再等一会儿")
                count = count - 1
            return result_list
        else:
            time_data = random.uniform(35, 40)
            time.sleep(time_data)
            logger.info(f"视频模拟观看{time_data}s")
            x = random.uniform(0, 0.2)
            y = random.uniform(0, 0.2)
            return [0.074 + x, 0.073 + y]

    def judge_and_get_text_by_xpath(self, xpath_str, text_str="领取奖励"):
        """ 在点击右上角的退出叉之前可能会出现 再看一个再领金币最高 """
        try:
            text_data = self.con.xpath(xpath_str).get_text()
            if text_str == text_data:
                self.con.click(0.822, 0.339)  # 清除掉
                logger.warning("点击右上角退出叉之前,清除了 '再看一个再领金币最高'!!!")
                return True
        except Exception as error:
            logger.error("点击右上角退出叉之前 出现问题" + str(error))
            return False

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

        self.find_target("看50次直播领金币")
        self.con.click(*self.point_list)
        logger.info(f"点击了 看50次直播领金币 字段")

    def main_function(self):
        self.pre_function()
        while self.video_count > 0:
            try:
                logger.info(f"当前{50 - self.video_count + 1},即将进入下一个直播！！！")
                watching_result = self.watch_signal_step_video()  # 直播结束
                if watching_result:
                    self.judge_and_get_text_by_xpath(
                        xpath_str='//*[@resource-id="com.kuaishou.nebula:id/again_dialog_ensure_text"]')  # 领取额外币
                    self.con.click(watching_result[0], watching_result[1])
                    # 也有可能是看完点之后才出现
                    time.sleep(random.uniform(1, 3))
                    logger.info(f"可能出现在点叉之后!!!")
                    self.judge_and_get_text_by_xpath(
                        xpath_str='//*[@resource-id="com.kuaishou.nebula:id/again_dialog_ensure_text"]')

                    time.sleep(random.uniform(1, 2))

                    try:
                        # 有可能叉之后直接退回了
                        guize_xpath = '//*[@resource-id="com.kuaishou.nebula:id/right_btn"]'
                        if self.judge_and_get_text_by_xpath(guize_xpath, "规则"):
                            self.con.swipe(0.5, 0.8, 0.5, 0.2)
                            self.video_count = self.video_count - 1
                            continue
                    except Exception as error:
                        self.con.click(0.935, 0.071)  # 右上角的叉
                        logger.info(f"奖励领取完成,即将退出直播间".center(20, "="))
                exit_1 = self.find_target("退出直播间")
                exit_2 = self.find_target('退出')
                if exit_1 or exit_2:
                    logger.info("点击右上角叉之后,出现了 退出、退出直播间, 此时进行点击")
                    try:
                        self.con.click(exit_1[0], exit_1[1])
                    except Exception as e:
                        self.con.click(exit_2[0], exit_2[1])
                    finally:
                        logger.info(f"点击了 退出、退出直播间")
                        # 做判断
                        try:
                            time.sleep(random.uniform(1, 2))
                            guize_xpath = '//*[@resource-id="com.kuaishou.nebula:id/right_btn"]'
                            if self.judge_and_get_text_by_xpath(guize_xpath, "规则"):
                                self.con.swipe(0.5, 0.8, 0.5, 0.2)
                                self.video_count = self.video_count - 1
                                continue
                        except Exception as error:
                            pass
                else:
                    raise Exception("特殊问题,重启应用")
            except Exception as error:
                logger.info("本次看直播遇到了特殊问题,重启应用" + str(error))
                self.main_function()
        return "success"


if __name__ == "__main__":
    demo_two = DemoTwo()
    final_result = demo_two.main_function()
    print(final_result)
