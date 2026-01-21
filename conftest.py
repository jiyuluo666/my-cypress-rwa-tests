
"""
统一配置 - 使用统一异常处理机制+缓存机制
"""
import time
from typing import Dict, Any

import pytest


from utils.excep_manager import AppManager, AppStatus, handle_app_failure
from utils.operate_yaml import read_yaml

#读取yaml文件
import os

config=read_yaml("pytest_app_config.yaml")

# 全局应用管理器
_APP_MANAGER = None
_REQUIRES_APP_CACHE: Dict[str, bool] = {}
_HEALTH_CHECK_CACHE: Dict[str, Any] = {
    "status": None,
    "timestamp": 0,
    "ttl": 60  # 缓存有效期（秒）
}

def get_app_manager(app_dir: str = None,health_check_url:str=None) -> AppManager:
    """
    获取或创建应用管理器
    :param health_check_url:测试对象健康网址（传入或默认）
    :param app_dir:测试对象网址{传入或默认）
    :return:
    """
    global _APP_MANAGER

    if _APP_MANAGER is None:
        if app_dir is None:
            app_dir =config["app"]["dir"]
        if health_check_url is None:
            health_check_url = config["app"]["health_check"]

        _APP_MANAGER = AppManager(
            app_dir=app_dir,
            max_retries=config["app"]["max_retries"],
            health_check_url=health_check_url
        )

    return _APP_MANAGER

# Hook函数
def pytest_addoption(parser):
    """添加pytest命令行参数配置"""
    parser.addoption(
        "--app-fail-strategy",
        action="store",
        default="skip",
        choices=["skip", "fail", "xfail"],
        help="应用启动失败时的处理策略"
    )
    parser.addoption(
        "--app-dir",
        action="store",
        default=None,
        help="应用目录路径"
    )
    parser.addoption(
        "--app-retry",
        action="store",
        type=int,
        default=2,
        help="应用启动重试次数"
    )


@pytest.fixture(scope="session")
def app_manager(request):
    """提供应用管理器fixture，主要用于 管理应用程序的生命周期:
    启动->运行->（失败-按策略执行）->终止进程
    """
    app_dir = request.config.getoption("--app-dir")
    max_retries = request.config.getoption("--app-retry")

    #app_dir不在命令行输入的话，会在get_app_manager方法内自动取默认值
    #get_app_manager方法会返回一个AppManager对象
    manager = get_app_manager(app_dir)
    manager.max_retries = max_retries

    # 启动应用
    result = manager.start_app()

    # 如果启动失败，根据策略处理
    if result.status == AppStatus.FAILED:
        strategy = request.config.getoption("--app-fail-strategy")
        handle_app_failure(manager, strategy=strategy, test_item=request)

    yield manager

    # 测试结束后清理
    manager.stop_app()


@pytest.fixture(scope="session", autouse=True)
def global_app_setup(app_manager, request):
    """全局应用设置（可选）"""
    # 这里可以添加全局的设置逻辑
    yield

    # 这里可以添加全局的清理逻辑


# 全局Hook：在测试运行前检查应用状态
def pytest_runtest_setup(item, ):
    """测试设置阶段检查应用状态
    1）这里不能直接取全局变量里的值，虽然前面app_manager会先执行，但是是有条件的
    也就是必须使用上述fixture的测试才可以，否则会取出来一个None值，会有问题
    2）此处还增加了缓存机制，设置了全局变量后，在每个测试进行检查之前，可以先判断缓存中有没有，如果有，可以直接取用
    减小了性能开销
    """
    app_manager = get_app_manager()
    # app_manager = _APP_MANAGER


    # 如果应用正常且缓存有效，直接返回
    if app_manager.result and app_manager.result.status == AppStatus.RUNNING:
        # 检查健康检查缓存是否有效
        cache = _HEALTH_CHECK_CACHE
        current_time = time.time()
        if cache["status"] is True and (current_time - cache["timestamp"]) < cache["ttl"]:
            return  # 缓存有效，直接返回

    # 如果应用状态失败，才需要进一步检查
    if app_manager.result and app_manager.result.status == AppStatus.FAILED:
        # 使用缓存避免重复遍历 markers
        item_id = item.nodeid
        if item_id not in _REQUIRES_APP_CACHE:
            _REQUIRES_APP_CACHE[item_id] = "requires_app" in [mark.name for mark in item.iter_markers()]

        if _REQUIRES_APP_CACHE[item_id]:
            handle_app_failure(app_manager, strategy=None, test_item=item)



# Hook：在测试集合阶段标记需要应用的测试
def pytest_collection_modifyitems(config, items):
    """
    1）自动为使用app_manager fixture的测试添加requires_app标记
    也就是说，使用了app_manager标记的一定要使用requires_app标记
    2）为什么要做这一步？看起来有点多余，实际上是因为有时候不会显式调用app_manager
    有可能是间接依赖，但也需要启动服务，所有这种方式拓展性更好
    """
    for item in items:
        # 检查测试是否使用app_manager fixture
        if hasattr(item, 'fixturenames') and 'app_manager' in item.fixturenames:
            item.add_marker(pytest.mark.requires_app)