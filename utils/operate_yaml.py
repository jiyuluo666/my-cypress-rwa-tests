
import os
import yaml
from pathlib import Path


def read_yaml(yaml_filename, max_depth=5):
    """
    自动定位并读取 YAML 文件

    参数:
        yaml_filename: YAML 文件名 (如: 'pytest_app_config.yaml')
        max_depth: 最大向上查找层级 (默认: 5)

    返回:
        YAML 文件内容
    """
    # 获取当前调用者文件路径
    import inspect
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename

    # 从调用者文件位置开始查找
    current_dir = Path(caller_file).parent

    for depth in range(max_depth + 1):
        # 尝试在当前目录查找 yaml 文件夹
        yaml_dir = current_dir / 'yaml'
        if yaml_dir.exists() and yaml_dir.is_dir():
            yaml_path = yaml_dir / yaml_filename
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)

        # 向上级目录查找
        if current_dir.parent == current_dir:  # 到达根目录
            break
        current_dir = current_dir.parent

    # 如果没找到，尝试直接在同级目录查找
    yaml_path = Path(caller_file).parent / yaml_filename
    if yaml_path.exists():
        with open(yaml_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    raise FileNotFoundError(
        f"找不到 YAML 文件: {yaml_filename}\n"
        f"在以下位置查找:\n"
        f"- {Path(caller_file).parent}/yaml/{yaml_filename}\n"
        f"- 以及向上 {max_depth} 级目录"
    )