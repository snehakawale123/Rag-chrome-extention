
chrome.action.onClicked.addListener(() => {
  chrome.windows.create({
    url: chrome.runtime.getURL("window.html"),
    type: "normal",
    width: 900,
    height: 850,
    focused: true
  });
});
