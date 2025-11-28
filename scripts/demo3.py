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

    def detect_and_close_popups(self):
        """
        检测并关闭屏幕上的弹窗 - 增强版，能找到各种位置的小叉叉
        返回: True 表示检测到并关闭了弹窗, False 表示没有检测到弹窗
        """
        try:
            xml_data = self.con.dump_hierarchy()
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_data)
            
            screen_width = self.con.window_size()[0]
            screen_height = self.con.window_size()[1]
            
            # 常见的弹窗关闭关键词
            close_keywords = [
                "关闭", "跳过", "稍后", "我知道了", "取消", 
                "暂不", "以后再说", "残忍拒绝", "放弃奖励",
                "Close", "Skip", "Cancel", "Not Now", "close",
                "×", "x", "X", "✕", "✖"  # 各种叉号
            ]
            
            # 常见的广告弹窗关键词
            ad_keywords = [
                "立即下载", "查看详情", "立即领取", "打开",
                "去微信", "去下载", "点击下载", "立即安装"
            ]
            
            # 收集所有可能的关闭按钮
            close_button_candidates = []
            
            # ========== 方法1: 检测文本或描述包含关闭关键词的按钮 ==========
            for node in root.iter():
                text_val = node.attrib.get("text", "")
                content_desc = node.attrib.get("content-desc", "")
                resource_id = node.attrib.get("resource-id", "")
                class_name = node.attrib.get("class", "")
                bounds = node.attrib.get("bounds")
                
                if not bounds:
                    continue
                
                # 检查是否包含关闭关键词
                for keyword in close_keywords:
                    if keyword in text_val or keyword in content_desc or keyword.lower() in resource_id.lower():
                        point_xy = list(map(int, re.findall(r"\d+", bounds)))
                        center_x = (point_xy[0] + point_xy[2]) / 2
                        center_y = (point_xy[1] + point_xy[3]) / 2
                        rel_x = center_x / screen_width
                        rel_y = center_y / screen_height
                        
                        # 计算优先级（越靠近角落优先级越高）
                        corner_distance = min(
                            abs(rel_x - 0.95) + abs(rel_y - 0.05),  # 右上
                            abs(rel_x - 0.05) + abs(rel_y - 0.05),  # 左上
                            abs(rel_x - 0.95) + abs(rel_y - 0.95),  # 右下
                            abs(rel_x - 0.05) + abs(rel_y - 0.95)   # 左下
                        )
                        
                        close_button_candidates.append({
                            'x': rel_x,
                            'y': rel_y,
                            'priority': corner_distance,
                            'reason': f"关键词匹配: '{keyword}'"
                        })
            
            # ========== 方法2: 检测所有小尺寸的可点击ImageButton/ImageView ==========
            for node in root.iter():
                class_name = node.attrib.get("class", "")
                clickable = node.attrib.get("clickable", "false")
                bounds = node.attrib.get("bounds")
                
                if not bounds:
                    continue
                
                # ImageButton 和 ImageView 通常是关闭按钮
                if ("ImageButton" in class_name or "ImageView" in class_name) and clickable == "true":
                    point_xy = list(map(int, re.findall(r"\d+", bounds)))
                    width = point_xy[2] - point_xy[0]
                    height = point_xy[3] - point_xy[1]
                    
                    # 小按钮（通常是关闭按钮）
                    if 20 < width < 200 and 20 < height < 200:
                        center_x = (point_xy[0] + point_xy[2]) / 2
                        center_y = (point_xy[1] + point_xy[3]) / 2
                        rel_x = center_x / screen_width
                        rel_y = center_y / screen_height
                        
                        # 靠近屏幕边缘的小按钮更可能是关闭按钮
                        edge_distance = min(rel_x, 1 - rel_x, rel_y, 1 - rel_y)
                        
                        if edge_distance < 0.15:  # 距离边缘15%以内
                            close_button_candidates.append({
                                'x': rel_x,
                                'y': rel_y,
                                'priority': edge_distance,
                                'reason': f"小型图片按钮 ({width}x{height}px) 靠近边缘"
                            })
            
            # ========== 方法3: 扫描屏幕四个角落和边缘的小按钮 ==========
            # 定义更多的角落和边缘位置
            edge_scan_positions = [
                # 上边缘
                (0.05, 0.05), (0.10, 0.05), (0.15, 0.05),
                (0.50, 0.05),  # 正上方
                (0.85, 0.05), (0.90, 0.05), (0.95, 0.05),
                
                # 下边缘
                (0.05, 0.95), (0.50, 0.95), (0.95, 0.95),
                
                # 左右边缘
                (0.05, 0.10), (0.05, 0.50), (0.05, 0.90),
                (0.95, 0.10), (0.95, 0.50), (0.95, 0.90),
                
                # 弹窗常见位置（中间偏上/偏下的角落）
                (0.85, 0.25), (0.15, 0.25),  # 弹窗右上、左上
                (0.85, 0.75), (0.15, 0.75),  # 弹窗右下、左下
            ]
            
            for node in root.iter():
                clickable = node.attrib.get("clickable", "false")
                bounds = node.attrib.get("bounds")
                
                if clickable == "true" and bounds:
                    point_xy = list(map(int, re.findall(r"\d+", bounds)))
                    width = point_xy[2] - point_xy[0]
                    height = point_xy[3] - point_xy[1]
                    
                    # 只关注小按钮
                    if 20 < width < 180 and 20 < height < 180:
                        center_x = (point_xy[0] + point_xy[2]) / 2
                        center_y = (point_xy[1] + point_xy[3]) / 2
                        rel_x = center_x / screen_width
                        rel_y = center_y / screen_height
                        
                        # 检查是否在扫描位置附近
                        for scan_x, scan_y in edge_scan_positions:
                            distance = ((rel_x - scan_x) ** 2 + (rel_y - scan_y) ** 2) ** 0.5
                            if distance < 0.08:  # 8%范围内
                                close_button_candidates.append({
                                    'x': rel_x,
                                    'y': rel_y,
                                    'priority': distance,
                                    'reason': f"边缘小按钮 ({width}x{height}px)"
                                })
                                break
            
            # ========== 方法4: 检测是否有广告弹窗，如果有就更激进地查找关闭按钮 ==========
            ad_detected = False
            for node in root.iter():
                text_val = node.attrib.get("text", "")
                for ad_keyword in ad_keywords:
                    if ad_keyword in text_val:
                        ad_detected = True
                        logger.warning(f"⚠️ 检测到广告关键词: '{ad_keyword}'")
                        break
                if ad_detected:
                    break
            
            # ========== 按优先级排序并尝试点击 ==========
            if close_button_candidates:
                # 去重（相近的位置只保留一个）
                unique_candidates = []
                for candidate in close_button_candidates:
                    is_duplicate = False
                    for existing in unique_candidates:
                        distance = ((candidate['x'] - existing['x']) ** 2 + 
                                  (candidate['y'] - existing['y']) ** 2) ** 0.5
                        if distance < 0.03:  # 3%范围内认为是重复
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        unique_candidates.append(candidate)
                
                # 按优先级排序
                unique_candidates.sort(key=lambda x: x['priority'])
                
                logger.warning(f"🔍 找到 {len(unique_candidates)} 个可能的关闭按钮")
                
                # 尝试点击优先级最高的几个
                max_attempts = min(3, len(unique_candidates))
                for i in range(max_attempts):
                    candidate = unique_candidates[i]
                    logger.warning(f"🎯 尝试点击第 {i+1} 个候选: {candidate['reason']} "
                                 f"位置 ({candidate['x']:.3f}, {candidate['y']:.3f})")
                    self.con.click(candidate['x'], candidate['y'])
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    # 点击后再次检测，如果弹窗消失了就返回
                    return True
            
            # 如果检测到广告但没找到明确的关闭按钮，盲点常见位置
            if ad_detected and not close_button_candidates:
                logger.warning("⚠️ 检测到广告但未找到明确关闭按钮，尝试盲点常见位置")
                blind_positions = [(0.95, 0.05), (0.90, 0.08), (0.05, 0.05), (0.85, 0.10)]
                for pos_x, pos_y in blind_positions:
                    self.con.click(pos_x, pos_y)
                    time.sleep(random.uniform(0.3, 0.6))
                return True
            
            return len(close_button_candidates) > 0
            
        except Exception as e:
            logger.error(f"检测弹窗时出错: {str(e)}")
            return False
    
    def safe_click_with_popup_check(self, x, y, check_before=True, check_after=True):
        """
        安全点击：在点击前后检测并关闭弹窗
        x, y: 点击坐标（相对坐标0-1或绝对坐标）
        check_before: 点击前是否检测弹窗
        check_after: 点击后是否检测弹窗
        """
        if check_before:
            logger.info("点击前检测弹窗...")
            max_attempts = 3
            for i in range(max_attempts):
                if self.detect_and_close_popups():
                    logger.info(f"第{i+1}次检测：发现并关闭了弹窗")
                    time.sleep(random.uniform(0.5, 1))
                else:
                    logger.info("没有检测到弹窗，继续执行")
                    break
        
        # 执行点击
        self.con.click(x, y)
        logger.info(f"已点击位置 ({x:.3f}, {y:.3f})")
        
        if check_after:
            time.sleep(random.uniform(0.5, 1))
            logger.info("点击后检测弹窗...")
            if self.detect_and_close_popups():
                logger.info("点击后发现并关闭了弹窗")
                time.sleep(random.uniform(0.5, 1))

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

        # 启动后检测弹窗
        logger.info("=" * 60)
        logger.info("🔍 第1次弹窗检测：应用启动后")
        self.detect_and_close_popups()
        time.sleep(1)

        self.click_text("去赚钱")
        time.sleep(10)
        
        # 点击"去赚钱"后检测弹窗
        logger.info("=" * 60)
        logger.info("🔍 第2次弹窗检测：点击'去赚钱'后")
        self.detect_and_close_popups()

        if self.has_target_content("立即签到"):
            self.con(text="立即签到").click()
            logger.warning(f"看广告之前出现了 '立即签到',已清除")

            time.sleep(random.uniform(1, 3))
            if self.has_target_content("去看视频"):
                self.con.click(0.918, 0.185)
                logger.warning(f"点击立即签到之后出现了 '去看视频',已清除")

        time.sleep(random.uniform(1, 10))
        
        # 滑动前检测弹窗
        logger.info("=" * 60)
        logger.info("🔍 第3次弹窗检测：准备滑动前")
        self.detect_and_close_popups()
        
        self.con.swipe(0.5, 0.8, 0.5, 0.6)  # 向下滑动一点点

        self.find_target("看广告得金币")
        
        # 点击"看广告得金币"前检测弹窗
        logger.info("=" * 60)
        logger.info("🔍 第4次弹窗检测：准备点击'看广告得金币'前")
        self.detect_and_close_popups()
        
        self.con.click(*self.point_list)
        time.sleep(random.uniform(1, 5))

        while self.video_count > 0:
            # 每次看视频前都检测弹窗
            logger.info("=" * 60)
            logger.info(f"🔍 看视频循环中弹窗检测 (剩余 {self.video_count} 个视频)")
            popup_detected = self.detect_and_close_popups()
            if popup_detected:
                time.sleep(random.uniform(1, 2))
                # 如果关闭了弹窗，可能需要重新进入看广告页面
                if not self.has_target_content("继续观看") and not self.has_target_content("领取奖励"):
                    logger.warning("关闭弹窗后，尝试重新进入看广告页面")
                    self.find_target("看广告得金币")
                    self.con.click(*self.point_list)
                    time.sleep(random.uniform(2, 4))
            
            watching_result = self.watch_signal_step_video()
            if not watching_result:
                logger.error(f"点击叉进行试探时,出现了特殊情况")
                # 尝试检测并关闭弹窗
                logger.warning("尝试检测是否有意外弹窗...")
                if self.detect_and_close_popups():
                    logger.info("已关闭意外弹窗，继续执行")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"在看视频的过程中,点叉试探时出现了特殊情况,请及时处理！！！")

            match watching_result[0]:
                case "继续观看":
                    self.con.click(watching_result[1][0], watching_result[1][1])
                case "领取奖励":
                    self.video_count = self.video_count - 1
                    self.con.click(watching_result[1][0], watching_result[1][1])
                    logger.info("已经看完一个视频,领取一次奖励☺".center(20, "="))
                    time.sleep(random.uniform(1, 3))
                    
                    # 领取奖励后检测弹窗
                    self.detect_and_close_popups()
                    
                case "领取额外金币":
                    self.video_count = self.video_count - 1
                    self.con.click(watching_result[1][0], watching_result[1][1])
                    time.sleep(random.uniform(1, 3))
                    
                    # 领取额外金币后检测弹窗
                    self.detect_and_close_popups()

                    self.find_target("看广告得金币")
                    self.con.click(self.point_list[0], self.point_list[1])
                    logger.warning(f"出现了 '领取额外金币' 点击叉之后再一次点击看广告得金币 重新进入 🙂")
        
        logger.info("=" * 60)
        logger.info("🎉 所有视频观看完成！")
        return "success"


if __name__ == "__main__":
    demo_two = DemoTwo()
    final_result = demo_two.main_function()
    print(final_result)