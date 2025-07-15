import shutil
import os
import sys


def create_afedium_plugin(source_dir):
    if not os.path.isdir(source_dir):
        print(f"错误: 源目录 '{source_dir}' 不存在。")
        return

    # PYZ 文件名将与源目录名相同
    output_filename = os.path.basename(source_dir)
    # 目标路径
    target_path = os.path.join('pyz_modules', output_filename)
    print(f"正在将 '{source_dir}' 打包到 '{target_path}.pyz'...")

    try:
        os.remove(target_path + '.pyz')
    except FileNotFoundError:
        pass

    try:
        # 使用 shutil 创建 zip 归档
        shutil.make_archive(target_path, 'zip', source_dir)
        # 将 .zip 重命名为 .pyz
        os.rename(target_path + '.zip', target_path + '.pyz')

        print(f"成功创建插件: {target_path}.pyz")
    except Exception as e:
        print(f"创建插件时出错: {e}")
        try:
            os.remove(target_path + '.zip')
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    if len(sys.argv) > 1:
        source_directory = sys.argv[1]
        create_afedium_plugin(source_directory)
    else:
        print("请提供插件的源目录作为参数。")
        print("用法: python create_pyz.py <你的插件源目录>")
        # 示例：python create_pyz.py advanced_template
