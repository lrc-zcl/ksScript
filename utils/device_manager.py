import time
import threading
from queue import Queue
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger


class DeviceManager:
    """多设备管理器 - 支持多设备并发运行和动态添加设备"""
    
    def __init__(self, device_class, max_workers=None):
        """
        初始化设备管理器
        :param device_class: 设备类（如 DemoTwo）
        :param max_workers: 线程池最大工作线程数，None表示使用默认值（CPU核心数*5）
        """
        self.device_class = device_class  # 设备类
        self.devices = {}  # 存储设备信息 {device_id: {"future": future, "instance": instance, "status": status}}
        self.device_queue = Queue()  # 用于动态添加设备的队列
        self.lock = threading.Lock()  # 线程锁，确保线程安全
        self.running = True  # 控制管理器运行状态
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 启动设备监听线程
        self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
        self.monitor_thread.start()
        logger.info(f"✓ 设备管理器已启动，支持动态添加设备（线程池大小: {max_workers or '默认'}）")
    
    def add_device(self, device_id, **kwargs):
        """ 添加设备到管理器 """

        if device_id is None:
            logger.error("添加设备失败：必须提供 device_id 参数")
            return False

        self.device_queue.put((device_id, kwargs))
        logger.info(f"✓ 设备 {device_id} 已加入队列，等待启动")
        return True
    
    def _monitor_devices(self):
        """监听设备队列并启动新设备"""
        while self.running:
            try:
                if not self.device_queue.empty():
                    device_id, kwargs = self.device_queue.get(timeout=1)
                    self._start_device(device_id, kwargs)
                else:
                    time.sleep(1)
            except Exception as e:
                logger.error(f"设备监听线程错误: {e}")
                time.sleep(1)
    
    def _start_device(self, device_id, kwargs):
        """启动单个设备的任务"""
        # 检查设备是否已存在
        with self.lock:
            if device_id in self.devices:
                logger.warning(f"设备 {device_id} 已存在，跳过添加")
                return
        
        try:
            logger.info(f"{'=' * 30}")
            logger.info(f"正在启动设备: {device_id}")
            logger.info(f"{'=' * 30}")
            
            # 创建设备实例
            demo_instance = self.device_class(android_device=device_id, **kwargs)
            
            # 使用线程池提交任务
            future = self.executor.submit(self._run_device_task, demo_instance, device_id)
            
            # 保存设备信息
            with self.lock:
                self.devices[device_id] = {
                    "future": future,
                    "instance": demo_instance,
                    "status": "running",
                    "start_time": datetime.now()
                }
            
            logger.info(f"✓ 设备 {device_id} 启动成功")
            
        except Exception as e:
            logger.error(f"✗ 启动设备 {device_id} 失败: {e}")
            # 记录错误状态
            with self.lock:
                self.devices[device_id] = {
                    "future": None,
                    "instance": None,
                    "status": "error",
                    "start_time": datetime.now(),
                    "error": str(e)
                }
    
    def _run_device_task(self, demo_instance, device_id):
        """运行设备任务的线程函数"""
        try:
            logger.info(f"[{device_id}] 开始执行任务")
            result = demo_instance.main_function()
            
            with self.lock:
                if device_id in self.devices:
                    self.devices[device_id]["status"] = "completed"
                    self.devices[device_id]["result"] = result
            
            logger.info(f"[{device_id}] 任务完成: {result}")
            
        except Exception as e:
            logger.error(f"[{device_id}] 任务执行出错: {e}")
            with self.lock:
                if device_id in self.devices:
                    self.devices[device_id]["status"] = "error"
                    self.devices[device_id]["error"] = str(e)
    
    def get_device_status(self, device_id=None):
        """
        获取设备状态
        :param device_id: 设备ID，None表示获取所有设备状态
        """
        with self.lock:
            if device_id:
                device_info = self.devices.get(device_id)
                if not device_info:
                    return None
                # 复制一份数据，避免在锁外访问时出现问题
                return {
                    "status": device_info["status"],
                    "start_time": device_info["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                # 复制所有设备的状态信息
                result = {}
                for k, v in self.devices.items():
                    result[k] = {
                        "status": v["status"],
                        "start_time": v["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                    }
                return result
    
    def print_status(self):
        """打印所有设备状态"""
        status = self.get_device_status()
        logger.info("\n" + "=" * 60)
        logger.info("当前设备状态:")
        logger.info("=" * 60)
        for device_id, info in status.items():
            logger.info(f"设备ID: {device_id}")
            logger.info(f"  状态: {info['status']}")
            logger.info(f"  启动时间: {info['start_time']}")
            logger.info(f"  执行结果: {info['result']}")
            logger.info("-" * 60)
    
    def wait_all_complete(self):
        """等待所有设备任务完成"""
        logger.info("等待所有设备任务完成...")
        with self.lock:
            futures = [info["future"] for info in self.devices.values() if info["future"] is not None]
        
        # 等待所有任务完成
        for future in as_completed(futures):
            try:
                future.result()  # 获取结果，如果有异常会抛出
            except Exception as e:
                logger.error(f"任务执行异常: {e}")
        
        logger.info("✓ 所有设备任务已完成")
        self.print_status()
    
    def get_active_count(self):
        """获取正在运行的设备数量"""
        with self.lock:
            return sum(1 for v in self.devices.values() if v["status"] == "running")
    
    def get_total_count(self):
        """获取总设备数量"""
        with self.lock:
            return len(self.devices)
    
    def remove_device(self, device_id):
        """
        移除设备（仅移除已完成或出错的设备）
        :param device_id: 设备ID
        :return: 是否成功移除
        """
        with self.lock:
            if device_id not in self.devices:
                logger.warning(f"设备 {device_id} 不存在")
                return False
            
            device_info = self.devices[device_id]
            if device_info["status"] == "running":
                # 检查 future 是否还在运行
                if device_info["future"] and not device_info["future"].done():
                    logger.warning(f"设备 {device_id} 正在运行，无法移除")
                    return False
            
            del self.devices[device_id]
            logger.info(f"✓ 设备 {device_id} 已移除")
            return True
    
    def stop(self):
        """停止设备管理器"""
        self.running = False
        # 关闭线程池，等待所有任务完成
        self.executor.shutdown(wait=True)
        logger.info("设备管理器已停止")

