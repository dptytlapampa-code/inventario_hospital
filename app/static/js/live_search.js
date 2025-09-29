(function (window, document) {
  const DEFAULT_DEBOUNCE = 200;

  function debounce(fn, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  function renderResults(target, items, templateFn) {
    if (!target) {
      return;
    }
    target.innerHTML = "";
    if (!items.length) {
      target.innerHTML = '<li class="list-group-item text-muted">Sin resultados</li>';
      return;
    }
    const fragment = document.createDocumentFragment();
    items.forEach((item) => {
      const element = templateFn(item);
      fragment.appendChild(element);
    });
    target.appendChild(fragment);
  }

  function defaultTemplate(item) {
    const li = document.createElement("li");
    li.className = "list-group-item list-group-item-action";
    li.textContent = item.label;
    li.dataset.value = item.id;
    return li;
  }

  function attachLiveSearch(inputEl, options) {
    const config = Object.assign(
      {
        minLength: 1,
        debounce: DEFAULT_DEBOUNCE,
        templateItem: defaultTemplate,
        targetListEl: null,
        resource: null,
        extraParamsFn: null,
        onSelect: null,
      },
      options || {}
    );

    const target =
      typeof config.targetListEl === "string"
        ? document.querySelector(config.targetListEl)
        : config.targetListEl;

    if (!inputEl || !config.resource) {
      return () => {};
    }

    let activeIndex = -1;
    let lastItems = [];

    function moveActive(delta) {
      if (!target) {
        return;
      }
      const items = Array.from(target.querySelectorAll(".list-group-item"));
      if (!items.length) {
        return;
      }
      items.forEach((item) => item.classList.remove("active"));
      activeIndex = (activeIndex + delta + items.length) % items.length;
      items[activeIndex].classList.add("active");
      items[activeIndex].scrollIntoView({ block: "nearest" });
    }

    function triggerSelect(item) {
      if (typeof config.onSelect === "function") {
        config.onSelect(item);
      }
    }

    function handleKeyboard(event) {
      if (!target || !lastItems.length) {
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        moveActive(1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        moveActive(-1);
      } else if (event.key === "Enter" && activeIndex >= 0) {
        event.preventDefault();
        triggerSelect(lastItems[activeIndex]);
      }
    }

    function fetchResults(value) {
      if (!value || value.length < config.minLength) {
        if (target) {
          target.innerHTML = "";
        }
        return;
      }
      const params = new URLSearchParams({ q: value });
      if (typeof config.extraParamsFn === "function") {
        const extra = config.extraParamsFn() || {};
        Object.entries(extra).forEach(([key, val]) => {
          if (val !== undefined && val !== null && val !== "") {
            params.append(key, val);
          }
        });
      }
      fetch(`/api/search/${config.resource}?${params.toString()}`, {
        headers: {
          Accept: "application/json",
        },
        credentials: "same-origin",
      })
        .then((response) => response.json())
        .then((data) => {
          lastItems = data.items || [];
          activeIndex = -1;
          if (target) {
            renderResults(target, lastItems, (item) => {
              const element = config.templateItem(item);
              element.addEventListener("click", () => triggerSelect(item));
              return element;
            });
          }
        })
        .catch(() => {
          if (target) {
            target.innerHTML = '<li class="list-group-item text-danger">Error al buscar</li>';
          }
        });
    }

    const debounced = debounce(fetchResults, config.debounce);
    inputEl.addEventListener("input", (event) => {
      const value = event.target.value;
      debounced(value);
    });
    inputEl.addEventListener("keydown", handleKeyboard);

    return function detach() {
      inputEl.removeEventListener("input", debounced);
      inputEl.removeEventListener("keydown", handleKeyboard);
    };
  }

  window.attachLiveSearch = attachLiveSearch;
})(window, document);
