(() => {
  "use strict";
  const tabs = document.querySelectorAll("[data-tab]");
  const panels = ["link", "images", "cbz"];
  const convertForm = document.getElementById("convert-form");
  const convertStatus = document.getElementById("convert-status");
  let inputType = "link";

  function activate(type) {
    inputType = type;
    tabs.forEach((tab) => {
      const active = tab.dataset.tab === type;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
    });
    panels.forEach((panel) => {
      document.getElementById(`panel-${panel}`).hidden = panel !== type;
    });
    // Never accidentally send multiple sources from hidden inputs.
    if (type !== "link") document.getElementById("url").value = "";
    if (type !== "images") document.getElementById("images").value = "";
    if (type !== "cbz") document.getElementById("cbz").value = "";
  }
  tabs.forEach((tab) =>
    tab.addEventListener("click", () => activate(tab.dataset.tab)),
  );
  const inspectButton = document.getElementById("inspect-link");
  const inspectStatus = document.getElementById("inspect-status");
  inspectButton.addEventListener("click", async () => {
    const url = document.getElementById("url").value.trim();
    if (!url) {
      inspectStatus.textContent = "Paste a chapter link first.";
      return;
    }
    inspectButton.disabled = true;
    inspectStatus.textContent = "Checking public chapter data…";
    try {
      const data = new FormData();
      data.append("url", url);
      const response = await fetch("/inspect", { method: "POST", body: data });
      const result = await response.json();
      inspectStatus.textContent = response.ok
        ? `${result.series} · ${result.episode} · ${result.page_count} pages found`
        : result.error;
    } catch (_) {
      inspectStatus.textContent = "Unable to inspect the source right now.";
    } finally {
      inspectButton.disabled = false;
    }
  });
  const contrast = document.getElementById("contrast");
  const contrastValue = document.getElementById("contrast-value");
  contrast.addEventListener(
    "input",
    () => (contrastValue.textContent = `${Number(contrast.value).toFixed(2)}×`),
  );
  convertForm.addEventListener("submit", (event) => {
    const chosen =
      inputType === "link"
        ? document.getElementById("url").value.trim()
        : inputType === "images"
          ? document.getElementById("images").files.length
          : document.getElementById("cbz").files.length;
    if (!chosen) {
      event.preventDefault();
      convertStatus.textContent =
        "Choose a chapter link or file before converting.";
      return;
    }
    convertStatus.textContent =
      "Converting your chapter. Your file will download automatically when ready…";
  });

  const fileInput = document.getElementById("cbz-files");
  const manager = document.getElementById("episode-manager");
  const list = document.getElementById("episode-list");
  const count = document.getElementById("episode-count");
  const sortButton = document.getElementById("sort-episodes");
  const orderMode = document.getElementById("order-mode");
  const mergeForm = document.getElementById("merge-form");
  const mergeButton = document.getElementById("merge-button");
  const mergeStatus = document.getElementById("merge-status");
  const volumeInput = document.getElementById("volume-name");
  let selectedFiles = [];
  function episodeNumber(name) {
    const match = name.match(/(?:episode|ep|chapter|ch)[\s._-]*(\d+)/i);
    return match ? Number(match[1]) : null;
  }
  function sortFiles() {
    selectedFiles.sort((a, b) => {
      const aa = episodeNumber(a.name),
        bb = episodeNumber(b.name);
      if (aa !== null && bb !== null && aa !== bb) return aa - bb;
      if (aa !== null && bb === null) return -1;
      if (aa === null && bb !== null) return 1;
      return a.name.localeCompare(b.name, undefined, {
        numeric: true,
        sensitivity: "base",
      });
    });
    orderMode.value = "auto";
    render();
  }
  function move(index, delta) {
    const target = index + delta;
    if (target < 0 || target >= selectedFiles.length) return;
    [selectedFiles[index], selectedFiles[target]] = [
      selectedFiles[target],
      selectedFiles[index],
    ];
    orderMode.value = "manual";
    render();
  }
  function render() {
    list.replaceChildren();
    manager.hidden = !selectedFiles.length;
    count.textContent = `(${selectedFiles.length} selected)`;
    selectedFiles.forEach((file, index) => {
      const item = document.createElement("li");
      item.className = "episode-item";
      const row = document.createElement("div");
      row.className = "episode-row";
      const name = document.createElement("span");
      name.className = "episode-filename";
      name.textContent = file.name;
      const controls = document.createElement("div");
      controls.className = "episode-controls";
      for (const [label, delta] of [
        ["↑", -1],
        ["↓", 1],
      ]) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.setAttribute(
          "aria-label",
          `Move ${file.name} ${delta < 0 ? "up" : "down"}`,
        );
        button.disabled =
          index + delta < 0 || index + delta >= selectedFiles.length;
        button.addEventListener("click", () => move(index, delta));
        controls.append(button);
      }
      row.append(name, controls);
      item.append(row);
      list.append(item);
    });
  }
  fileInput.addEventListener("change", () => {
    selectedFiles = Array.from(fileInput.files);
    sortFiles();
    mergeStatus.textContent = `${selectedFiles.length} chapter files selected.`;
  });
  sortButton.addEventListener("click", sortFiles);
  function errorMessage(raw) {
    // A reverse proxy might return a full HTML 413 response. Don't print markup.
    if (/<html|<!doctype/i.test(raw)) {
      return /413|Request Entity Too Large/i.test(raw)
        ? "Upload too large (HTTP 413). Increase client_max_body_size in NGINX and MAX_UPLOAD_MB in the container."
        : "The server rejected the request. Check the reverse proxy and container logs.";
    }
    return raw.slice(0, 400);
  }
  mergeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (selectedFiles.length < 2 || selectedFiles.length > 20) {
      mergeStatus.textContent = "Select between 2 and 20 CBZ files.";
      return;
    }
    const data = new FormData();
    selectedFiles.forEach((file) => data.append("cbz_files", file, file.name));
    data.append("order_mode", "manual");
    data.append("volume_name", volumeInput.value);
    mergeButton.disabled = true;
    mergeStatus.textContent =
      "Uploading and merging. Large volumes can take some time…";
    try {
      const response = await fetch(mergeForm.action, {
        method: "POST",
        body: data,
      });
      if (!response.ok) throw new Error(errorMessage(await response.text()));
      const blob = await response.blob();
      const filename =
        response.headers
          .get("Content-Disposition")
          ?.match(/filename\*?=(?:UTF-8''|\")?([^";]+)/i)?.[1] ||
        "Merged-Volume.cbz";
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = decodeURIComponent(filename.trim());
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      mergeStatus.textContent = `Merged ${selectedFiles.length} chapters successfully.`;
    } catch (error) {
      mergeStatus.textContent = `Merge failed: ${error.message}`;
    } finally {
      mergeButton.disabled = false;
    }
  });
})();
