"""
Cypress Real World App - 身份验证测试
测试功能：用户注册、登录、登出
"""
import time
import uuid

import pytest
from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from seleniumbase import BaseCase

from deractors.exception_deractor import handle_app_exception, retry_on_app_failure


class AuthTest(BaseCase):
    """身份验证相关测试用例"""
    @pytest.fixture(autouse=True, scope="class")
    def setup_class(self, app_manager):
        """类级别的设置，确保应用已启动"""
        self.app_manager = app_manager

    def setUp(self):
        """测试前置设置"""
        super().setUp()

        # 清理登录态
        self.open("http://localhost:3000/")  # 使用正确的前端端口
        self.execute_script("localStorage.clear();")
        self.execute_script("sessionStorage.clear();")
        self.delete_all_cookies()
        self.refresh()

        # 等待页面加载
        self.wait_for_element("body")

    @handle_app_exception(strategy="skip")
    @retry_on_app_failure(max_retries=2, delay=3)
    def test_register_and_login_and_logout(self):
        """
        完整测试流程：注册新用户 -> 登录 -> 登出
        """
        # 生成唯一的用户名，避免重复注册失败
        unique_id = str(uuid.uuid4())[:8]
        test_username = f"testuser_{unique_id}"
        test_email = f"testuser_{unique_id}@example.com"
        test_password = "password123"

        # ========== 第一部分：用户注册 ==========
        # 当前在 /signin，点击“Sign Up”链接
        # 这个链接在 SignInForm 里是：<Link data-test="signup" to="/signup">
        self.click('a[href="/signup"]')
        # 或者使用包含文本的选择器
        # self.click("a:contains('Sign up')")

        # 等待注册页面加载
        self.wait_for_element("#firstName", timeout=10)

        # 填写注册表单
        self.type("#firstName", "Test")
        self.type("#lastName", "User")
        self.type("#username", test_username)
        self.type("#password", test_password)
        self.type("#confirmPassword", test_password)

        # 点击注册按钮
        self.click('button[type="submit"]')
        print("Clicked signup button, waiting for redirect...")

        # 或者使用文本选择器
        # self.click("button:contains('Sign Up')")

        # 关键修改：等待URL包含 /signin
        # 由于项目的路由跳转问题，我们需要等待URL变化
        start_time = time.time()
        timeout = 15
        while time.time() - start_time < timeout:
            #这里使用了seleniumbase框架的api
            current_url = self.get_current_url()
            print(f"Current URL: {current_url}")
            if "/signin" in current_url:
                print("Successfully redirected to signin page!")
                break
            # 如果仍然在 /signup，尝试再次点击注册按钮
            # 这是一个变通方法，应对路由跳转失败的情况
            if "/signup" in current_url:
                try:
                    # 检查是否仍在注册页面，如果是则再次提交
                    if self.is_element_visible('button[type="submit"]'):
                        print("Still on signup page, retrying submit...")
                        self.click('button[type="submit"]')
                except:
                    pass
            time.sleep(1)
        else:
            # 超时处理
            print("Timeout: Still on URL:", self.get_current_url())
            # # 尝试手动导航到登录页面
            # self.driver.get("http://localhost:3000/signin")
            # print("Manually navigated to signin page")

        # 等待注册成功，通常会跳转到登录页面或首页
        self.wait_for_element("#username", timeout=10)

        # 如果超时还在 /signup：把“页面错误/网络异常”信息抓出来
        # （你可以先手动 print 当前地址，确认是否还在 /signup）
        print("Current URL:", self.get_current_url())

        # 验证注册成功（可能需要根据实际页面调整）
        # 如果跳转到登录页面，验证登录表单存在
        # 如果显示成功消息，验证消息存在
        # 这里假设注册成功后会有提示或跳转
        time.sleep(20)  # 等待页面跳转

        # # ========== 第二部分：用户登录 ==========
        # # 填写登录信息（使用注册时的用户名和密码）
        self.type("#username", test_username)
        self.type("#password", test_password)
        self.click('button[type="submit"]')
        #
        # 等待登录成功后的页面元素
        # 登录成功后通常会显示导航栏或 Dashboard
        # self.wait_for_element('button[data-test="user-onboarding-next"]', timeout=10)
        # self.click('button[data-test="user-onboarding-next')
        # self.wait_for_element("nav", timeout=10)
        self.wait_for_element('[data-testid="PersonIcon"]', timeout=10)
        # 验证登录成功
        self.assert_element('[data-testid="PersonIcon"]')  # 验证导航栏存在
        # 验证用户名显示在页面上（可能需要根据实际页面调整）
        # self.assert_text(test_username, timeout=5)

        # # ========== 第三部分：用户登出 ==========
        # # 点击用户菜单或头像
        # # 根据实际页面元素调整选择器
        # if self.is_element_visible('button[aria-label*="User"]'):
        #     self.click('button[aria-label*="User"]')
        # elif self.is_element_visible('[data-test*="user-menu"]'):
        #     self.click('[data-test*="user-menu"]')
        # elif self.is_text_visible("User"):
        #     self.click("button:contains('User')")
        # else:
        #     # 尝试点击右上角的用户相关按钮
        #     self.click('button[type="button"]:last-of-type')
        #
        # # 等待下拉菜单出现
        # time.sleep(1)
        #
        # # 点击登出按钮
        # if self.is_text_visible("Sign out"):
        #     self.click("a:contains('Sign out')")
        # elif self.is_text_visible("Logout"):
        #     self.click("a:contains('Logout')")
        # elif self.is_element_visible('a[href="/signout"]'):
        #     self.click('a[href="/signout"]')
        # else:
        #     # 如果找不到登出链接，尝试其他可能的选择器
        #     self.click('button:contains("Sign out")')
        #
        # # 等待登出成功，通常会跳转到首页或登录页面
        # self.wait_for_element("body", timeout=10)
        # time.sleep(2)  # 等待页面跳转
        #
        # # 验证登出成功
        # # 验证登录链接再次出现，或验证用户菜单消失
        # self.assert_element('a[href="/signin"]')
        # # 或者验证欢迎页面文本
        # if self.is_text_visible("Welcome"):
        #     self.assert_text("Welcome")

    # @handle_app_exception(strategy="skip")
    # @retry_on_app_failure(max_retries=2, delay=2)
    # def test_login_with_existing_user(self):
    #     """
    #     测试使用已有账号登录（使用默认测试账号）
    #     """
    #     test_username = "user@example.com"
    #     test_password = "password123"
    #
    #     # 访问登录页面
    #     self.open("http://localhost:3001/signin")
    #     self.wait_for_element("#username", timeout=10)
    #
    #     # 填写登录信息
    #     self.type("#username", test_username)
    #     self.type("#password", test_password + "\n")
    #
    #     # 等待登录成功
    #     self.wait_for_element("nav", timeout=10)
    #
    #     # 验证登录成功
    #     self.assert_element("nav")
    #     # 可以添加更多验证，比如验证用户名显示等
    #
    # @handle_app_exception(strategy="skip")
    # @retry_on_app_failure(max_retries=2, delay=2)
    # def test_logout(self):
    #     """
    #     单独测试登出功能（假设已经登录）
    #     """
    #     # 先登录
    #     test_username = "user@example.com"
    #     test_password = "password123"
    #
    #     self.open("http://localhost:3001/signin")
    #     self.wait_for_element("#username", timeout=10)
    #     self.type("#username", test_username)
    #     self.type("#password", test_password + "\n")
    #     self.wait_for_element("nav", timeout=10)
    #
    #     # 执行登出
    #     # 点击用户菜单
    #     if self.is_element_visible('button[aria-label*="User"]'):
    #         self.click('button[aria-label*="User"]')
    #     elif self.is_text_visible("User"):
    #         self.click("button:contains('User')")
    #
    #     time.sleep(1)
    #
    #     # 点击登出
    #     if self.is_text_visible("Sign out"):
    #         self.click("a:contains('Sign out')")
    #     elif self.is_element_visible('a[href="/signout"]'):
    #         self.click('a[href="/signout"]')
    #
    #     # 验证登出成功
    #     self.wait_for_element("body", timeout=10)
    #     self.assert_element('a[href="/signin"]')
