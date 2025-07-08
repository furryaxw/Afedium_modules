document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("module-container");

  fetch("index.json")
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(modules => {
      modules.forEach(module => {
        // Create a container for the module
        const moduleDiv = document.createElement("div");
        moduleDiv.className = "module";

        // Module Name
        const name = document.createElement("h2");
        name.textContent = module.name;
        moduleDiv.appendChild(name);

        // Module Description
        if (module.description) {
          const description = document.createElement("p");
          description.textContent = module.description;
          moduleDiv.appendChild(description);
        }

        // Module Meta Info (Author, Version)
        const meta = document.createElement("div");
        meta.className = "module-meta";
        meta.innerHTML = `
          <span>Author: ${module.author}</span> |
          <span>Version: ${module.version}</span>
        `;
        moduleDiv.appendChild(meta);

        // Dependencies
        const dependenciesDiv = document.createElement("div");
        dependenciesDiv.className = "module-dependencies";

        // Module Dependencies
        if (module.dependencies && module.dependencies.length > 0) {
          const depList = document.createElement("ul");
          module.dependencies.forEach(dep => {
            const item = document.createElement("li");
            item.textContent = dep;
            depList.appendChild(item);
          });
          const strong = document.createElement("strong");
          strong.textContent = "Dependencies:";
          dependenciesDiv.appendChild(strong);
          dependenciesDiv.appendChild(depList);
        }

        // Pip Dependencies
        if (module.pip_dependencies && module.pip_dependencies.length > 0) {
          const pipList = document.createElement("ul");
          module.pip_dependencies.forEach(dep => {
            const item = document.createElement("li");
            item.textContent = dep;
            pipList.appendChild(item);
          });
          const strong = document.createElement("strong");
          strong.textContent = "Pip Dependencies:";
          dependenciesDiv.appendChild(strong);
          dependenciesDiv.appendChild(pipList);
        }

        moduleDiv.appendChild(dependenciesDiv);

        // Append the module to the container
        container.appendChild(moduleDiv);
      });
    })
    .catch(error => {
      console.error("Error fetching or parsing modules:", error);
      container.innerHTML += "<p style='color: red;'>Error loading modules. Please check the console for details.</p>";
    });
});