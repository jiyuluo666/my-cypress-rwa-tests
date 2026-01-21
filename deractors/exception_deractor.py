"""
测试装饰器 - 用于统一异常处理
1)虽然有excep_manager.py异常处理工具，但是在业务逻辑中还是需要主动调用。
也就是说需要在不同的逻辑中重复调用，还要将app_manager传进去，代码不够简洁
因此使用此装饰器统一处理项目中的测试异常

2)直接用类似注解的方式访问
这里主要是两个注解：异常处理+重试处理
"""
import functools
import logging
import time


from utils.excep_manager import AppManager, handle_app_failure, AppStatus
from conftest import get_app_manager
logger = logging.getLogger(__name__)


def handle_app_exception(strategy: str = "skip", app_manager: AppManager = None):
    """
    装饰器：统一处理应用异常（自动获取或手动传入 app_manager）

    Args:
        strategy: 处理策略 - "skip" | "fail" | "xfail"
        app_manager: 应用管理器实例（可选，如果不传则自动获取）

    使用示例:
        @handle_app_exception(strategy="skip")
        def test_something(self):
            ...

        # 或者在类级别使用
        @handle_app_exception(strategy="skip")
        class MyTest(BaseCase):
            ...
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            # 自动获取 app_manager（如果没有传入）
            manager = app_manager
            if manager is None:
                # 尝试从 kwargs 中获取（如果是通过 fixture 传入的）
                if 'app_manager' in kwargs:
                    manager = kwargs['app_manager']
                else:
                    # 从全局获取
                    manager = get_app_manager()

            # 检查应用状态
            if manager.result and manager.result.status == AppStatus.FAILED:
                handle_app_failure(manager, strategy=strategy)

            # 如果应用正常，运行测试
            return test_func(*args, **kwargs)

        return wrapper
    return decorator


def retry_on_app_failure(max_retries: int = 3, delay: int = 2):
    """
       装饰器：测试失败时重试整个测试

       使用示例:
           @retry_on_app_failure(max_retries=3, delay=2)
           def test_something(self):
               ...
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return test_func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"测试失败，尝试 {attempt + 1}/{max_retries}: {str(e)}")

                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        # 捕捉到异常之后，可以在这里尝试重启应用
                        continue

            # 所有重试都失败
            raise last_exception if last_exception else Exception("测试失败")

        return wrapper

    return decorator
