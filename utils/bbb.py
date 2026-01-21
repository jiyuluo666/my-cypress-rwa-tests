import os

from utils.operate_yaml import read_yaml
#
# config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yaml', 'pytest_app_config.yaml')
# print(config_path)
config=read_yaml("pytest_app_config.yaml")
print(config["app"]["command"])