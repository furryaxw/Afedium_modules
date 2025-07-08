document.addEventListener("DOMContentLoaded", () => {
    const gridContainer = document.getElementById("module-grid");

    fetch("index.json")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP 错误! 状态: ${response.status}`);
            }
            return response.json();
        })
        .then(modules => {
            modules.forEach(module => {
                const moduleDiv = document.createElement("div");
                moduleDiv.className = "module";

                // ... 标题和描述部分无变动 ...
                const nameH2 = document.createElement("h2");
                if (module.homepage) {
                    const link = document.createElement("a");
                    link.href = module.homepage;
                    link.textContent = module.name;
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                    nameH2.appendChild(link);
                } else {
                    nameH2.textContent = module.name;
                }
                const idSpan = document.createElement("span");
                idSpan.className = "module-id";
                idSpan.textContent = module.id;
                nameH2.appendChild(idSpan);
                moduleDiv.appendChild(nameH2);

                if (module.description) {
                    const description = document.createElement("p");
                    description.className = "description";
                    description.textContent = module.description;
                    moduleDiv.appendChild(description);
                } else {
                    const placeholder = document.createElement("p");
                    placeholder.className = "description";
                    moduleDiv.appendChild(placeholder);
                }

                // --- 依赖项部分 (已更新) ---
                const dependenciesDiv = document.createElement("div");
                dependenciesDiv.className = "module-dependencies";

                const depTypes = [
                    { title: "模块依赖", key: "dependencies" },
                    { title: "Pip 依赖", key: "pip_dependencies" },
                    { title: "Linux 依赖", key: "linux_dependencies" }
                ];

                const hasDependencies = depTypes.some(dep => module[dep.key] && module[dep.key].length > 0);

                if (hasDependencies) {
                    const table = document.createElement("table");

                    depTypes.forEach(depType => {
                        const deps = module[depType.key];
                        if (deps && deps.length > 0) {
                            const row = table.insertRow();

                            const cellType = row.insertCell();
                            cellType.className = "dep-type";
                            cellType.textContent = depType.title + ":";

                            const cellList = row.insertCell();
                            cellList.className = "dep-list-cell"; // 使用新的class

                            // --- 关键改动在这里 ---
                            // 遍历依赖项，为每个依赖创建一个span标签
                            deps.forEach(dep => {
                                const tag = document.createElement("span");
                                tag.className = "dep-tag";
                                tag.textContent = dep;
                                cellList.appendChild(tag);
                            });
                        }
                    });

                    dependenciesDiv.appendChild(table);
                }

                moduleDiv.appendChild(dependenciesDiv);

                // --- 页脚区域 (无变动) ---
                const cardFooter = document.createElement("div");
                cardFooter.className = "card-footer";
                const typeSpan = document.createElement("span");
                typeSpan.className = "module-type";
                typeSpan.textContent = module.type || "未知类型";
                cardFooter.appendChild(typeSpan);

                const footerRight = document.createElement("div");
                footerRight.className = "footer-right";
                const metaSpan = document.createElement("span");
                metaSpan.className = "module-meta";
                metaSpan.innerHTML = `<span>作者: ${module.author}</span> | <span>版本: ${module.version}</span>`;
                footerRight.appendChild(metaSpan);

                const downloadBtn = document.createElement("a");
                downloadBtn.className = "download-btn";
                downloadBtn.href = module.url;
                downloadBtn.textContent = "下载";
                footerRight.appendChild(downloadBtn);

                cardFooter.appendChild(footerRight);
                moduleDiv.appendChild(cardFooter);

                gridContainer.appendChild(moduleDiv);
            });
        })
        .catch(error => {
            console.error("获取或解析模块时出错:", error);
            gridContainer.innerHTML = "<p style='color: red;'>加载模块出错，请检查控制台获取详细信息。</p>";
        });
});