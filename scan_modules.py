import ast
import json
import os
import sys


def get_info(module: str):
    try:
        with open(module, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code)
    except (IOError, SyntaxError):
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id == 'Info':
                    try:
                        value = ast.literal_eval(node.value)
                        if isinstance(value, dict):
                            return value
                        else:
                            continue
                    except ValueError:
                        continue
    return None


def pick_module(name):
    if name.endswith("py"):
        return name.split(".")[0]
    else:
        return ""


modules_data = []
module_files = os.listdir("modules")
modules = map(pick_module, module_files)
modules = [_ for _ in modules if _ != ""]
for name in modules:
    info = get_info(f"modules/{name}.py")
    modules_data.append(info)

data = json.dumps({
    "site": "Afedium官方模块仓库",
    "base_url": "http://modules.afedium.furryaxw.top/",
    "last_update_date": "",
    "module_count": len(modules_data),
    "version": 1,

    "modules": modules_data
}, ensure_ascii=False, indent=2)

print(data)
with open("index.json", "w", encoding="utf-8") as f:
    f.write(data)
    f.flush()
