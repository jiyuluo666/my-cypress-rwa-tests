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
1. 访问 Cypress Real World App登录页面
2. 输入用户名和密码登录
3. 添加商品到购物车
4. 进入购物车页面验证
5. 填写结账信息
6. 完成购买流程
7. 验证购买成功

## 运行测试
### 安装依赖
```bash
pip install -r requirements.txt
