(() => {
    "use strict";

    const panel = document.getElementById("lab-test-search-panel");
    const input = document.getElementById("lab-test-search");
    const status = document.getElementById("lab-test-search-status");
    const select = document.getElementById("id_lab_test");
    const dataElement = document.getElementById("lab-test-search-data");
    const categorySelect = document.getElementById("lab-test-category");

    if (
        !panel || !input || !status || !select
        || !dataElement || !categorySelect
    ) {
        return;
    }

    const search = globalThis.LabAssistCatalog;
    if (!search) return;

    let catalog;

    try {
        catalog = JSON.parse(dataElement.textContent);
    } catch {
        return;
    }

    const testsById = new Map(catalog.map((test) => [String(test.id), test]));
    const categoryByTestId = new Map(
        catalog.map((test) => [
            String(test.id),
            String(test.category_id ?? ""),
        ])
    );

    const categoriesById = new Map();

    for (const test of catalog) {
        const categoryId = String(test.category_id ?? "");

        if (categoryId !== "") {
            categoriesById.set(categoryId, test.category_name);
        }
    }

    const sortedCategories = Array.from(categoriesById.entries())
        .sort((a, b) => a[1].localeCompare(b[1], "en"));

    for (const [id, name] of sortedCategories) {
        const option = document.createElement("option");
        option.value = id;
        option.textContent = name;
        categorySelect.appendChild(option);
    }
    const originalOptions = Array.from(select.options, (option) => ({
        value: option.value,
        label: option.textContent,
        disabled: option.disabled,
    }));

    function updateOptions() {
        const selectedValue = select.value;
        const fragment = document.createDocumentFragment();
        // Stable ranking: exact code/name/alias, prefix, word prefix, substring.
        // The current selection is retained even outside the search/category.
        const rankedOptions = originalOptions.map((option, index) => ({
            ...option, index,
            score: search.score(testsById.get(option.value) ?? {
                code: "", name: option.label, aliases: [],
            }, input.value),
        })).sort((a, b) => {
            if (a.value === "") return -1;
            if (b.value === "") return 1;
            return (a.score - b.score) || (a.index - b.index);
        });

        let matchCount = 0;
        let selectedOutsideSearch = false;

        for (const option of rankedOptions) {
            const isPlaceholder = option.value === "";

            const categoryId = categoryByTestId.get(option.value) ?? "";
            const selectedCategory = categorySelect.value;

            const matchesCategory = selectedCategory === ""
                || (
                    selectedCategory === "uncategorized"
                        ? categoryId === ""
                        : categoryId === selectedCategory
                );

            const matches = !isPlaceholder
                && matchesCategory
                && Number.isFinite(option.score);

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
    categorySelect.addEventListener("change", updateOptions);
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