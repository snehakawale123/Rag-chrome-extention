
const API_BASE = "http://127.0.0.1:8000";

// Get elements from popup.html
const urlInput = document.getElementById("urlInput");
const ingestButton = document.getElementById("ingestButton");
const currentPageButton = document.getElementById("currentPageButton");
const ingestStatus = document.getElementById("ingestStatus");

const pdfInput = document.getElementById("pdfInput");
const uploadPdfButton = document.getElementById("uploadPdfButton");
const uploadStatus = document.getElementById("uploadStatus");

const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");

// Check whether a URL is HTTP or HTTPS.
function isWebUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

// Display a message safely in the chat.
function addMessage(text, role = "assistant", sources = []) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.textContent = text || "No response received.";

  if (Array.isArray(sources) && sources.length > 0) {
    const sourcesContainer = document.createElement("div");
    sourcesContainer.className = "sources";

    const heading = document.createElement("strong");
    heading.textContent = "Sources";
    sourcesContainer.appendChild(heading);

    sources.forEach((source) => {
      const sourceItem = document.createElement("div");
      sourceItem.style.marginBottom = "8px";

      if (source.url && isWebUrl(source.url)) {
        const link = document.createElement("a");
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = source.title || source.url;
        sourceItem.appendChild(link);
      } else {
        const filename = document.createElement("span");
        filename.textContent = source.filename
          ? `PDF: ${source.filename}${
              source.page != null ? ` (page ${source.page})` : ""
            }`
          : source.title || "Document source";

        sourceItem.appendChild(filename);
      }

      sourcesContainer.appendChild(sourceItem);
    });

    message.appendChild(sourcesContainer);
  }

  messages.appendChild(message);
  messages.scrollTop = messages.scrollHeight;
}

// Index a webpage entered in the URL field.
async function ingestWebpage(url) {
  if (!isWebUrl(url)) {
    ingestStatus.textContent =
      "Enter a valid webpage URL beginning with http:// or https://.";
    return;
  }

  ingestButton.disabled = true;
  currentPageButton.disabled = true;
  ingestStatus.textContent = "Indexing webpage. Please wait...";

  try {
    const response = await fetch(`${API_BASE}/api/webpages/ingest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url })
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        result.detail || result.message || "Webpage indexing failed."
      );
    }

    ingestStatus.textContent =
      result.message || `Webpage indexed successfully: ${url}`;
  } catch (error) {
    ingestStatus.textContent = `Error: ${error.message}`;
  } finally {
    ingestButton.disabled = false;
    currentPageButton.disabled = false;
  }
}

// Index the URL entered by the user.
ingestButton.addEventListener("click", async () => {
  await ingestWebpage(urlInput.value.trim());
});

// Index the currently active browser tab.
currentPageButton.addEventListener("click", async () => {
  ingestStatus.textContent = "";

  try {
    const tabs = await chrome.tabs.query({
      active: true,
      currentWindow: true
    });

    const tab = tabs[0];

    if (!tab || !tab.url || !isWebUrl(tab.url)) {
      ingestStatus.textContent =
        "This tab cannot be indexed. Open a regular HTTP or HTTPS webpage.";
      return;
    }

    urlInput.value = tab.url;
    await ingestWebpage(tab.url);
  } catch (error) {
    ingestStatus.textContent =
      `Could not read the current tab: ${error.message}`;
  }
});

// Upload and index a PDF file.
uploadPdfButton.addEventListener("click", async () => {
  const file = pdfInput.files[0];

  if (!file) {
    uploadStatus.textContent = "Please choose a PDF file first.";
    return;
  }

  if (
    file.type !== "application/pdf" &&
    !file.name.toLowerCase().endsWith(".pdf")
  ) {
    uploadStatus.textContent = "Please select a valid PDF file.";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  uploadPdfButton.disabled = true;
  uploadStatus.textContent = "Uploading and indexing PDF...";

  try {
    const response = await fetch(`${API_BASE}/api/documents/upload`, {
      method: "POST",
      body: formData
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        result.detail || result.message || "PDF upload failed."
      );
    }

    uploadStatus.textContent =
      `${file.name} uploaded and indexed successfully. You can now ask questions below.`;

    // Keep the popup ready for chat.
    questionInput.focus();
    
  } catch (error) {
    uploadStatus.textContent =
      `Upload failed: ${error.message}. Check that FastAPI is running.`;
  } finally {
    uploadPdfButton.disabled = false;
  }
});

// Ask a question about indexed PDFs and webpages.
chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = questionInput.value.trim();

  if (!question) {
    return;
  }

  addMessage(question, "user");
  questionInput.value = "";
  sendButton.disabled = true;

  const loadingMessage = document.createElement("div");
  loadingMessage.className = "message assistant";
  loadingMessage.textContent = "Thinking...";
  messages.appendChild(loadingMessage);
  messages.scrollTop = messages.scrollHeight;

  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question })
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        result.detail || result.message || "Could not get an answer."
      );
    }

    loadingMessage.remove();
    addMessage(
      result.answer || result.message || "No answer was returned.",
      "assistant",
      result.sources || []
    );
  } catch (error) {
    loadingMessage.remove();
    addMessage(`Error: ${error.message}`, "error");
  } finally {
    sendButton.disabled = false;
    questionInput.focus();
  }
});
