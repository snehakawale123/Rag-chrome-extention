
document.getElementById("pdfInput").addEventListener("change", async (event) => {
  const file = event.target.files[0];

  if (!file) return;

  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      "http://127.0.0.1:8000/api/documents/upload",
      {
        method: "POST",
        body: formData
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "Upload failed");
    }

    document.body.insertAdjacentHTML(
      "beforeend",
      "<p>PDF uploaded successfully. Return to your RAG Assistant to chat.</p>"
    );
  } catch (error) {
    document.body.insertAdjacentText(
      "beforeend",
      `Upload failed: ${error.message}`
    );
  }
});
