import output from "./output.json" with { type: "json" };

/**
 * @typedef {typeof output.stalled_dossiers[0]} Bill
 * @typedef {{bill: Bill, liElement: HTMLLIElement}[]} BillsMap
 */

//#region HTML Elements

const houses = /** @type {NodeListOf<HTMLInputElement>} */ (
  document.querySelectorAll('input[name="house"]')
);
const title = /** @type {HTMLHeadingElement} */ (
  document.getElementById("title")
);
const search = /** @type {HTMLInputElement} */ (
  document.querySelector('input[name="search"]')
);
const showFilters = /** @type {HTMLInputElement} */ (
  document.querySelector('input[name="show-filters"]')
);
const filters = /** @type {HTMLFormElement} */ (
  document.getElementById("filters")
);
const sorts = /** @type {NodeListOf<HTMLInputElement>} */ (
  document.querySelectorAll('input[name="sort"]')
);
const minWaitTimeLabel = /** @type {HTMLLabelElement} */ (
  document.getElementById("min-wait-time-label")
);
const minWaitTime = /** @type {HTMLInputElement} */ (
  document.querySelector('input[name="min-wait-time"]')
);
const lapsedBills = /** @type {HTMLInputElement} */ (
  document.querySelector('input[name="lapsed-bills"]')
);
const readings = /** @type {HTMLFieldSetElement} */ (
  document.getElementById("readings")
);
const procedures = /** @type {HTMLFieldSetElement} */ (
  document.getElementById("procedures")
);
const list = /** @type {HTMLOListElement} */ (document.getElementById("list"));
const lastUpdated = /** @type {HTMLTimeElement} */ (
  document.getElementById("last-updated")
);

//#endregion

//#region Utilities

/**
 * Normalizes a string by trimming whitespace, converting to lowercase and removing accents.
 * @param {string} str
 * @param {boolean} removeWhitespace
 * @returns {string}
 */
function normalizeString(str, removeWhitespace = false) {
  let normalizedString = str
    .trim()
    .toLocaleLowerCase("fr-FR")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "");
  if (removeWhitespace) {
    normalizedString = normalizedString.replace(/\s+/g, "");
  }
  return normalizedString;
}

/**
 * Formats a number as an ordinal in French, with an optional HTML superscript for the suffix.
 * @param {number} n
 * @param {boolean} html
 * @returns {string}
 */
function formatOrdinals(n, html = false) {
  const pr = new Intl.PluralRules("fr-FR", { type: "ordinal" });
  const suffixes = new Map([
    ["one", "ère"],
    ["other", "ème"],
  ]);
  const rule = pr.select(n);
  const suffix = suffixes.get(rule);
  return `${n}${html ? /*html*/ `<sup>${suffix}</sup>` : suffix}`;
}

/**
 * Formats a date as a localized string in French, with an optional time component.
 * @param {string | number | Date} value
 * @param {boolean} time
 * @returns {string}
 */
