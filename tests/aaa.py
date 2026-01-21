from utils.operate_yaml import read_yaml



# 使用示例
if __name__ == "__main__":
    config=read_yaml("../yaml/pytest_app_config.yaml")
    print("读取的路径是：",config["app"]["dir"])