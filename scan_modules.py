import json
import os
import zipfile

MODULE_DIR = "modules"
# 生成的索引版本更新为 2
INDEX_VERSION = 2


def get_info_from_pyz(module_path: str):
    """
    修改后的函数：从 .pyz 归档文件中读取并解析 info.json。
    """
    try:
        with zipfile.ZipFile(module_path, 'r') as zf:
            if 'info.json' in zf.namelist():
                with zf.open('info.json') as info_file:
                    return json.load(info_file)
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError) as e:
        print(f"错误: 无法从 '{module_path}' 读取有效的元信息: {e}")
    return None


def main():
    """
    主扫描和生成逻辑
    """
    modules_data = []

    if not os.path.isdir(MODULE_DIR):
        print(f"错误: 模块目录 '{MODULE_DIR}' 不存在。")
        return

    # 扫描目录下的 .pyz 文件
    module_files = [f for f in os.listdir(MODULE_DIR) if f.endswith(".pyz")]

    for file_name in module_files:
        full_path = os.path.join(MODULE_DIR, file_name)
        info = get_info_from_pyz(full_path)
        if info:
            modules_data.append(info)
        else:
            print(f"警告: 跳过无法解析的模块 {file_name}")

    # 生成 v2 版本的 index.json
    index_data = {
        "site": "Afedium官方模块仓库",
        "base_url": "http://modules.afedium.furryaxw.top/",
        "last_update_date": "",
        "module_count": len(modules_data),
        "version": INDEX_VERSION,
        "modules": modules_data
    }

    # 使用 ensure_ascii=False 以正确显示中文，indent=2 保持格式美观
    output_json = json.dumps(index_data, ensure_ascii=False, indent=2)

    try:
        with open("index.json", "w", encoding="utf-8") as f:
            f.write(output_json)
        print("\n成功将索引写入 index.json 文件。")
    except IOError as e:
        print(f"\n错误: 无法写入 index.json 文件: {e}")


if __name__ == "__main__":
    main()
