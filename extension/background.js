let SERVER_URL = "http://localhost:3000";
let isLoggingEnabled = true;
let scope = "example.com";


function matchesScope(url, scope) {
    if (!scope) return true;
    if (scope.startsWith("*.")) {
        // Strip "*." and match the base domain
        const domain = scope.replace("*.", "");
        return url.includes(domain);
    }
    return url.includes(scope);
}

// Load settings from Chrome storage
chrome.storage.sync.get(["serverUrl", "loggingEnabled", "scope"], (data) => {
    if (data.serverUrl) SERVER_URL = data.serverUrl;
    if (typeof data.loggingEnabled !== "undefined") isLoggingEnabled = data.loggingEnabled;
    if (data.scope) scope = data.scope;
});

// Listen for popup messages to update config
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "updateSettings") {
        SERVER_URL = message.serverUrl;
        isLoggingEnabled = message.loggingEnabled;
        scope = message.scope;

        chrome.storage.sync.set({
            serverUrl: SERVER_URL,
            loggingEnabled: isLoggingEnabled,
            scope
        });

        sendResponse({ status: "success" });
    }
});

// 🔥 MAIN LOGIC: Only capture real page navigations
chrome.webNavigation.onCommitted.addListener((details) => {
    if (!isLoggingEnabled) return;

    // Only main frame (not iframes)
    if (details.frameId !== 0) return;

    chrome.tabs.get(details.tabId, (tab) => {
        if (chrome.runtime.lastError) return;

        const url = tab.url;
        if (!url || url.startsWith("chrome://") || url.startsWith("chrome-extension://")) return;

        // Optional scope filtering
        if (!matchesScope(url, scope)) return;

        // Log it to the Flask server
        fetch(`${SERVER_URL}/capture-har`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pageUrl: url })
        }).catch(err => {
            console.error("Failed to send URL:", err);
        });
    });
});
