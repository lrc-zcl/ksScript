"""
多设备运行示例 - 简化版
"""

from demo2 import DemoTwo
from utils.device_manager import DeviceManager


if __name__ == "__main__":
    # 创建设备管理器（指定使用 DemoTwo 类）
    manager = DeviceManager(DemoTwo)
    
    # 添加设备 - 只需要传设备序列号
    manager.add_device("127.0.0.1:5555")
    manager.add_device("127.0.0.1:5556")
    manager.add_device("192.168.1.100:5555")
    
    # 动态添加设备（运行过程中也可以添加）
    # manager.add_device("127.0.0.1:5557")
    
    # 等待所有设备完成
    manager.wait_all_complete()
    
    # 查看状态
    manager.print_status()

