#主要测试文件
from seleniumbase import BaseCase


class CypressRealworldApp(BaseCase):
    def test_crwa_login_and_purchase(self):
        # 1. 访问登录页面
        self.open("https://www.saucedemo.com")

        # 2. 输入用户名和密码并登录
        self.type("#user-name", "standard_user")
        self.type("#password", "secret_sauce\n")  # \n 表示按回车键

        # 3. 验证登录成功（断言商品列表页加载）
        self.assert_element("div.inventory_list")
        self.assert_exact_text("Products", "span.title")

        # 4. 添加商品到购物车
        self.click('button[name*="backpack"]')
        self.click("#shopping_cart_container a")

        # 5. 验证商品已添加到购物车
        self.assert_exact_text("Your Cart", "span.title")
        self.assert_text("Backpack", "div.cart_item")

        # 6. 点击结算按钮
        self.click("button#checkout")

        # 7. 填写结账信息
        self.type("#first-name", "Test")
        self.type("#last-name", "User")
        self.type("#postal-code", "12345")
        self.click("input#continue")

        # 8. 验证结账信息页面
        self.assert_exact_text("Checkout: Overview", "span.title")
        self.assert_text("Backpack", "div.cart_item")

        # 9. 完成购买
        self.click("button#finish")

        # 10. 验证购买成功
        self.assert_exact_text("Thank you for your order!", "h2")
        self.assert_element('img[alt="Pony Express"]')

        # 11. 退出登录
        self.js_click("button#react-burger-menu-btn")
        self.click("a#logout_sidebar_link")
        self.assert_element("div#login_button_container")