function formatDate(value, time = false) {
  return new Date(value).toLocaleDateString("fr-FR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    ...(time ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
}

//#endregion

/**
 * @param {HTMLFieldSetElement} fieldsetElement
 * @param {keyof Bill} property
 * @returns {string[]}
 */
function getPropertyFilterCheckedValues(fieldsetElement, property) {
  const checkedValues = [
    ...fieldsetElement.querySelectorAll(`input[name="${property}"]`),
  ]
    .filter((e) => {
      const input = /** @type {HTMLInputElement} */ (e);
      return input.checked;
    })
    .map((e) => {
      const input = /** @type {HTMLInputElement} */ (e);
      return input.value;
    });
  return checkedValues;
}

/**
 * @param {Bill} bill
 * @returns {string}
 */
function getStalledSinceHtml(bill) {
  const stalledSinceDate = formatDate(bill.stalled_since);
  const filingCount = bill.steps.filter(
    (step) => step.house === bill.stalled_by && step.reading === bill.reading,
  ).length;
  const latestFilingDate = formatDate(
    bill.steps[bill.steps.length - 1].filing_date,
  );
  return `Depuis le ${stalledSinceDate}${filingCount > 1 ? /*html*/ ` <span class="pico-color-secondary">(redéposé le ${latestFilingDate})</span>` : ""}`;
}

/**
 * @param {string} reading
 * @param {boolean} html
 * @returns {string}
 */
function getReadingString(reading, html = false) {
  if (/^\d+$/.test(reading)) {
    return `${formatOrdinals(Number(reading), html)} lecture`;
  }
  switch (reading) {
    case "LUNI":
      return "Lecture unique";
    case "NLEC":
      return "Nouvelle lecture";
    case "LDEF":
      return "Lecture définitive";
    default:
      return reading;
  }
}

/**
 * @param {BillsMap} billsMap
 * @param {string} house
 */
function renderTitle(billsMap, house) {
  const text =
    house == "AN"
      ? "Dans les tiroirs de l'Assemblée nationale"
      : "Dans les tiroirs du Sénat";
  const count = billsMap.reduce((count, { liElement }) => {
    return liElement.hidden ? count : count + 1;
  }, 0);
  title.innerHTML = `${text} (${count})`;
}

function renderMinWaitTimeLabel() {
  minWaitTimeLabel.textContent = `En attente depuis au moins : ${minWaitTime.value} mois`;
}

/**
 * @param {HTMLFieldSetElement} fieldsetElement
 * @param {string} legend
 * @param {Bill[]} bills
 * @param {keyof Bill} property
 * @param {(this: HTMLInputElement, ev: Event) => any} inputEventListener
 * @param {(value: any) => string} renderPropertyValue
 * @returns {HTMLInputElement[]}
 */
function renderPropertyFilter(
  fieldsetElement,
  legend,
  bills,
  property,
  inputEventListener,
  renderPropertyValue = (value) => value.toString(),
) {
  const values = [
    ...new Set(
      bills.map((bill) => bill[property]).filter((value) => value != null),
    ),
  ].sort();
  /**
   * @type {HTMLInputElement[]}
   */
  const inputElements = [];
  const labelElements = values.map((value) => {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = property;
    input.id = `${property}-${normalizeString(value.toString(), true)}`;
    input.value = value.toString();
    input.addEventListener("change", inputEventListener);
    inputElements.push(input);
    label.append(input);
    label.insertAdjacentHTML("beforeend", renderPropertyValue(value));
    return label;
  });
  const legendElement = document.createElement("legend");
  legendElement.textContent = legend;
  fieldsetElement.innerHTML = "";
  fieldsetElement.append(legendElement, ...labelElements);
  return inputElements;
}

/**
 * @param {Bill[]} bills
 * @param {string} house
 * @param {string} order
 * @param {boolean} filter
 * @returns {BillsMap}
 */
function renderBills(bills, house, order, filter = true) {
  const billsMap = bills
    .filter((bill) => bill.stalled_by === house)
    .sort((a, b) =>
      order === "newest"
        ? b.stalled_since - a.stalled_since
        : a.stalled_since - b.stalled_since,
    )
    .map((bill) => ({ bill, liElement: document.createElement("li") }));

  for (const { bill, liElement } of billsMap) {
    liElement.id = bill.uid;
    liElement.classList.add("bill");
    if (bill.lapsed) liElement.classList.add("lapsed");
    liElement.innerHTML = /*html*/ `
      <article>
        <header>
          <div role="group">
            <div>${getStalledSinceHtml(bill)}</div>
            <div class="bill-uid">
              <code>${bill.uid}</code>
            </div>
          </div>
        </header>
        <hgroup>
          <h3>${bill.title}</h3>
          <p>${bill.procedure}</p>
          <p>${getReadingString(bill.reading, true)}</p>
        </hgroup>
        ${
          bill.link_AN || bill.link_SN
            ? /*html*/ `
              <footer>
                <small>
                  Dossier législatif :
                  ${bill.link_AN ? /*html*/ `<a class="bill-link" href="${bill.link_AN}" target="_blank" rel="noopener noreferrer">Assemblée nationale</a>` : ""}
                  ${bill.link_SN ? /*html*/ `<a class="bill-link" href="${bill.link_SN}" target="_blank" rel="noopener noreferrer">Sénat</a>` : ""}
                </small>
              </footer>
            `
            : ""
        }
      </article>
    `;
  }

  if (filter) {
    filterBills(billsMap, house);
  } else {
    renderTitle(billsMap, house); // `filterBills` already renders title.
  }

  const fragment = document.createDocumentFragment();
  billsMap.forEach(({ liElement }) => fragment.append(liElement));
  list.innerHTML = "";
  list.append(fragment);

  return billsMap;
}

/**
 * @param {BillsMap} billsMap
 * @param {string} house
 */
function filterBills(billsMap, house) {
  const checkedReadings = getPropertyFilterCheckedValues(readings, "reading");
  const checkedProcedures = getPropertyFilterCheckedValues(
    procedures,
    "procedure",
  );
  const searchQuery =
    search.value && !/^\s*$/.test(search.value)
      ? normalizeString(search.value)
      : null;

  billsMap.forEach(({ bill, liElement }) => {
    liElement.hidden = (() => {
      // Min Wait Time
      if (
        Date.now() - bill.stalled_since <
        Number(minWaitTime.value) * 30 * 24 * 60 * 60 * 1000 // In months.
      ) {
        return true;
      }
      // Lapsed Bills
      if (!lapsedBills.checked && liElement.classList.contains("lapsed")) {
        return true;
      }
      // Property Filters
      if (
        !checkedReadings.includes(bill.reading) ||
        !checkedProcedures.includes(bill.procedure)
      ) {
        return true;
      }
      // Search
      if (searchQuery != null) {
        const reading = getReadingString(bill.reading);
        const matches =
          normalizeString(bill.title).includes(searchQuery) ||
          normalizeString(bill.procedure).includes(searchQuery) ||
          normalizeString(reading).startsWith(searchQuery) ||
          normalizeString(bill.uid).includes(searchQuery) ||
          bill.steps.some((step) =>
            normalizeString(step.uid).includes(searchQuery),
          );
        if (!matches) return true;
      }

      return false;
    })();
  });

  renderTitle(billsMap, house);
}

/**
 * @param {number} timestamp
 */
function renderLastUpdated(timestamp) {
  const date = new Date(timestamp);
  lastUpdated.setAttribute("datetime", date.toISOString());
  lastUpdated.textContent = formatDate(date, true);
}

const readingsInputElements = renderPropertyFilter(
  readings,
  "Lecture :",
  output.stalled_dossiers,
  "reading",
  propertyFilterEventListener,
  (reading) => getReadingString(reading.toString(), true),
);
const proceduresInputElements = renderPropertyFilter(
  procedures,
  "Procédure :",
  output.stalled_dossiers,
  "procedure",
  propertyFilterEventListener,
);

const checkedHouse = [...houses].find((radio) => radio.checked);
const checkedOrder = [...sorts].find((radio) => radio.checked);
showFilters.checked = sessionStorage.getItem("showFiltersChecked") === "true";
const filtersFormData = sessionStorage.getItem("filtersFormData");
if (filtersFormData) {
  for (const [name, value] of JSON.parse(filtersFormData)) {
    const controls = filters.elements[name];
    if (controls instanceof RadioNodeList) {
      const input = [...controls].find(
        (input) => input.value === value && input instanceof HTMLInputElement,
      );
      if (input) input.checked = true;
    } else if (controls instanceof HTMLInputElement) {
      controls.value = value;
    }
  }
} else {
  readingsInputElements.forEach((e) => e.setAttribute("checked", "true"));
  proceduresInputElements.forEach((e) => e.setAttribute("checked", "true"));
}

let currentHouse = checkedHouse?.value ?? "SN";
let currentOrder = checkedOrder?.value ?? "oldest";

let billsMap = renderBills(output.stalled_dossiers, currentHouse, currentOrder);
renderMinWaitTimeLabel();
renderLastUpdated(output.generated_at);
filters.style.display = showFilters.checked ? "block" : "none";

houses.forEach((radio) =>
  radio.addEventListener("change", (e) => {
    const input = /** @type {HTMLInputElement} */ (e.target);
    currentHouse = input.value;
    billsMap = renderBills(output.stalled_dossiers, currentHouse, currentOrder);
  }),
);

search.addEventListener("input", () => {
  filterBills(billsMap, currentHouse);
});

showFilters.addEventListener("change", (e) => {
  const input = /** @type {HTMLInputElement} */ (e.target);
  filters.style.display = input.checked ? "block" : "none";
});

sorts.forEach((radio) =>
  radio.addEventListener("change", (e) => {
    const input = /** @type {HTMLInputElement} */ (e.target);
    currentOrder = input.value;
    billsMap = renderBills(output.stalled_dossiers, currentHouse, currentOrder);
  }),
);

minWaitTime.addEventListener("input", () => {
  renderMinWaitTimeLabel();
  filterBills(billsMap, currentHouse);
});

lapsedBills.addEventListener("change", () => {
  filterBills(billsMap, currentHouse);
});

function propertyFilterEventListener() {
  filterBills(billsMap, currentHouse);
}

window.addEventListener("beforeunload", () => {
  const filtersFormData = [...new FormData(filters).entries()];
  sessionStorage.setItem("filtersFormData", JSON.stringify(filtersFormData));
  sessionStorage.setItem(
    "showFiltersChecked",
    JSON.stringify(showFilters.checked),
  );
});
