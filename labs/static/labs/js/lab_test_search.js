(() => {
    "use strict";

    const panel = document.getElementById("lab-test-search-panel");
    const input = document.getElementById("lab-test-search");
    const status = document.getElementById("lab-test-search-status");
    const select = document.getElementById("id_lab_test");
    const dataElement = document.getElementById("lab-test-search-data");

    if (!panel || !input || !status || !select || !dataElement) {
        return;
    }

    let catalog;

    try {
        catalog = JSON.parse(dataElement.textContent);
    } catch {
        return;
    }

    const normalize = (value) => String(value).normalize("NFKC").toLowerCase();

    const searchTextById = new Map(
        catalog.map((test) => [
            String(test.id),
            normalize([test.code, test.name, ...test.aliases].join(" ")),
        ])
    );

    const originalOptions = Array.from(select.options, (option) => ({
        value: option.value,
        label: option.textContent,
        disabled: option.disabled,
    }));

    function updateOptions() {
        const selectedValue = select.value;
        const terms = normalize(input.value).trim().split(/\s+/).filter(Boolean);
        const fragment = document.createDocumentFragment();

        let matchCount = 0;
        let selectedOutsideSearch = false;

        for (const option of originalOptions) {
            const isPlaceholder = option.value === "";
            const searchText = searchTextById.get(option.value)
                ?? normalize(option.label);

            const matches = !isPlaceholder
                && terms.every((term) => searchText.includes(term));

            const isSelected = option.value === selectedValue;

            if (matches) {
                matchCount += 1;
            }

            if (!isPlaceholder && isSelected && !matches) {
                selectedOutsideSearch = true;
            }

            if (isPlaceholder || matches || isSelected) {
                const element = document.createElement("option");
                element.value = option.value;
                element.textContent = option.label;
                element.disabled = option.disabled;
                element.selected = isSelected;
                fragment.appendChild(element);
            }
        }

        select.replaceChildren(fragment);
        select.value = selectedValue;

        const message = matchCount === 0
            ? "No matching tests."
            : `${matchCount} matching test(s).`;

        status.textContent = selectedOutsideSearch
            ? `${message} Your current selection is also shown and has not changed.`
            : message;
    }

    input.addEventListener("input", updateOptions);
    select.addEventListener("change", updateOptions);

    // Prevent Enter in the search box from submitting any surrounding form.
    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
        }
    });

    panel.hidden = false;
    updateOptions();
})();
