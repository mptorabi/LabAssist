/* Pure search helpers. No networking, storage, unit inference or automatic selection. */
(function (root) {
    "use strict";
    const normalize = (value) => String(value ?? "").normalize("NFKC").toLowerCase()
        .replace(/[_\-—–()/,]+/g, " ").replace(/\s+/g, " ").trim();
    function score(test, query) {
        const q = normalize(query);
        if (!q) return 3;
        const names = [test.code, test.name, ...(test.aliases ?? [])].map(normalize);
        if (names.some((name) => name === q)) return 0;
        if (names.some((name) => name.startsWith(q))) return 1;
        const text = names.join(" ");
        const terms = q.split(" ");
        if (!terms.every((term) => text.includes(term))) return Infinity;
        const words = text.split(" ");
        return terms.every((term) => words.some((word) => word.startsWith(term))) ? 2 : 3;
    }
    const api = {normalize, score};
    if (typeof module !== "undefined" && module.exports) module.exports = api;
    else root.LabAssistCatalog = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
