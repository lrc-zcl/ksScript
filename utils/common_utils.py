from loguru import logger
from errorProcess import raise_error


@raise_error
def judge_cha_by_xpath(con, xpath_str):
    """ 通过xpath 判断有没有叉 有的话就清除 """

    video_xpath = con.xpath(xpath_str)
    if not video_xpath:
        video_xpath.click()
        logger.warning(f"通过xpath 检测到了叉,已清除!!! ")
