document.addEventListener("DOMContentLoaded", () => {
    const serverUrlInput = document.getElementById("serverUrl");
    const scopeInput = document.getElementById("scope");
    const toggleLogging = document.getElementById("toggleLogging");
    const saveBtn = document.getElementById("saveBtn");

    chrome.storage.sync.get(["serverUrl", "loggingEnabled", "scope"], (data) => {
        if (data.serverUrl) serverUrlInput.value = data.serverUrl;
        if (typeof data.loggingEnabled !== "undefined") toggleLogging.checked = data.loggingEnabled;
        if (data.scope) scopeInput.value = data.scope;
    });

    saveBtn.addEventListener("click", () => {
        const serverUrl = serverUrlInput.value.trim();
        const scope = scopeInput.value.trim();
        const loggingEnabled = toggleLogging.checked;

        chrome.runtime.sendMessage({
            type: "updateSettings",
            serverUrl,
            scope,
            loggingEnabled
        }, response => {
            if (response.status === "success") alert("Settings saved!");
        });
    });
});
