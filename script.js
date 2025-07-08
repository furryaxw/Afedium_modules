document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("module-container");

    fetch("index.json")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP 错误! 状态: ${response.status}`);
            }
            return response.json();
        })
        .then(modules => {
            modules.forEach(module => {
                // 为每个模块创建一个容器 div
                const moduleDiv = document.createElement("div");
                moduleDiv.className = "module";

                // 创建一个 <a> 标签作为链接
                const link = document.createElement("a");
                link.href = module.url; // 设置链接地址为模块的 URL
                link.style.textDecoration = 'none'; // 可选：去掉链接的下划线

                // 模块名称 (H2)
                const name = document.createElement("h2");
                name.textContent = module.name;

                // 将 H2 标题放入链接中
                link.appendChild(name);

                // 将完整的链接（包含标题）添加到模块 DIV 中
                moduleDiv.appendChild(link);
                // --- 修改结束 ---

                // 模块描述
                if (module.description) {
                    const description = document.createElement("p");
                    description.textContent = module.description;
                    moduleDiv.appendChild(description);
                }

                // 模块元信息 (作者, 版本)
                const meta = document.createElement("div");
                meta.className = "module-meta";
                meta.innerHTML = `
                    <span>作者: ${module.author}</span> |
                    <span>版本: ${module.version}</span>
                `;
                moduleDiv.appendChild(meta);

                // 依赖项的容器
                const dependenciesDiv = document.createElement("div");
                dependenciesDiv.className = "module-dependencies";

                // 渲染依赖列表的辅助函数
                const renderDependencies = (title, deps) => {
                    if (deps && deps.length > 0) {
                        const strong = document.createElement("strong");
                        strong.textContent = title;
                        dependenciesDiv.appendChild(strong);

                        const list = document.createElement("ul");
                        deps.forEach(dep => {
                            const item = document.createElement("li");
                            item.textContent = dep;
                            list.appendChild(item);
                        });
                        dependenciesDiv.appendChild(list);
                    }
                };

                // 渲染各种依赖
                renderDependencies("模块依赖:", module.dependencies);
                renderDependencies("Pip 依赖:", module.pip_dependencies);
                renderDependencies("Linux 依赖:", module.linux_dependencies);

                moduleDiv.appendChild(dependenciesDiv);

                // 将完整的模块 div 添加到主容器中
                container.appendChild(moduleDiv);
            });
        })
        .catch(error => {
            console.error("获取或解析模块时出错:", error);
            container.innerHTML += "<p style='color: red;'>加载模块出错，请检查控制台获取详细信息。</p>";
        });
});