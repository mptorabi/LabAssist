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

    const unitInput = document.getElementById("id_unit");

    if (unitInput) {
        const unitsByTestId = new Map(
            catalog.map((test) => [
                String(test.id),
                test.units ?? [],
            ])
        );

        const unitSuggestions = document.createElement("datalist");
        unitSuggestions.id = "lab-unit-suggestions";

        const unitHelp = document.createElement("p");
        unitHelp.id = "lab-unit-suggestions-help";
        unitHelp.setAttribute("role", "status");
        unitHelp.setAttribute("aria-live", "polite");

        unitInput.setAttribute("list", unitSuggestions.id);
        unitInput.setAttribute("autocomplete", "off");

        const describedBy = [
            unitInput.getAttribute("aria-describedby"),
            unitHelp.id,
        ].filter(Boolean).join(" ");

        unitInput.setAttribute("aria-describedby", describedBy);

        const unitContainer = unitInput.closest("p") ?? unitInput;
        unitContainer.after(unitSuggestions, unitHelp);

        function updateUnitSuggestions(testChanged = false) {
            const units = unitsByTestId.get(select.value) ?? [];
            const fragment = document.createDocumentFragment();

            for (const symbol of units) {
                const option = document.createElement("option");
                option.value = symbol;
                fragment.appendChild(option);
            }

            unitSuggestions.replaceChildren(fragment);

            let message;

            if (!select.value) {
                message = "Select a lab test to see suggested units.";
            } else if (units.length === 0) {
                message = "No suggested units are available for this test.";
            } else {
                message = `Suggested units: ${units.join(", ")}.`;
            }

            message += (
                " Use only the unit printed on the report. "
                + "You may enter another unit or leave it blank."
            );

            if (testChanged && unitInput.value.trim() !== "") {
                message += (
                    " The test changed; your entered unit was kept. "
                    + "Check that it matches the report for this test."
                );
            }

            unitHelp.textContent = message;
        }

        select.addEventListener("change", () => {
            updateUnitSuggestions(true);
        });

        updateUnitSuggestions();
    }

    panel.hidden = false;
    updateOptions();
})();