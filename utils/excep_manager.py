
"""
统一的异常处理机制 - 应用管理器
1）让上层（conftest.py、装饰器）只需要判断 manager.result.status，不关心启动细节。
2）在AppManager 中增加了健康检查的缓存机制，无需每次测试之前都进行一次检查
"""
import os
import subprocess
import time
import signal
import functools
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

import pytest

from utils.operate_yaml import read_yaml

logger = logging.getLogger(__name__)
config=read_yaml("pytest_app_config.yaml")

class AppStatus(Enum):
    """应用状态枚举"""
    NOT_STARTED = "应用未启动"
    STARTING = "应用启动中..."
    RUNNING = "应用运行中..."
    FAILED = "应用启动失败"
    STOPPED = "应用启动终止"


@dataclass
class AppResult:
    """应用启动结果"""
    status: AppStatus
    process: Optional[subprocess.Popen] = None
    error: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    start_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AppManager:
    """统一的应用管理器，提供异常处理和状态管理"""

    def __init__(self, app_dir: str, max_retries: int = 2, health_check_url: Optional[str] = None):
        """
        :param app_dir: 应用目录
        :param max_retries:最大重试次数
        :param health_check_url:健康检查网址
        """
        self.app_dir = app_dir
        self.max_retries = max_retries
        self.health_check_url = health_check_url
        self._app_result: Optional[AppResult] = None
        self._exception_handler: Optional[Callable] = None
        #优化后：增加了缓存机制
        self._health_check_cache = {
            "status": None,
            "timestamp": 0,
            "ttl": 60  # 缓存60秒
        }

    def set_exception_handler(self, handler: Callable):
        """设置自定义异常处理器，这是为“可插拔异常处理”预留的接口。但此处还未被定义"""
        self._exception_handler = handler

    def _default_exception_handler(self, result: AppResult, test_item=None) -> None:
        """默认异常处理策略，理论上可以处理所有类型的异常，但暂时就处理应用启动异常，且可以输出异常信息"""
        handle_app_failure(self, strategy=None, test_item=test_item)

    def _handle_exception(self, result: AppResult, test_item=None) -> None:
        """统一的异常处理入口"""
        if self._exception_handler:
            self._exception_handler(result, test_item)
        else:
            self._default_exception_handler(result, test_item)

    def start_app(self) -> AppResult:
        """启动应用，统一处理所有异常"""
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"尝试启动应用 (尝试 {attempt + 1}/{self.max_retries + 1})")

                # 检查应用目录是否存在
                import os
                if not os.path.exists(self.app_dir):
                    error_msg = f"应用目录不存在: {self.app_dir}"
                    logger.error(error_msg)
                    if attempt == self.max_retries:
                        self._app_result = AppResult(
                            status=AppStatus.FAILED,
                            error=error_msg
                        )
                        return self._app_result
                    continue

                # 启动应用（Windows 需要 shell=True）
                import platform
                is_windows = platform.system() == "Windows"
                startup_command=config["app"]["command"]

                
                # 启动应用
                process = subprocess.Popen(
                    startup_command,  # 使用配置文件中的启动命令
                    cwd=self.app_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    shell=is_windows
                )

                # 等待并检查启动状态
                time.sleep(2)  # 初始等待

                if process.poll() is not None:
                    # 进程已退出
                    stdout, stderr = process.communicate()
                    error_msg = f"进程已退出，返回码: {process.returncode}"

                    self._app_result = AppResult(
                        status=AppStatus.FAILED,
                        error=error_msg,
                        stdout=stdout,
                        stderr=stderr
                    )

                    if attempt == self.max_retries:
                        return self._app_result
                    continue

                # 健康检查
                if self.health_check_url:
                    if not self._health_check(process):
                        process.terminate()
                        process.wait()

                        if attempt == self.max_retries:
                            self._app_result = AppResult(
                                status=AppStatus.FAILED,
                                error="健康检查失败",
                                process=process
                            )
                            return self._app_result
                        continue

                # 启动成功
                self._app_result = AppResult(
                    status=AppStatus.RUNNING,
                    process=process,
                    metadata={"attempt": attempt + 1}
                )

                logger.info("应用启动成功")
                return self._app_result

            except Exception as e:
                logger.error(f"启动尝试 {attempt + 1} 失败: {str(e)}")

                if attempt == self.max_retries:
                    self._app_result = AppResult(
                        status=AppStatus.FAILED,
                        error=str(e),
                        metadata={"last_exception": e}
                    )
                    return self._app_result

        return self._app_result

    def _health_check(self, process: subprocess.Popen, timeout: int = 30) -> bool:
        """执行健康检查
        处理器处理的第二类异常：请求异常
        """
        import requests
        from requests.exceptions import RequestException
        #超时了就算失败
        start_time = time.time()
        while time.time() - start_time < timeout:
            if process.poll() is not None:
                return False

            try:
                #只有在返回码为200才行
                response = requests.get(self.health_check_url, timeout=2)
                if response.status_code == 200:
                    return True
            except RequestException:
                pass

            time.sleep(1)

        return False

    def quick_health_check(self, force: bool = False) -> None | int | bool:
        """
        快速健康检查（带缓存）
        :param force: 是否强制检查（忽略缓存）
        :return: 应用是否健康
        """
        import time

        # 检查缓存
        if not force:
            cache = self._health_check_cache
            current_time = time.time()
            if cache["status"] is not None and (current_time - cache["timestamp"]) < cache["ttl"]:
                return cache["status"]

        # 执行实际检查
        if not self.health_check_url:
            return True

        try:
            import requests
            response = requests.get(self.health_check_url, timeout=2)
            is_healthy = response.status_code == 200

            # 更新缓存
            self._health_check_cache = {
                "status": is_healthy,
                "timestamp": time.time(),
                "ttl": 60
            }
            return is_healthy
        except Exception:
            self._health_check_cache = {
                "status": False,
                "timestamp": time.time(),
                "ttl": 60
            }
            return False


    def stop_app(self):
        """
        停止应用：
        需要主动调用，调用时会先检查应用状态，如果还在进程中，才由停止进程的必要
        """
        if self._app_result and self._app_result.process:
            logger.info("停止应用...")
            self._app_result.process.terminate()
            self._app_result.process.wait()
            self._app_result.status = AppStatus.STOPPED
        else:
            logger.info("进程已经停止，无需进行操作...")

    @property
    def result(self) -> Optional[AppResult]:
        """获取启动结果"""
        return self._app_result

def handle_app_failure(app_manager: AppManager, strategy: str = None, test_item=None) -> None:
    """
    统一的异常处理函数 - 所有地方都调用这个函数

    Args:
        app_manager: 应用管理器实例
        strategy: 处理策略 ("skip" | "fail" | "xfail")，如果为 None，则从 test_item 获取
        test_item: pytest 测试项，用于获取配置的策略（如果 strategy 为 None）
    """
    if not app_manager.result or app_manager.result.status != AppStatus.FAILED:
        return  # 应用正常，不需要处理

    # 构建错误信息
    error_msg = f"应用启动失败: {app_manager.result.error}"
    if app_manager.result.stderr:
        error_msg += f"\n错误输出:\n{app_manager.result.stderr[:500]}..."

    # 获取策略
    if strategy is None:
        if test_item and hasattr(test_item, 'config'):
            strategy = test_item.config.getoption("--app-fail-strategy", "skip")
        else:
            strategy = "skip"

    # 根据策略处理
    if strategy == "fail":
        pytest.fail(error_msg)
    elif strategy == "skip":
        pytest.skip(error_msg)
    elif strategy == "xfail":
        pytest.xfail(error_msg)
    else:
        pytest.skip(error_msg)  # 默认跳过