"""
线程池资源管理
"""

import time
from demo2 import DemoTwo
from utils.device_manager import DeviceManager
from loguru import logger


if __name__ == "__main__":

    manager = DeviceManager(DemoTwo, max_workers=5)
    manager.add_device("127.0.0.1:5555")
    manager.add_device("127.0.0.1:5556")
    manager.add_device("192.168.1.100:5555")
    
    # 动态添加更多设备（运行过程中也可以添加）
    # manager.add_device("127.0.0.1:5557")
    # manager.add_device("127.0.0.1:5558")

    logger.info("\n📊 线程池状态监控：")
    for i in range(5):
        time.sleep(3)
        status = manager.get_pool_status()
        logger.info(f"  [{i+1}] 运行中:{status['running']} | "
                   f"已完成:{status['completed']} | "
                   f"队列中:{status['queue_size']} | "
                   f"总数:{status['total']}")

    logger.info("\n⏳ 等待所有设备任务完成...\n")
    manager.wait_all_complete()

    manager.print_status()

    manager.stop()
    
    logger.success("\n✅ 所有任务已完成！")

