# SeleniumBase  测试项目

本项目使用 SeleniumBase 框架对开源项目Cypress Real World App进行自动化测试，覆盖从登录到购买的完整流程。

## 技术栈
- Python 3.9+
- SeleniumBase
- pytest

## 项目结构
- `tests/`：测试文件目录
- `README.md`：项目说明
- `requirements.txt`：依赖管理
- `.gitignore`：Git 忽略配置

## 测试流程
1. 克隆并启动 Cypress Real World App
2. 安装 SeleniumBase

## Cypress Real World App开源项目介绍
- 用户认证 ：注册、登录、登出
- 支付管理 ：添加支付方式、管理支付方式
- 交易流程 ：创建交易、处理交易、查看交易历史
- 用户设置 ：修改个人信息、管理账户设置

# 全局conftest -----------------------------
执行顺序自上而下
### 1）收集阶段
- pytest_addoption(parser)：最先执行之一，用来注册命令行参数
- pytest_collection_modifyitems(config,items)：收集到全部测试项后，它只是“打标记”，不启动应用。
遍历 items，把用到 app_manager fixture 的测试自动加上 requires_app 标记。
### 2）会话级 fixture 初始化（session fixtures setup）
- app_manager(request)
- global_app_setup(app_manager, request)
### 3）每条用例开始前（per-test setup hook）
- pytest_runtest_setup(item)：
### 4）用例函数执行（call）
- @handle_app_exception(app_manager, strategy=...)：在用例函数体之前再次检查 app_manager.result，失败则 fail/skip/xfail。
- @retry_on_app_failure(...)：包裹用例函数，异常则重试（它不会自动检查 AppStatus，只要抛异常就重试）
### 5）会话结束（session teardown）

# 运行所有测试
pytest tests/

# 带演示模式运行
pytest tests/ --demo

# 生成 HTML 报告
pytest tests/ --html=report.html

## 测试账号
默认测试账号（如果应用包含示例数据）：
- 用户名：user@example.com
- 密码：password123
