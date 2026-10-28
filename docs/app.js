// ContextIQ — AI Conversational Assistant
// Production backend hosted on Render

const API = "https://contextiq-rag-knowledge-assistant.onrender.com";

const $ = (s) => document.querySelector(s);

// Escape HTML to prevent injection
const escape = (s) =>
  String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[c],
  );

// Check backend connection and retrieve documents
async function refresh() {
  try {
    const [healthResponse, documentsResponse] = await Promise.all([
      fetch(API + "/api/health"),
      fetch(API + "/api/documents"),
    ]);

    if (!healthResponse.ok || !documentsResponse.ok) {
      throw new Error("Backend request failed");
    }

    const h = await healthResponse.json();
    const d = await documentsResponse.json();

    $("#status").textContent = "Backend connected";
    $("#docCount").textContent = d.length;

    $("#chunkCount").textContent = d.reduce(
      (total, document) => total + document.chunks,
      0,
    );

    $("#engine").textContent = h.ai_enabled
      ? "OpenAI + RAG"
      : "Retrieval mode";

    $("#files").innerHTML = d
      .map(
        (x) =>
          `<div class="file-item">
            <button
              data-delete="${escape(x.id)}"
              aria-label="Remove document"
            >✕</button>
            📄 ${escape(x.name)}
            <br>
            <small>${x.chunks} segments</small>
          </div>`,
      )
      .join("");

  } catch (error) {
    console.error("Backend connection error:", error);

    $("#status").textContent = "Backend offline — connection unavailable";
    $("#engine").textContent = "Offline";
  }
}

// Display chat messages
function add(role, text, sources = []) {
  const welcome = $(".welcome");

  if (welcome) {
    welcome.remove();
  }

  const el = document.createElement("div");
  el.className = "message " + role;
  el.textContent = text;

  for (const s of sources) {
    const ref = document.createElement("div");
    ref.className = "source";

    ref.textContent =
      `${s.document} · Segment ${s.chunk}: ${s.excerpt}`;

    el.appendChild(ref);
  }

  $("#messages").appendChild(el);

  $("#messages").scrollTop = $("#messages").scrollHeight;
}

// Upload PDF or text documents
$("#file").onchange = async (e) => {
  const f = e.target.files[0];

  if (!f) return;

  const form = new FormData();
  form.append("file", f);

  try {
    const response = await fetch(API + "/api/upload", {
      method: "POST",
      body: form,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Document upload failed",
      );
    }

    add(
      "assistant",
      `Added ${data.name} (${data.chunks} text segments). Ask a question!`,
    );

    await refresh();

  } catch (error) {
    console.error("Upload error:", error);
    alert("Upload failed: " + error.message);
  }

  e.target.value = "";
};

// Handle AI questions
$("#form").onsubmit = async (e) => {
  e.preventDefault();

  const q = $("#question").value.trim();

  if (!q) return;

  add("user", q);

  $("#question").value = "";

  add("assistant", "Thinking...");

  const pending = $("#messages").lastElementChild;

  try {
    const response = await fetch(API + "/api/chat", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        question: q,
      }),
    });

    const data = await response.json();

    pending.remove();

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Unable to generate answer",
      );
    }

    add(
      "assistant",
      data.answer,
      data.sources || [],
    );

  } catch (error) {
    pending.remove();

    console.error("Chat error:", error);

    add(
      "assistant",
      "Request failed: " + error.message,
    );
  }
};

// Clear conversation
$("#clear").onclick = () => {
  $("#messages").innerHTML = `
    <div class="welcome">
      <div class="orb">✧</div>
      <h2>Start a new conversation.</h2>
      <p>Ask a question about your uploaded documents.</p>
    </div>
  `;
};

// Handle suggested questions and document deletion
document.addEventListener("click", async (e) => {
  const questionButton = e.target.closest("[data-question]");

  if (questionButton) {
    $("#question").value = questionButton.dataset.question;
    $("#form").requestSubmit();
    return;
  }

  const deleteButton = e.target.closest("[data-delete]");

  if (deleteButton) {
    try {
      const response = await fetch(
        API +
          "/api/documents/" +
          encodeURIComponent(deleteButton.dataset.delete),
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        throw new Error("Unable to delete document");
      }

      await refresh();

    } catch (error) {
      console.error("Delete error:", error);
      alert("Delete failed: " + error.message);
    }
  }
});

// Initialize application
refresh();