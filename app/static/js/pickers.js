(function (window, document) {
  function createChip(item, roles, onRemove, onRoleChange) {
    const li = document.createElement("li");
    li.className = "list-group-item d-flex align-items-center justify-content-between";
    li.dataset.hospitalId = item.hospital_id;

    const left = document.createElement("div");
    left.innerHTML = `<strong>${item.hospital}</strong>`;

    const controls = document.createElement("div");
    controls.className = "d-flex align-items-center gap-2";

    const select = document.createElement("select");
    select.className = "form-select form-select-sm";
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "Seleccionar rol";
    select.appendChild(defaultOption);
    roles.forEach((rol) => {
      const option = document.createElement("option");
      option.value = String(rol.id);
      option.textContent = rol.nombre;
      if (item.rol_id && Number(item.rol_id) === Number(rol.id)) {
        option.selected = true;
      }
      select.appendChild(option);
    });
    select.addEventListener("change", () => onRoleChange(item.hospital_id, select.value));

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "btn btn-sm btn-outline-danger";
    removeBtn.textContent = "Quitar";
    removeBtn.addEventListener("click", () => onRemove(item.hospital_id));

    controls.appendChild(select);
    controls.appendChild(removeBtn);

    li.appendChild(left);
    li.appendChild(controls);
    return li;
  }

  function UserHospitalAssignment(options) {
    const config = Object.assign(
      {
        userInput: "#usuarioLookup",
        hospitalInput: "#hospitalLookup",
        hospitalList: "#hospitalAssignments",
        resourceUsers: "usuarios",
        resourceHospitals: "hospitales",
        onUserSelected: () => {},
        roles: [],
      },
      options || {}
    );

    const userInput = document.querySelector(config.userInput);
    const hospitalInput = document.querySelector(config.hospitalInput);
    const hospitalList = document.querySelector(config.hospitalList);
    const state = new Map();

    let currentUserId = null;

    function renderHospitals(assignments) {
      if (!hospitalList) {
        return;
      }
      hospitalList.innerHTML = "";
      assignments.forEach((item) => {
        const node = createChip(item, config.roles, removeHospital, updateRole);
        hospitalList.appendChild(node);
      });
    }

    function removeHospital(hospitalId) {
      state.delete(hospitalId);
      renderHospitals(Array.from(state.values()));
    }

    function updateRole(hospitalId, rolId) {
      const current = state.get(hospitalId);
      if (current) {
        current.rol_id = rolId ? Number(rolId) : null;
      }
    }

    function addHospital(item) {
      if (!item) return;
      if (state.has(item.id)) {
        return;
      }
      state.set(item.id, {
        hospital_id: item.id,
        hospital: item.label,
        rol_id: null,
      });
      renderHospitals(Array.from(state.values()));
      hospitalInput.value = "";
    }

    if (userInput) {
      window.attachLiveSearch(userInput, {
        resource: config.resourceUsers,
        targetListEl: document.querySelector("#usuarioLookupResults"),
        onSelect: (item) => {
          currentUserId = item.id;
          userInput.value = item.label;
          if (typeof config.onUserSelected === "function") {
            config.onUserSelected(item);
          }
          fetch(`/api/search/usuarios/${item.id}/hospitales`, {
            headers: { Accept: "application/json" },
            credentials: "same-origin",
          })
            .then((response) => response.json())
            .then((data) => {
              state.clear();
              (data.items || []).forEach((assignment) => {
                state.set(assignment.hospital_id, assignment);
              });
              renderHospitals(Array.from(state.values()));
            });
        },
      });
    }

    if (hospitalInput) {
      window.attachLiveSearch(hospitalInput, {
        resource: config.resourceHospitals,
        targetListEl: document.querySelector("#hospitalLookupResults"),
        onSelect: addHospital,
      });
    }

    return {
      getAssignments() {
        return Array.from(state.values());
      },
      getUsuarioId() {
        return currentUserId;
      },
      removeHospital,
      addHospital,
    };
  }

  window.UserHospitalAssignment = UserHospitalAssignment;
})(window, document);
