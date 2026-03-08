/**
 * System list view — in-DOM table, filters, column dropdown, SSE, signals expand.
 * Used by feature tree editor when a system list pane is selected. No iframe.
 * Expects #system-list-panel in the document. Call SystemListView.loadPane(tabKey) to show a pane.
 */
(function () {
  "use strict";

  const CHANNEL_MAP_KEY = "channel map";
  const DISCONNECT_MAP_KEY = "disconnect map";
  const CIRCUITS_LIST_KEY = "circuits list";
  const BOM_KEY = "bom";
  const INSTANCES_LIST_KEY = "instances list";
  const POST_HARNESS_INSTANCES_LIST_KEY = "post harness instances list";
  const CHANNEL_TYPE_HEADERS = ["from_channel_type", "to_channel_type", "A-side_device_channel_type", "B-side_device_channel_type"];

  let panel = null;
  let currentTabKey = null;
  let instancesListSourceKey = INSTANCES_LIST_KEY;
  const fileStates = {};
  let useHumanReadableChannelTypes = false;
  let channelTypeCompatibleCache = {};
  let channelTypeDisplayCache = {};
  let sseEventSource = null;
  let onStateChange = null;
  let ddPending = { sortDir: 0, checked: null };
  let ddLabel = null;
  let ddColIdx = -1;
  let ddAllValues = [];
  let ddSignalsWrap = null;
  let lastRenderedCount = 0;
  let lastTotal = 0;

  function getPanel() {
    if (panel) return panel;
    panel = document.getElementById("system-list-panel");
    return panel;
  }

  function getDataKey() {
    return currentTabKey === INSTANCES_LIST_KEY ? instancesListSourceKey : currentTabKey;
  }

  function getState(key) {
    if (!fileStates[key]) {
      fileStates[key] = { rows: [], headers: [], sortCol: -1, sortDir: 1, colFilters: [], search: "" };
    }
    const st = fileStates[key];
    while (st.colFilters.length < st.headers.length) st.colFilters.push(null);
    return st;
  }

  function parseText(text) {
    if (!text || !String(text).trim()) return { headers: [], rows: [] };
    const sep = text.includes("\t") ? "\t" : ",";
    const lines = String(text).trim().split(/\r?\n/);
    const headers = lines[0].split(sep).map((h) => h.trim());
    const rows = lines.slice(1).filter((l) => l.trim()).map((l) => l.split(sep).map((c) => c.trim()));
    return { headers, rows };
  }

  function applyFileContent(key, text) {
    const st = getState(key);
    const { headers, rows } = parseText(text);
    const sameHeaders = headers.length === st.headers.length && headers.every((h, i) => h === st.headers[i]);
    if (!sameHeaders) {
      st.colFilters = headers.map(() => null);
      st.sortCol = -1;
    } else {
      while (st.colFilters.length < headers.length) st.colFilters.push(null);
    }
    st.headers = headers;
    st.rows = rows;
  }

  function fetchChannelTypeDisplays(typeStrings) {
    if (!typeStrings || !typeStrings.length) return Promise.resolve({});
    const url = "/api/channel-type-display?" + typeStrings.map((t) => "type=" + encodeURIComponent(t)).join("&");
    return fetch(url)
      .then((r) => r.json())
      .then((map) => {
        Object.assign(channelTypeDisplayCache, map);
        return map;
      })
      .catch(() => ({}));
  }

  function getChannelTypeDisplay(raw) {
    if (!raw || !useHumanReadableChannelTypes) return raw ?? "";
    const key = (typeof raw === "string" ? raw.trim() : String(raw));
    return (channelTypeDisplayCache[key] ?? key) || "";
  }

  function isChannelTypeColumn(headerName) {
    return CHANNEL_TYPE_HEADERS.includes(headerName);
  }

  function channelColIdx(st, name) {
    const i = st.headers.indexOf(name);
    return i >= 0 ? i : -1;
  }

  function applyChannelFilters(st, rows) {
    const p = getPanel();
    if (!p) return rows;
    const unmapped = p.querySelector("#sl-ch-unmapped");
    if (unmapped && !unmapped.checked) {
      const toDevCol = channelColIdx(st, "to_device_refdes");
      const toChanCol = channelColIdx(st, "to_device_channel_id");
      const filled = (v) => v !== undefined && v !== null && String(v).trim() !== "";
      rows = rows.filter((r) => filled(r[toDevCol]) && filled(r[toChanCol]));
    }
    const netCol = channelColIdx(st, "merged_net");
    const fromDevCol = channelColIdx(st, "from_device_refdes");
    const fromChanCol = channelColIdx(st, "from_device_channel_id");
    const toDevCol = channelColIdx(st, "to_device_refdes");
    const toChanCol = channelColIdx(st, "to_device_channel_id");
    const fromTypeCol = channelColIdx(st, "from_channel_type");
    const netEl = p.querySelector("#sl-ch-net");
    const devAEl = p.querySelector("#sl-ch-dev-a");
    const chanAEl = p.querySelector("#sl-ch-chan-a");
    const devBEl = p.querySelector("#sl-ch-dev-b");
    const chanBEl = p.querySelector("#sl-ch-chan-b");
    const netVal = netEl ? netEl.value : "";
    const devAVal = devAEl ? devAEl.value : "";
    const chanAVal = chanAEl ? chanAEl.value : "";
    const devBVal = devBEl ? devBEl.value : "";
    const chanBVal = chanBEl ? chanBEl.value : "";
    if (netVal && netCol >= 0) rows = rows.filter((r) => (r[netCol] ?? "").trim() === netVal);
    const fromDev = (r) => (r[fromDevCol] ?? "").trim();
    const toDev = (r) => (r[toDevCol] ?? "").trim();
    const fromChan = (r) => (r[fromChanCol] ?? "").trim();
    const toChan = (r) => (r[toChanCol] ?? "").trim();
    const pairOnFrom = (r, dev, chan) => (dev === "" || fromDev(r) === dev) && (chan === "" || fromChan(r) === chan);
    const pairOnTo = (r, dev, chan) => (dev === "" || toDev(r) === dev) && (chan === "" || toChan(r) === chan);
    const oneEndMatches = (r, dev, chan) => pairOnFrom(r, dev, chan) || pairOnTo(r, dev, chan);
    const pair1Set = devAVal !== "" || chanAVal !== "";
    const pair2Set = devBVal !== "" || chanBVal !== "";
    if (pair1Set && pair2Set) {
      rows = rows.filter(
        (r) =>
          (pairOnFrom(r, devAVal, chanAVal) && pairOnTo(r, devBVal, chanBVal)) ||
          (pairOnFrom(r, devBVal, chanBVal) && pairOnTo(r, devAVal, chanAVal))
      );
    } else if (pair1Set) {
      rows = rows.filter((r) => oneEndMatches(r, devAVal, chanAVal));
    } else if (pair2Set) {
      rows = rows.filter((r) => oneEndMatches(r, devBVal, chanBVal));
    }
    const typeRelEl = p.querySelector("#sl-ch-type-rel");
    const typeValEl = p.querySelector("#sl-ch-type-val");
    const typeRel = typeRelEl ? typeRelEl.value : "any";
    const typeVal = typeValEl ? typeValEl.value : "";
    if (typeRel === "is_or_compatible" && typeVal && fromTypeCol >= 0) {
      const rowType = (r) => (r[fromTypeCol] ?? "").trim();
      const allowed = channelTypeCompatibleCache[typeVal];
      if (allowed && allowed.size) {
        rows = rows.filter((r) => allowed.has(rowType(r)));
      } else {
        rows = rows.filter((r) => rowType(r) === typeVal);
      }
    }
    return rows;
  }

  function applyDisconnectFilters(st, rows) {
    const p = getPanel();
    if (!p) return rows;
    const avail = p.querySelector("#sl-dc-available");
    if (avail && !avail.checked) {
      const aDevCol = channelColIdx(st, "A-side_device_refdes");
      const bDevCol = channelColIdx(st, "B-side_device_refdes");
      const filled = (v) => v !== undefined && v !== null && String(v).trim() !== "";
      rows = rows.filter((r) => filled(r[aDevCol]) && filled(r[bDevCol]));
    }
    const discCol = channelColIdx(st, "disconnect_refdes");
    const discChanCol = channelColIdx(st, "disconnect_channel_id");
    const aDevCol = channelColIdx(st, "A-side_device_refdes");
    const aChanCol = channelColIdx(st, "A-side_device_channel_id");
    const bDevCol = channelColIdx(st, "B-side_device_refdes");
    const bChanCol = channelColIdx(st, "B-side_device_channel_id");
    const aTypeCol = channelColIdx(st, "A-side_device_channel_type");
    const bTypeCol = channelColIdx(st, "B-side_device_channel_type");
    const discVal = p.querySelector("#sl-dc-disc")?.value ?? "";
    const discChanVal = p.querySelector("#sl-dc-disc-chan")?.value ?? "";
    if (discCol >= 0 && discVal) rows = rows.filter((r) => (r[discCol] ?? "").trim() === discVal);
    if (discChanCol >= 0 && discChanVal) rows = rows.filter((r) => (r[discChanCol] ?? "").trim() === discChanVal);
    const devAVal = p.querySelector("#sl-dc-dev-a")?.value ?? "";
    const chanAVal = p.querySelector("#sl-dc-chan-a")?.value ?? "";
    const devBVal = p.querySelector("#sl-dc-dev-b")?.value ?? "";
    const chanBVal = p.querySelector("#sl-dc-chan-b")?.value ?? "";
    const aDev = (r) => (r[aDevCol] ?? "").trim();
    const bDev = (r) => (r[bDevCol] ?? "").trim();
    const aChan = (r) => (r[aChanCol] ?? "").trim();
    const bChan = (r) => (r[bChanCol] ?? "").trim();
    const pairOnA = (r, dev, chan) => (dev === "" || aDev(r) === dev) && (chan === "" || aChan(r) === chan);
    const pairOnB = (r, dev, chan) => (dev === "" || bDev(r) === dev) && (chan === "" || bChan(r) === chan);
    const pair1Set = devAVal !== "" || chanAVal !== "";
    const pair2Set = devBVal !== "" || chanBVal !== "";
    if (pair1Set && pair2Set) {
      rows = rows.filter(
        (r) =>
          (pairOnA(r, devAVal, chanAVal) && pairOnB(r, devBVal, chanBVal)) ||
          (pairOnA(r, devBVal, chanBVal) && pairOnB(r, devAVal, chanAVal))
      );
    } else if (pair1Set) {
      rows = rows.filter((r) => pairOnA(r, devAVal, chanAVal) || pairOnB(r, devAVal, chanAVal));
    } else if (pair2Set) {
      rows = rows.filter((r) => pairOnA(r, devBVal, chanBVal) || pairOnB(r, devBVal, chanBVal));
    }
    const typeRelEl = p.querySelector("#sl-dc-type-rel");
    const typeValEl = p.querySelector("#sl-dc-type-val");
    const typeRel = typeRelEl ? typeRelEl.value : "any";
    const typeVal = typeValEl ? typeValEl.value : "";
    if (typeRel === "is_or_compatible" && typeVal && (aTypeCol >= 0 || bTypeCol >= 0)) {
      const rowTypeA = (r) => (r[aTypeCol] ?? "").trim();
      const rowTypeB = (r) => (r[bTypeCol] ?? "").trim();
      const allowed = channelTypeCompatibleCache[typeVal];
      if (allowed && allowed.size) {
        rows = rows.filter((r) => allowed.has(rowTypeA(r)) || allowed.has(rowTypeB(r)));
      } else {
        rows = rows.filter((r) => rowTypeA(r) === typeVal || rowTypeB(r) === typeVal);
      }
    }
    return rows;
  }

  function applyCircuitsFilters(st, rows) {
    const p = getPanel();
    if (!p) return rows;
    const fromDevCol = channelColIdx(st, "from_side_device_refdes");
    const fromChanCol = channelColIdx(st, "from_side_device_chname");
    const fromConnCol = channelColIdx(st, "net_from_connector_name");
    const toDevCol = channelColIdx(st, "to_side_device_refdes");
    const toChanCol = channelColIdx(st, "to_side_device_chname");
    const toConnCol = channelColIdx(st, "net_to_connector_name");
    const fromTypeCol = channelColIdx(st, "from_channel_type");
    const toTypeCol = channelColIdx(st, "to_channel_type");
    const signalCol = channelColIdx(st, "signal");
    const fromDev = (r) => (r[fromDevCol] ?? "").trim();
    const toDev = (r) => (r[toDevCol] ?? "").trim();
    const fromChan = (r) => (r[fromChanCol] ?? "").trim();
    const toChan = (r) => (r[toChanCol] ?? "").trim();
    const fromConn = (r) => (r[fromConnCol] ?? "").trim();
    const toConn = (r) => (r[toConnCol] ?? "").trim();
    const devAVal = p.querySelector("#sl-ci-dev-a")?.value ?? "";
    const chanAVal = p.querySelector("#sl-ci-chan-a")?.value ?? "";
    const connAVal = p.querySelector("#sl-ci-conn-a")?.value ?? "";
    const devBVal = p.querySelector("#sl-ci-dev-b")?.value ?? "";
    const chanBVal = p.querySelector("#sl-ci-chan-b")?.value ?? "";
    const connBVal = p.querySelector("#sl-ci-conn-b")?.value ?? "";
    const fromMatches = (r, d, c, conn) =>
      (d === "" || fromDev(r) === d) && (c === "" || fromChan(r) === c) && (conn === "" || fromConn(r) === conn);
    const toMatches = (r, d, c, conn) =>
      (d === "" || toDev(r) === d) && (c === "" || toChan(r) === c) && (conn === "" || toConn(r) === conn);
    const pair1Set = devAVal !== "" || chanAVal !== "" || connAVal !== "";
    const pair2Set = devBVal !== "" || chanBVal !== "" || connBVal !== "";
    if (pair1Set && pair2Set) {
      rows = rows.filter(
        (r) =>
          (fromMatches(r, devAVal, chanAVal, connAVal) && toMatches(r, devBVal, chanBVal, connBVal)) ||
          (fromMatches(r, devBVal, chanBVal, connBVal) && toMatches(r, devAVal, chanAVal, connAVal))
      );
    } else if (pair1Set) {
      rows = rows.filter(
        (r) => fromMatches(r, devAVal, chanAVal, connAVal) || toMatches(r, devAVal, chanAVal, connAVal)
      );
    } else if (pair2Set) {
      rows = rows.filter(
        (r) => fromMatches(r, devBVal, chanBVal, connBVal) || toMatches(r, devBVal, chanBVal, connBVal)
      );
    }
    const typeRelEl = p.querySelector("#sl-ci-type-rel");
    const typeValEl = p.querySelector("#sl-ci-type-val");
    const typeRel = typeRelEl ? typeRelEl.value : "any";
    const typeVal = typeValEl ? typeValEl.value : "";
    if (typeRel === "is_or_compatible" && typeVal && (fromTypeCol >= 0 || toTypeCol >= 0)) {
      const rowTypeFrom = (r) => (r[fromTypeCol] ?? "").trim();
      const rowTypeTo = (r) => (r[toTypeCol] ?? "").trim();
      const allowed = channelTypeCompatibleCache[typeVal];
      if (allowed && allowed.size) {
        rows = rows.filter((r) => allowed.has(rowTypeFrom(r)) || allowed.has(rowTypeTo(r)));
      } else {
        rows = rows.filter((r) => rowTypeFrom(r) === typeVal || rowTypeTo(r) === typeVal);
      }
    }
    const signalVal = p.querySelector("#sl-ci-signal")?.value ?? "";
    if (signalVal && signalCol >= 0) rows = rows.filter((r) => (r[signalCol] ?? "").trim() === signalVal);
    return rows;
  }

  function buildPanelDOM() {
    const p = getPanel();
    if (!p || p.querySelector("#sl-table-wrap")) return;
    p.innerHTML = "";
    p.style.display = "flex";
    p.style.flexDirection = "column";
    p.style.minHeight = "0";
    p.style.overflow = "hidden";

    const headersWrap = document.createElement("div");
    headersWrap.id = "sl-headers-wrap";
    headersWrap.className = "sl-headers";

    const instHeader = document.createElement("div");
    instHeader.id = "sl-instances-header";
    instHeader.className = "sl-viewer-header";
    instHeader.innerHTML = `
      <p class="sl-channel-sentence">Show:</p>
      <div class="sl-instances-options">
        <label class="sl-instances-option selected" data-value="instances list">
          <input type="radio" name="sl-instances-source" value="instances list" checked>
          <span>Instances list</span>
        </label>
        <label class="sl-instances-option" data-value="post harness instances list">
          <input type="radio" name="sl-instances-source" value="post harness instances list">
          <span>Post harness instances list</span>
        </label>
      </div>`;
    headersWrap.appendChild(instHeader);

    const chHeader = document.createElement("div");
    chHeader.id = "sl-channel-header";
    chHeader.className = "sl-viewer-header";
    chHeader.innerHTML = `
      <div class="sl-channel-toggle"><input type="checkbox" id="sl-ch-unmapped" checked><label for="sl-ch-unmapped">Show unmapped channels</label></div>
      <p class="sl-channel-sentence">Show me channels in <select id="sl-ch-net"><option value="">any merged net</option></select> that connect <select id="sl-ch-chan-a"><option value="">any channel</option></select> of <select id="sl-ch-dev-a"><option value="">any device</option></select> to <select id="sl-ch-chan-b"><option value="">any channel</option></select> of <select id="sl-ch-dev-b"><option value="">any device</option></select>.</p>
      <p class="sl-channel-type-row">Channel type <select id="sl-ch-type-rel"><option value="any">is any</option><option value="is_or_compatible">is or is compatible with</option></select> <select id="sl-ch-type-val" style="display:none;"><option value="">—</option></select> <button type="button" class="sl-channel-clear" id="sl-ch-clear">Clear</button></p>`;
    headersWrap.appendChild(chHeader);

    const dcHeader = document.createElement("div");
    dcHeader.id = "sl-disconnect-header";
    dcHeader.className = "sl-viewer-header";
    dcHeader.innerHTML = `
      <div class="sl-channel-toggle"><input type="checkbox" id="sl-dc-available" checked><label for="sl-dc-available">Show available disconnect channels</label></div>
      <p class="sl-channel-sentence">Show me channels that pass through <select id="sl-dc-disc-chan"><option value="">any channel</option></select> of <select id="sl-dc-disc"><option value="">any disconnect</option></select> that connect <select id="sl-dc-chan-a"><option value="">any channel</option></select> of <select id="sl-dc-dev-a"><option value="">any device</option></select> to <select id="sl-dc-chan-b"><option value="">any channel</option></select> of <select id="sl-dc-dev-b"><option value="">any device</option></select>.</p>
      <p class="sl-channel-type-row">Channel type <select id="sl-dc-type-rel"><option value="any">is any</option><option value="is_or_compatible">is or is compatible with</option></select> <select id="sl-dc-type-val" style="display:none;"><option value="">—</option></select> <button type="button" class="sl-channel-clear" id="sl-dc-clear">Clear</button></p>`;
    headersWrap.appendChild(dcHeader);

    const ciHeader = document.createElement("div");
    ciHeader.id = "sl-circuits-header";
    ciHeader.className = "sl-viewer-header";
    ciHeader.innerHTML = `
      <p class="sl-channel-sentence">Show me circuits that connect <select id="sl-ci-chan-a"><option value="">any channel</option></select> on <select id="sl-ci-conn-a"><option value="">any connector</option></select> of <select id="sl-ci-dev-a"><option value="">any device</option></select> to <select id="sl-ci-chan-b"><option value="">any channel</option></select> on <select id="sl-ci-conn-b"><option value="">any connector</option></select> of <select id="sl-ci-dev-b"><option value="">any device</option></select>.</p>
      <p class="sl-channel-type-row">Channel type <select id="sl-ci-type-rel"><option value="any">is any</option><option value="is_or_compatible">is or is compatible with</option></select> <select id="sl-ci-type-val" style="display:none;"><option value="">—</option></select> and signal is <select id="sl-ci-signal"><option value="">any</option></select> <button type="button" class="sl-channel-clear" id="sl-ci-clear">Clear</button></p>`;
    headersWrap.appendChild(ciHeader);

    const channelTypeWrap = document.createElement("div");
    channelTypeWrap.className = "sl-channel-type-wrap";
    channelTypeWrap.innerHTML = `
      <label><input type="checkbox" id="sl-channel-type-human"> <span>Channel types: human-readable</span></label>`;
    headersWrap.appendChild(channelTypeWrap);

    p.appendChild(headersWrap);

    const tableWrap = document.createElement("div");
    tableWrap.id = "sl-table-wrap";
    tableWrap.className = "sl-table-wrap";
    const empty = document.createElement("div");
    empty.id = "sl-empty";
    empty.className = "sl-empty";
    empty.textContent = "Loading…";
    const table = document.createElement("table");
    table.id = "sl-table";
    table.innerHTML = "<thead id=\"sl-thead\"></thead><tbody id=\"sl-tbody\"></tbody>";
    tableWrap.appendChild(empty);
    tableWrap.appendChild(table);
    p.appendChild(tableWrap);

    const dropdown = document.createElement("div");
    dropdown.id = "sl-col-dropdown";
    dropdown.className = "sl-col-dropdown";
    dropdown.innerHTML = `
      <div class="sl-dd-search"><input type="text" id="sl-dd-search" placeholder="Search values…"></div>
      <div class="sl-dd-sort">
        <button id="sl-dd-asc">↑ A→Z</button>
        <button id="sl-dd-desc">↓ Z→A</button>
        <button id="sl-dd-nosort">✕ None</button>
      </div>
      <div class="sl-dd-list" id="sl-dd-list"></div>
      <div class="sl-dd-footer">
        <button type="button" class="sl-dd-cancel">Cancel</button>
        <button type="button" class="sl-dd-apply">Apply</button>
      </div>`;
    document.body.appendChild(dropdown);

    const ddSearchEl = document.getElementById("sl-dd-search");
    if (ddSearchEl) ddSearchEl.addEventListener("input", () => renderDDList(ddSearchEl.value));
    dropdown.querySelector("#sl-dd-asc")?.addEventListener("click", () => { ddPending.sortDir = 1; updateDDSortBtns(); });
    dropdown.querySelector("#sl-dd-desc")?.addEventListener("click", () => { ddPending.sortDir = -1; updateDDSortBtns(); });
    dropdown.querySelector("#sl-dd-nosort")?.addEventListener("click", () => { ddPending.sortDir = 0; updateDDSortBtns(); });
    dropdown.querySelector(".sl-dd-apply")?.addEventListener("click", ddApply);
    dropdown.querySelector(".sl-dd-cancel")?.addEventListener("click", () => dropdown.classList.remove("open"));

    function onChannelFilterChange() {
      if (currentTabKey === CHANNEL_MAP_KEY) renderTable();
      const typeRel = p.querySelector("#sl-ch-type-rel")?.value;
      if (typeRel === "is_or_compatible") {
        const v = p.querySelector("#sl-ch-type-val")?.value;
        if (v) fetchChannelTypeCompatible(v);
      }
      notifyState();
    }
    p.querySelector("#sl-ch-clear")?.addEventListener("click", () => {
      p.querySelector("#sl-ch-unmapped").checked = true;
      ["#sl-ch-net", "#sl-ch-chan-a", "#sl-ch-dev-a", "#sl-ch-chan-b", "#sl-ch-dev-b"].forEach((sel) => { const el = p.querySelector(sel); if (el) el.value = ""; });
      p.querySelector("#sl-ch-type-rel").value = "any";
      const tv = p.querySelector("#sl-ch-type-val"); if (tv) { tv.style.display = "none"; tv.value = ""; }
      if (currentTabKey === CHANNEL_MAP_KEY) { buildChannelDropdowns(); renderTable(); notifyState(); }
    });
    p.querySelector("#sl-ch-unmapped")?.addEventListener("change", onChannelFilterChange);
    ["#sl-ch-net", "#sl-ch-dev-a", "#sl-ch-chan-a", "#sl-ch-dev-b", "#sl-ch-chan-b"].forEach((sel) => {
      p.querySelector(sel)?.addEventListener("change", onChannelFilterChange);
    });
    p.querySelector("#sl-ch-type-rel")?.addEventListener("change", () => {
      const rel = p.querySelector("#sl-ch-type-rel")?.value;
      const tv = p.querySelector("#sl-ch-type-val"); if (tv) tv.style.display = rel === "is_or_compatible" ? "inline-block" : "none";
      onChannelFilterChange();
    });
    p.querySelector("#sl-ch-type-val")?.addEventListener("change", onChannelFilterChange);

    function onDisconnectFilterChange() {
      if (currentTabKey === DISCONNECT_MAP_KEY) renderTable();
      const typeRel = p.querySelector("#sl-dc-type-rel")?.value;
      if (typeRel === "is_or_compatible") { const v = p.querySelector("#sl-dc-type-val")?.value; if (v) fetchChannelTypeCompatible(v); }
      notifyState();
    }
    p.querySelector("#sl-dc-clear")?.addEventListener("click", () => {
      p.querySelector("#sl-dc-available").checked = true;
      ["#sl-dc-disc", "#sl-dc-disc-chan", "#sl-dc-dev-a", "#sl-dc-chan-a", "#sl-dc-dev-b", "#sl-dc-chan-b"].forEach((sel) => { const el = p.querySelector(sel); if (el) el.value = ""; });
      p.querySelector("#sl-dc-type-rel").value = "any";
      const tv = p.querySelector("#sl-dc-type-val"); if (tv) { tv.style.display = "none"; tv.value = ""; }
      if (currentTabKey === DISCONNECT_MAP_KEY) { buildDisconnectDropdowns(); renderTable(); notifyState(); }
    });
    ["#sl-dc-available", "#sl-dc-disc", "#sl-dc-disc-chan", "#sl-dc-dev-a", "#sl-dc-chan-a", "#sl-dc-dev-b", "#sl-dc-chan-b"].forEach((sel) => {
      p.querySelector(sel)?.addEventListener("change", onDisconnectFilterChange);
    });
    p.querySelector("#sl-dc-type-rel")?.addEventListener("change", () => {
      const tv = p.querySelector("#sl-dc-type-val"); if (tv) tv.style.display = p.querySelector("#sl-dc-type-rel")?.value === "is_or_compatible" ? "inline-block" : "none";
      onDisconnectFilterChange();
    });
    p.querySelector("#sl-dc-type-val")?.addEventListener("change", onDisconnectFilterChange);

    function onCircuitsFilterChange() {
      if (currentTabKey === CIRCUITS_LIST_KEY) renderTable();
      const typeRel = p.querySelector("#sl-ci-type-rel")?.value;
      if (typeRel === "is_or_compatible") { const v = p.querySelector("#sl-ci-type-val")?.value; if (v) fetchChannelTypeCompatible(v); }
      notifyState();
    }
    p.querySelector("#sl-ci-clear")?.addEventListener("click", () => {
      ["#sl-ci-chan-a", "#sl-ci-conn-a", "#sl-ci-dev-a", "#sl-ci-chan-b", "#sl-ci-conn-b", "#sl-ci-dev-b", "#sl-ci-type-rel", "#sl-ci-signal"].forEach((sel) => { const el = p.querySelector(sel); if (el) el.value = sel.includes("type") ? "any" : ""; });
      const tv = p.querySelector("#sl-ci-type-val"); if (tv) { tv.style.display = "none"; tv.value = ""; }
      if (currentTabKey === CIRCUITS_LIST_KEY) { buildCircuitsDropdowns(); renderTable(); notifyState(); }
    });
    ["#sl-ci-chan-a", "#sl-ci-conn-a", "#sl-ci-dev-a", "#sl-ci-chan-b", "#sl-ci-conn-b", "#sl-ci-dev-b", "#sl-ci-type-rel", "#sl-ci-type-val", "#sl-ci-signal"].forEach((sel) => {
      p.querySelector(sel)?.addEventListener("change", onCircuitsFilterChange);
    });

    instHeader.querySelectorAll("input[name=sl-instances-source]").forEach((radio) => {
      radio.addEventListener("change", (e) => {
        if (currentTabKey !== INSTANCES_LIST_KEY) return;
        instancesListSourceKey = e.target.value;
        instHeader.querySelectorAll(".sl-instances-option").forEach((opt) => {
          opt.classList.toggle("selected", opt.dataset.value === instancesListSourceKey);
        });
        renderTable();
        notifyState();
      });
    });
    instHeader.querySelectorAll(".sl-instances-option").forEach((opt) => {
      opt.addEventListener("click", (e) => {
        if (e.target.tagName === "INPUT") return;
        opt.querySelector("input").checked = true;
        instancesListSourceKey = opt.dataset.value;
        instHeader.querySelectorAll(".sl-instances-option").forEach((o) => o.classList.toggle("selected", o.dataset.value === instancesListSourceKey));
        renderTable();
        notifyState();
      });
    });

    p.querySelector("#sl-channel-type-human")?.addEventListener("change", () => {
      useHumanReadableChannelTypes = !!p.querySelector("#sl-channel-type-human")?.checked;
      if (currentTabKey === CHANNEL_MAP_KEY) buildChannelDropdowns();
      if (currentTabKey === DISCONNECT_MAP_KEY) buildDisconnectDropdowns();
      if (currentTabKey === CIRCUITS_LIST_KEY) buildCircuitsDropdowns();
      renderTable();
      notifyState();
    });

    tableWrap.addEventListener("click", (e) => {
      const tr = e.target.closest("tr");
      if (!tr || !tr.classList.contains("sl-device-row")) return;
      const refdes = tr.dataset.deviceRefdes;
      if (!refdes) return;
      const detailTr = tr.nextElementSibling;
      if (!detailTr || !detailTr.classList.contains("sl-signals-detail-row")) return;
      p.querySelectorAll("tr.sl-signals-detail-row.expanded").forEach((row) => {
        if (row !== detailTr) row.classList.remove("expanded");
        row.previousElementSibling?.classList?.remove("signals-expanded");
      });
      detailTr.classList.toggle("expanded");
      tr.classList.toggle("signals-expanded", detailTr.classList.contains("expanded"));
      if (!detailTr.classList.contains("expanded")) return;
      const wrap = detailTr.querySelector(".sl-signals-viewer-wrap");
      const placeholder = wrap?.querySelector(".loading");
      if (!placeholder || placeholder.textContent !== "Click row to load signals list") return;
      wrap.innerHTML = "<span class=\"loading\">Loading…</span>";
      fetch("/api/signals-list?device_refdes=" + encodeURIComponent(refdes))
        .then((r) => {
          if (!r.ok) throw new Error(r.status === 404 ? "Signals list not found" : r.statusText);
          return r.text();
        })
        .then((tsv) => renderSignalsTable(detailTr, tsv))
        .catch((err) => {
          const w = detailTr.querySelector(".sl-signals-viewer-wrap");
          if (w) w.innerHTML = "<span class=\"error\">" + (err.message || "Load failed") + "</span>";
        });
    });

    document.addEventListener("click", (e) => {
      if (dropdown && !dropdown.contains(e.target) && !e.target.closest(".sl-th-inner")) dropdown.classList.remove("open");
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") dropdown.classList.remove("open");
    });
  }

  function buildChannelDropdowns() {
    const st = getState(CHANNEL_MAP_KEY);
    if (!st.headers.length) return;
    const p = getPanel();
    if (!p) return;
    const netCol = channelColIdx(st, "merged_net");
    const fromDevCol = channelColIdx(st, "from_device_refdes");
    const fromChanCol = channelColIdx(st, "from_device_channel_id");
    const toDevCol = channelColIdx(st, "to_device_refdes");
    const toChanCol = channelColIdx(st, "to_device_channel_id");
    const fromTypeCol = channelColIdx(st, "from_channel_type");
    function uniques(colIdx) {
      if (colIdx < 0) return [];
      const set = new Set(st.rows.map((r) => (r[colIdx] ?? "").trim()).filter(Boolean));
      return [...set].sort((a, b) => a.localeCompare(b));
    }
    function uniquesEither(colA, colB) {
      const set = new Set();
      if (colA >= 0) st.rows.forEach((r) => { const v = (r[colA] ?? "").trim(); if (v) set.add(v); });
      if (colB >= 0) st.rows.forEach((r) => { const v = (r[colB] ?? "").trim(); if (v) set.add(v); });
      return [...set].sort((a, b) => a.localeCompare(b));
    }
    function fill(id, options, anyLabel) {
      const el = p.querySelector(id);
      if (!el) return;
      const cur = el.value;
      el.innerHTML = "<option value=\"\">" + anyLabel + "</option>";
      options.forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v;
        el.appendChild(opt);
      });
      if (options.includes(cur)) el.value = cur;
    }
    fill("#sl-ch-net", netCol >= 0 ? uniques(netCol) : [], "any merged net");
    fill("#sl-ch-dev-a", uniquesEither(fromDevCol, toDevCol), "any device");
    fill("#sl-ch-chan-a", uniquesEither(fromChanCol, toChanCol), "any channel");
    fill("#sl-ch-dev-b", uniquesEither(fromDevCol, toDevCol), "any device");
    fill("#sl-ch-chan-b", uniquesEither(fromChanCol, toChanCol), "any channel");
    const typeOpts = fromTypeCol >= 0 ? uniques(fromTypeCol) : [];
    const typeEl = p.querySelector("#sl-ch-type-val");
    if (typeEl) {
      typeEl.innerHTML = "<option value=\"\">—</option>";
      typeOpts.forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = useHumanReadableChannelTypes ? (channelTypeDisplayCache[v] ?? v) : v;
        typeEl.appendChild(opt);
      });
    }
    if (useHumanReadableChannelTypes && typeOpts.length) fetchChannelTypeDisplays(typeOpts).then(() => buildChannelDropdowns());
  }

  function buildDisconnectDropdowns() {
    const st = getState(DISCONNECT_MAP_KEY);
    if (!st.headers.length) return;
    const p = getPanel();
    if (!p) return;
    const aDevCol = channelColIdx(st, "A-side_device_refdes");
    const aChanCol = channelColIdx(st, "A-side_device_channel_id");
    const bDevCol = channelColIdx(st, "B-side_device_refdes");
    const bChanCol = channelColIdx(st, "B-side_device_channel_id");
    const discCol = channelColIdx(st, "disconnect_refdes");
    const discChanCol = channelColIdx(st, "disconnect_channel_id");
    function uniques(colIdx) {
      if (colIdx < 0) return [];
      return [...new Set(st.rows.map((r) => (r[colIdx] ?? "").trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    }
    function uniquesEither(colA, colB) {
      const set = new Set();
      if (colA >= 0) st.rows.forEach((r) => { const v = (r[colA] ?? "").trim(); if (v) set.add(v); });
      if (colB >= 0) st.rows.forEach((r) => { const v = (r[colB] ?? "").trim(); if (v) set.add(v); });
      return [...set].sort((a, b) => a.localeCompare(b));
    }
    function fill(id, options, anyLabel) {
      const el = p.querySelector(id);
      if (!el) return;
      const cur = el.value;
      el.innerHTML = "<option value=\"\">" + anyLabel + "</option>";
      options.forEach((v) => { const o = document.createElement("option"); o.value = v; o.textContent = v; el.appendChild(o); });
      if (options.includes(cur)) el.value = cur;
    }
    fill("#sl-dc-disc", uniques(discCol), "any disconnect");
    fill("#sl-dc-disc-chan", uniques(discChanCol), "any channel");
    fill("#sl-dc-dev-a", uniquesEither(aDevCol, bDevCol), "any device");
    fill("#sl-dc-chan-a", uniquesEither(aChanCol, bChanCol), "any channel");
    fill("#sl-dc-dev-b", uniquesEither(aDevCol, bDevCol), "any device");
    fill("#sl-dc-chan-b", uniquesEither(aChanCol, bChanCol), "any channel");
    const typeOpts = uniquesEither(channelColIdx(st, "A-side_device_channel_type"), channelColIdx(st, "B-side_device_channel_type"));
    const typeEl = p.querySelector("#sl-dc-type-val");
    if (typeEl) {
      typeEl.innerHTML = "<option value=\"\">—</option>";
      typeOpts.forEach((v) => { const o = document.createElement("option"); o.value = v; o.textContent = v; typeEl.appendChild(o); });
    }
  }

  function buildCircuitsDropdowns() {
    const st = getState(CIRCUITS_LIST_KEY);
    if (!st.headers.length) return;
    const p = getPanel();
    if (!p) return;
    const fromDevCol = channelColIdx(st, "from_side_device_refdes");
    const fromChanCol = channelColIdx(st, "from_side_device_chname");
    const fromConnCol = channelColIdx(st, "net_from_connector_name");
    const toDevCol = channelColIdx(st, "to_side_device_refdes");
    const toChanCol = channelColIdx(st, "to_side_device_chname");
    const toConnCol = channelColIdx(st, "net_to_connector_name");
    const signalCol = channelColIdx(st, "signal");
    function uniques(colIdx) {
      if (colIdx < 0) return [];
      return [...new Set(st.rows.map((r) => (r[colIdx] ?? "").trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    }
    function uniquesEither(colA, colB) {
      const set = new Set();
      if (colA >= 0) st.rows.forEach((r) => { const v = (r[colA] ?? "").trim(); if (v) set.add(v); });
      if (colB >= 0) st.rows.forEach((r) => { const v = (r[colB] ?? "").trim(); if (v) set.add(v); });
      return [...set].sort((a, b) => a.localeCompare(b));
    }
    function fill(id, options, anyLabel) {
      const el = p.querySelector(id);
      if (!el) return;
      const cur = el.value;
      el.innerHTML = "<option value=\"\">" + anyLabel + "</option>";
      options.forEach((v) => { const o = document.createElement("option"); o.value = v; o.textContent = v; el.appendChild(o); });
      if (options.includes(cur)) el.value = cur;
    }
    fill("#sl-ci-chan-a", uniquesEither(fromChanCol, toChanCol), "any channel");
    fill("#sl-ci-conn-a", uniquesEither(fromConnCol, toConnCol), "any connector");
    fill("#sl-ci-dev-a", uniquesEither(fromDevCol, toDevCol), "any device");
    fill("#sl-ci-chan-b", uniquesEither(fromChanCol, toChanCol), "any channel");
    fill("#sl-ci-conn-b", uniquesEither(fromConnCol, toConnCol), "any connector");
    fill("#sl-ci-dev-b", uniquesEither(fromDevCol, toDevCol), "any device");
    fill("#sl-ci-signal", uniques(signalCol), "any");
    const fromTypeCol = channelColIdx(st, "from_channel_type");
    const toTypeCol = channelColIdx(st, "to_channel_type");
    const typeOpts = uniquesEither(fromTypeCol, toTypeCol);
    const typeEl = p.querySelector("#sl-ci-type-val");
    if (typeEl) {
      typeEl.innerHTML = "<option value=\"\">—</option>";
      typeOpts.forEach((v) => { const o = document.createElement("option"); o.value = v; o.textContent = v; typeEl.appendChild(o); });
    }
  }

  function showViewerHeaders() {
    const p = getPanel();
    if (!p) return;
    ["sl-instances-header", "sl-channel-header", "sl-disconnect-header", "sl-circuits-header"].forEach((id) => {
      const el = p.querySelector("#" + id);
      if (el) el.classList.remove("visible");
    });
    if (currentTabKey === INSTANCES_LIST_KEY) {
      const el = p.querySelector("#sl-instances-header");
      if (el) el.classList.add("visible");
    } else if (currentTabKey === CHANNEL_MAP_KEY) {
      const el = p.querySelector("#sl-channel-header");
      if (el) el.classList.add("visible");
      buildChannelDropdowns();
    } else if (currentTabKey === DISCONNECT_MAP_KEY) {
      const el = p.querySelector("#sl-disconnect-header");
      if (el) el.classList.add("visible");
      buildDisconnectDropdowns();
    } else if (currentTabKey === CIRCUITS_LIST_KEY) {
      const el = p.querySelector("#sl-circuits-header");
      if (el) el.classList.add("visible");
      buildCircuitsDropdowns();
    }
    const typeWrap = p.querySelector(".sl-channel-type-wrap");
    if (typeWrap) typeWrap.style.display = "block";
  }

  function fetchChannelTypeCompatible(typeVal) {
    if (!typeVal) return Promise.resolve();
    return fetch("/api/channel-type-compatible?type=" + encodeURIComponent(typeVal))
      .then((r) => r.json())
      .then((data) => {
        channelTypeCompatibleCache[typeVal] = new Set(Array.isArray(data) ? data : []);
        if (currentTabKey) renderTable();
      })
      .catch(() => { channelTypeCompatibleCache[typeVal] = new Set([typeVal]); });
  }

  function buildHeader() {
    const p = getPanel();
    if (!p) return;
    const dataKey = getDataKey();
    const st = getState(dataKey);
    const thead = p.querySelector("#sl-thead");
    if (!thead) return;
    thead.innerHTML = "";
    const tr = document.createElement("tr");
    st.headers.forEach((h, i) => {
      const th = document.createElement("th");
      th.dataset.i = i;
      th.innerHTML = `<div class="sl-th-inner" data-i="${i}"><span>${escapeHtml(h)}</span><i class="sl-sort-btn">⇅</i><span class="sl-filter-dot"></span></div>`;
      th.querySelector(".sl-th-inner").addEventListener("click", (e) => openColDropdown(dataKey, i, th, e));
      tr.appendChild(th);
    });
    thead.appendChild(tr);
    updateHeaderUI();
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function updateHeaderUI() {
    const p = getPanel();
    if (!p) return;
    const dataKey = getDataKey();
    const st = getState(dataKey);
    p.querySelectorAll("#sl-thead th").forEach((th, i) => {
      const inner = th.querySelector(".sl-th-inner");
      const si = th.querySelector(".sl-sort-btn");
      if (!inner || !si) return;
      th.className = "";
      si.textContent = "⇅";
      if (i === st.sortCol) {
        th.className = st.sortDir === 1 ? "asc" : "desc";
        si.textContent = st.sortDir === 1 ? "↑" : "↓";
      }
      inner.className = "sl-th-inner" + (st.colFilters[i] ? " filtered" : "");
    });
  }

  function renderTable() {
    const p = getPanel();
    if (!p) return;
    const dataKey = getDataKey();
    const st = getState(dataKey);
    const empty = p.querySelector("#sl-empty");
    const table = p.querySelector("#sl-table");
    const tbody = p.querySelector("#sl-tbody");
    if (!empty || !table || !tbody) return;

    if (!st.headers.length) {
      empty.style.display = "flex";
      table.style.display = "none";
      empty.textContent = "No data.";
      return;
    }
    empty.style.display = "none";
    table.style.display = "";

    let rows = [...st.rows];
    const q = (st.search || "").toLowerCase();
    if (q) rows = rows.filter((r) => r.some((c) => (c ?? "").toLowerCase().includes(q)));
    st.colFilters.forEach((f, i) => {
      if (f) rows = rows.filter((r) => f.has(r[i] ?? ""));
    });
    if (currentTabKey === CHANNEL_MAP_KEY) rows = applyChannelFilters(st, rows);
    if (currentTabKey === DISCONNECT_MAP_KEY) rows = applyDisconnectFilters(st, rows);
    if (currentTabKey === CIRCUITS_LIST_KEY) rows = applyCircuitsFilters(st, rows);

    if (st.sortCol >= 0) {
      rows = rows.slice().sort((a, b) => {
        const av = a[st.sortCol] ?? "";
        const bv = b[st.sortCol] ?? "";
        const an = parseFloat(av);
        const bn = parseFloat(bv);
        if (!isNaN(an) && !isNaN(bn)) return (an - bn) * st.sortDir;
        return String(av).localeCompare(String(bv)) * st.sortDir;
      });
    }

    lastRenderedCount = rows.length;
    lastTotal = st.rows.length;
    notifyState({ rows: rows.length, total: st.rows.length, headers: st.headers, sortCol: st.sortCol, sortDir: st.sortDir, search: st.search });

    tbody.innerHTML = "";
    if (!rows.length) {
      tbody.innerHTML = `<tr class="sl-no-rows"><td colspan="${st.headers.length}">No matching rows</td></tr>`;
      return;
    }

    const channelTypeColIdxs = st.headers.map((h, i) => (isChannelTypeColumn(h) ? i : -1)).filter((i) => i >= 0);
    const uniqueTypes = new Set();
    if (useHumanReadableChannelTypes && channelTypeColIdxs.length) {
      rows.forEach((r) => channelTypeColIdxs.forEach((i) => { const v = (r[i] ?? "").trim(); if (v) uniqueTypes.add(v); }));
    }

    function renderTbody() {
      const isBom = currentTabKey === BOM_KEY;
      const refdesIdx = isBom ? st.headers.indexOf("device_refdes") : -1;
      rows.forEach((row) => {
        const tr = document.createElement("tr");
        if (isBom && refdesIdx >= 0) {
          tr.classList.add("sl-device-row");
          tr.dataset.deviceRefdes = (row[refdesIdx] ?? "").trim();
        }
        st.headers.forEach((h, i) => {
          const td = document.createElement("td");
          const raw = row[i] ?? "";
          td.textContent = useHumanReadableChannelTypes && isChannelTypeColumn(h) ? getChannelTypeDisplay(raw) : raw;
          td.title = raw;
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
        if (isBom && refdesIdx >= 0 && tr.dataset.deviceRefdes) {
          const detailTr = document.createElement("tr");
          detailTr.classList.add("sl-signals-detail-row");
          const detailTd = document.createElement("td");
          detailTd.colSpan = st.headers.length;
          detailTd.innerHTML = '<div class="sl-signals-viewer-wrap"><span class="loading">Click row to load signals list</span></div>';
          detailTr.appendChild(detailTd);
          tbody.appendChild(detailTr);
        }
      });
    }
    if (uniqueTypes.size) {
      fetchChannelTypeDisplays([...uniqueTypes]).then(renderTbody);
    } else {
      renderTbody();
    }
  }

  function parseTsv(tsvText) {
    const lines = String(tsvText).trim().split(/\r?\n/);
    if (!lines.length) return { headers: [], rows: [] };
    const headers = lines[0].split(/\t/);
    const rows = lines.slice(1).map((line) => line.split(/\t/));
    return { headers, rows };
  }

  function renderSignalsTable(container, tsvText) {
    const wrap = container.querySelector(".sl-signals-viewer-wrap") || container;
    wrap.innerHTML = "";
    try {
      const { headers, rows } = parseTsv(tsvText);
      if (!headers.length) {
        wrap.innerHTML = "<span class=\"loading\">No columns</span>";
        return;
      }
      wrap._signalsState = {
        search: "",
        colFilters: headers.map(() => null),
        fullRows: rows,
        headers,
        sortCol: -1,
        sortDir: 1,
      };
      const toolbar = document.createElement("div");
      toolbar.className = "sl-signals-toolbar";
      const searchInput = document.createElement("input");
      searchInput.type = "text";
      searchInput.placeholder = "Search…";
      searchInput.addEventListener("input", () => {
        wrap._signalsState.search = searchInput.value;
        renderSignalsTableBody(wrap);
      });
      const clearBtn = document.createElement("button");
      clearBtn.textContent = "Clear";
      clearBtn.addEventListener("click", () => {
        wrap._signalsState.search = "";
        wrap._signalsState.colFilters = headers.map(() => null);
        wrap._signalsState.sortCol = -1;
        searchInput.value = "";
        renderSignalsTableBody(wrap);
      });
      toolbar.appendChild(searchInput);
      toolbar.appendChild(clearBtn);
      wrap.appendChild(toolbar);
      const table = document.createElement("table");
      const thead = document.createElement("thead");
      const thr = document.createElement("tr");
      headers.forEach((h) => {
        const th = document.createElement("th");
        th.innerHTML = "<div class=\"sl-th-inner\">" + escapeHtml(h) + "</div>";
        thr.appendChild(th);
      });
      thead.appendChild(thr);
      table.appendChild(thead);
      const tbody = document.createElement("tbody");
      table.appendChild(tbody);
      wrap.appendChild(table);
      renderSignalsTableBody(wrap);
    } catch (e) {
      wrap.innerHTML = "<span class=\"error\">" + (e.message || "Parse error") + "</span>";
    }
  }

  function renderSignalsTableBody(wrap) {
    const st = wrap._signalsState;
    if (!st || !st.headers.length) return;
    let rows = [...st.fullRows];
    const q = (st.search || "").toLowerCase();
    if (q) rows = rows.filter((r) => r.some((c) => (c ?? "").toLowerCase().includes(q)));
    st.colFilters.forEach((f, i) => { if (f) rows = rows.filter((r) => f.has(r[i] ?? "")); });
    if (st.sortCol >= 0) {
      rows = rows.slice().sort((a, b) => {
        const av = a[st.sortCol] ?? "";
        const bv = b[st.sortCol] ?? "";
        const an = parseFloat(av);
        const bn = parseFloat(bv);
        if (!isNaN(an) && !isNaN(bn)) return (an - bn) * st.sortDir;
        return String(av).localeCompare(String(bv)) * st.sortDir;
      });
    }
    const tbody = wrap.querySelector("table tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      st.headers.forEach((h, i) => {
        const td = document.createElement("td");
        td.textContent = row[i] ?? "";
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  function openColDropdown(label, colIdx, thEl, e) {
    e.stopPropagation();
    const p = getPanel();
    if (!p) return;
    const dropdown = document.getElementById("sl-col-dropdown");
    const ddList = document.getElementById("sl-dd-list");
    const ddSearchEl = document.getElementById("sl-dd-search");
    if (!dropdown || !ddList || !ddSearchEl) return;
    ddLabel = label;
    ddColIdx = colIdx;
    ddSignalsWrap = null;
    const st = getState(label);
    const valSet = new Set(st.rows.map((r) => r[colIdx] ?? ""));
    ddAllValues = [...valSet].sort((a, b) => {
      const an = parseFloat(a);
      const bn = parseFloat(b);
      return !isNaN(an) && !isNaN(bn) ? an - bn : String(a).localeCompare(String(b));
    });
    ddPending.checked = st.colFilters[colIdx] ? new Set(st.colFilters[colIdx]) : new Set(ddAllValues);
    ddPending.sortDir = st.sortCol === colIdx ? st.sortDir : 0;
    ddSearchEl.value = "";
    renderDDList("");
    updateDDSortBtns();
    const rect = thEl.getBoundingClientRect();
    dropdown.style.top = rect.bottom + 2 + "px";
    dropdown.style.left = Math.min(rect.left, window.innerWidth - 228) + "px";
    dropdown.classList.add("open");
    ddSearchEl.focus();
  }

  function renderDDList(q) {
    const dropdown = document.getElementById("sl-col-dropdown");
    const ddList = document.getElementById("sl-dd-list");
    const ddSearchEl = document.getElementById("sl-dd-search");
    if (!dropdown || !ddList || !ddSearchEl) return;
    const vals = q ? ddAllValues.filter((v) => String(v).toLowerCase().includes(q.toLowerCase())) : ddAllValues;
    const colHeader = ddLabel ? getState(ddLabel).headers[ddColIdx] || "" : "";
    let html = "";
    if (!q) {
      const allC = vals.every((v) => ddPending.checked.has(v));
      html += `<div class="sl-dd-item sl-dd-select-all" data-val="__all__"><input type="checkbox" ${allC ? "checked" : ""}><label>(Select All)</label></div>`;
    }
    vals.forEach((v, i) => {
      const chk = ddPending.checked.has(v) ? "checked" : "";
      html += `<div class="sl-dd-item" data-val="${escapeHtml(String(v)).replace(/"/g, "&quot;")}"><input type="checkbox" ${chk}><label>${escapeHtml(v === "" ? "(blank)" : v)}</label></div>`;
    });
    ddList.innerHTML = html;
    ddList.querySelectorAll(".sl-dd-item").forEach((item) => {
      item.addEventListener("click", (ev) => {
        if (ev.target.tagName === "INPUT") return;
        const cb = item.querySelector("input");
        cb.checked = !cb.checked;
        const val = item.dataset.val;
        if (val === "__all__") {
          vals.forEach((v) => (cb.checked ? ddPending.checked.add(v) : ddPending.checked.delete(v)));
        } else {
          if (cb.checked) ddPending.checked.add(val);
          else ddPending.checked.delete(val);
        }
        renderDDList(ddSearchEl.value);
      });
    });
  }

  function updateDDSortBtns() {
    const asc = document.getElementById("sl-dd-asc");
    const desc = document.getElementById("sl-dd-desc");
    const nosort = document.getElementById("sl-dd-nosort");
    if (asc) asc.className = ddPending.sortDir === 1 ? "active" : "";
    if (desc) desc.className = ddPending.sortDir === -1 ? "active" : "";
    if (nosort) nosort.className = ddPending.sortDir === 0 ? "active" : "";
  }

  function ddApply() {
    const dropdown = document.getElementById("sl-col-dropdown");
    if (!dropdown) return;
    const st = getState(ddLabel);
    if (ddPending.sortDir !== 0) {
      st.sortCol = ddColIdx;
      st.sortDir = ddPending.sortDir;
    } else if (st.sortCol === ddColIdx) {
      st.sortCol = -1;
    }
    const allSel = ddAllValues.every((v) => ddPending.checked.has(v));
    st.colFilters[ddColIdx] = allSel ? null : new Set(ddPending.checked);
    dropdown.classList.remove("open");
    updateHeaderUI();
    renderTable();
    notifyState();
  }


  function notifyState(override) {
    const dataKey = getDataKey();
    const st = getState(dataKey);
    const payload = override || {
      rows: st.rows.length,
      total: st.rows.length,
      headers: st.headers,
      sortCol: st.sortCol,
      sortDir: st.sortDir,
      search: st.search || "",
    };
    if (typeof onStateChange === "function") onStateChange(payload);
  }

  function connectSSE() {
    if (sseEventSource) return;
    sseEventSource = new EventSource("/api/sse");
    sseEventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const key = data.key ?? data.label;
        const content = data.content;
        if (key == null || content === undefined) return;
        applyFileContent(key, content);
        if (key === currentTabKey || (key === POST_HARNESS_INSTANCES_LIST_KEY && currentTabKey === INSTANCES_LIST_KEY && instancesListSourceKey === POST_HARNESS_INSTANCES_LIST_KEY)) {
          if (currentTabKey === CHANNEL_MAP_KEY) buildChannelDropdowns();
          if (currentTabKey === DISCONNECT_MAP_KEY) buildDisconnectDropdowns();
          if (currentTabKey === CIRCUITS_LIST_KEY) buildCircuitsDropdowns();
          buildHeader();
          renderTable();
        }
      } catch (_) { }
    };
  }

  function loadPane(tabKey) {
    if (!getPanel()) return;
    buildPanelDOM();
    currentTabKey = tabKey;
    if (tabKey === INSTANCES_LIST_KEY) {
      instancesListSourceKey = fileStates["post harness instances list"] ? "post harness instances list" : INSTANCES_LIST_KEY;
    }
    fetch("/api/files")
      .then((r) => r.json())
      .then((files) => {
        Object.keys(files).forEach((key) => {
          const item = files[key];
          const content = typeof item === "string" ? item : (item && item.content);
          applyFileContent(key, content);
        });
        if (!getState(getDataKey()).headers.length) {
          const st = getState(tabKey);
          if (!st.headers.length && fileStates["post harness instances list"] && tabKey === INSTANCES_LIST_KEY) {
            instancesListSourceKey = "post harness instances list";
          }
        }
        showViewerHeaders();
        buildHeader();
        renderTable();
        connectSSE();
      })
      .catch(() => {
        const empty = getPanel()?.querySelector("#sl-empty");
        if (empty) empty.textContent = "Failed to load.";
      });
  }

  function setSearch(value) {
    const dataKey = getDataKey();
    getState(dataKey).search = value ?? "";
    renderTable();
  }

  function clearFilters() {
    const dataKey = getDataKey();
    const st = getState(dataKey);
    st.colFilters = st.headers.map(() => null);
    st.sortCol = -1;
    st.sortDir = 1;
    st.search = "";
    updateHeaderUI();
    renderTable();
    notifyState();
  }

  function setSort(col, dir) {
    const dataKey = getDataKey();
    const st = getState(dataKey);
    st.sortCol = col >= 0 ? col : -1;
    st.sortDir = dir === -1 || dir === 1 ? dir : 1;
    updateHeaderUI();
    renderTable();
    notifyState();
  }

  function setChannelTypeHumanReadable(use) {
    useHumanReadableChannelTypes = !!use;
    const p = getPanel();
    const cb = p?.querySelector("#sl-channel-type-human");
    if (cb) cb.checked = useHumanReadableChannelTypes;
    if (currentTabKey) {
      renderTable();
      notifyState();
    }
  }

  window.SystemListView = {
    loadPane,
    setSearch,
    clearFilters,
    setSort,
    setChannelTypeHumanReadable,
    getState() {
      const dataKey = getDataKey();
      const st = getState(dataKey);
      return {
        rows: lastRenderedCount,
        total: lastTotal || st.rows.length,
        headers: st.headers,
        sortCol: st.sortCol,
        sortDir: st.sortDir,
        search: st.search || "",
      };
    },
    setOnStateChange(fn) {
      onStateChange = fn;
    },
  };
})();
