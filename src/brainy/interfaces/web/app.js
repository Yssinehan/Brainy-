const token = window.BRAINY_GATEWAY_TOKEN;
const headers = { "Content-Type": "application/json", "X-DreamOS-Token": token };
const $ = (selector) => document.querySelector(selector);

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, { ...options, headers: { "X-DreamOS-Token": token, ...(options.headers || {}) } });
  } catch {
    throw new Error("Le serveur Brainy est indisponible. Lancez l’API puis réessayez.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(formatDetail(body.detail) || "La mémoire n’a pas pu répondre. Réessayez dans un instant.");
  }
  return response.json();
}

function formatDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return "";
}

function card(text, kind = "result-card") { return `<div class="${kind}">${escapeHtml(text)}</div>`; }
function escapeHtml(value) { const node = document.createElement("div"); node.textContent = value || ""; return node.innerHTML; }
function setStatus(target, message, loading = false) { target.innerHTML = `<p class="status ${loading ? "loading" : ""}">${escapeHtml(message)}</p>`; }
function speak(text) { if ("speechSynthesis" in window) { speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance(text)); } }

function appendSources(answer, container) {
  if (!answer.sources?.length) return;
  const fragment = $("#source-template").content.cloneNode(true);
  fragment.querySelector("summary span").textContent = `(${answer.sources.length})`;
  const list = fragment.querySelector(".source-list");
  answer.sources.forEach((source) => {
    const item = document.createElement("div"); item.className = "source";
    item.innerHTML = `<b>${escapeHtml(source.source)}</b><span>${escapeHtml(source.snippet)}</span>`;
    list.append(item);
  });
  container.append(fragment);
}

function appendMessage(role, text, answer = null) {
  $("#empty-thought")?.remove();
  const message = document.createElement("article"); message.className = `message ${role}`;
  message.innerHTML = `<div class="meta">${role === "user" ? "vous" : "brainy"}</div><div class="body ${answer && !answer.grounded ? "honest" : ""}">${escapeHtml(text)}</div>`;
  if (answer?.disagreement) message.insertAdjacentHTML("beforeend", `<div class="disagreement">Les voix consultées ne sont pas entièrement d’accord. Consultez les sources avant de décider.</div>`);
  appendSources(answer, message); $("#conversation").append(message); message.scrollIntoView({ behavior: "smooth", block: "end" });
}

document.querySelectorAll(".nav-item[data-view]").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item === button));
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === button.dataset.view));
  history.replaceState(null, "", `#${button.dataset.view}`);
}));

$("#ask-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const field = $("#question"); const question = field.value.trim(); if (!question) return;
  appendMessage("user", question); field.value = ""; field.style.height = "";
  const waiting = document.createElement("article"); waiting.className = "message assistant"; waiting.innerHTML = `<div class="status loading">Je relie les traces…</div>`; $("#conversation").append(waiting);
  try {
    const answer = await request("/api/v1/chat", { method: "POST", headers, body: JSON.stringify({ message: question, verify: $("#chat-verify").checked }) });
    waiting.remove();
    appendMessage("assistant", answer.response || answer.text, answer);
  }
  catch (error) { waiting.innerHTML = card(`${error.message} Vérifiez que l’API et votre modèle sont prêts.`, "result-card error"); }
});
$("#question").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); $("#ask-form").requestSubmit(); }
});
$("#question").addEventListener("input", (event) => { event.target.style.height = "auto"; event.target.style.height = `${event.target.scrollHeight}px`; });

$("#agent-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const target = $("#agent-result"); setStatus(target, "L’agent dessine son chemin…", true);
  try {
    const result = await request("/api/v1/agent/run", { method: "POST", headers, body: JSON.stringify({ goal: $("#agent-goal").value.trim(), allow_network: $("#allow-network").checked, allow_write: $("#allow-write").checked, max_steps: Number($("#max-steps").value) }) });
    const steps = result.steps.map((step, index) => `<article><h3>étape ${index + 1}${step.tool_name ? ` / ${escapeHtml(step.tool_name)}` : ""}</h3><p>${escapeHtml(step.thought)}</p>${step.observation ? `<p class="observation">observation: ${escapeHtml(step.observation)}</p>` : ""}</article>`).join("");
    target.innerHTML = `<div class="timeline">${steps || "<article><p>Aucune étape intermédiaire n’a été nécessaire.</p></article>"}</div><div class="final-answer">${escapeHtml(result.final_answer)}</div>`;
  } catch (error) { target.innerHTML = card(`${error.message} L’agent n’a effectué aucune action supplémentaire.`, "result-card error"); }
});

let recorder, chunks = [];
const recordButton = $("#record-button");
async function startRecording() {
  try { const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); chunks = []; recorder = new MediaRecorder(stream); recorder.ondataavailable = (e) => chunks.push(e.data); recorder.onstop = () => { stream.getTracks().forEach((track) => track.stop()); sendAudio(new Blob(chunks, { type: recorder.mimeType || "audio/webm" })); }; recorder.start(); recordButton.classList.add("recording"); recordButton.setAttribute("aria-pressed", "true"); recordButton.querySelector("b").textContent = "J’écoute…"; }
  catch { $("#voice-result").innerHTML = card("Le micro est indisponible. Autorisez son accès dans votre navigateur, puis réessayez.", "result-card error"); }
}
function stopRecording() { if (recorder?.state === "recording") recorder.stop(); recordButton.classList.remove("recording"); recordButton.setAttribute("aria-pressed", "false"); recordButton.querySelector("b").textContent = "Maintenez pour parler"; }
recordButton.addEventListener("pointerdown", startRecording); recordButton.addEventListener("pointerup", stopRecording); recordButton.addEventListener("pointerleave", stopRecording); recordButton.addEventListener("keydown", (e) => { if ((e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); startRecording(); } }); recordButton.addEventListener("keyup", stopRecording);
async function sendAudio(blob) {
  const result = $("#voice-result"); setStatus(result, "J’écoute et je cherche dans vos notes…", true); const data = new FormData(); data.append("file", blob, "thought.webm");
  try { const answer = await request(`/voice/ask?verify=${$("#voice-verify").checked}`, { method: "POST", body: data }); result.innerHTML = `<p class="eyebrow">vous avez dit</p>${card(answer.transcript)}<p class="eyebrow">brainy répond</p>`; const response = document.createElement("div"); response.className = "result-card"; response.textContent = answer.text; result.append(response); appendSources(answer, result); speak(answer.text); }
  catch (error) { result.innerHTML = card(error.message, "result-card error"); }
}

let imageFile;
const dropZone = $("#drop-zone"); $("#image-file").addEventListener("change", (event) => { imageFile = event.target.files[0]; if (imageFile) dropZone.querySelector("b").textContent = imageFile.name; });
["dragenter", "dragover"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => { event.preventDefault(); dropZone.classList.add("drag"); })); ["dragleave", "drop"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => { event.preventDefault(); dropZone.classList.remove("drag"); })); dropZone.addEventListener("drop", (event) => { imageFile = event.dataTransfer.files[0]; if (imageFile?.type.startsWith("image/")) dropZone.querySelector("b").textContent = imageFile.name; });
async function imageAction(action) {
  const target = $("#vision-result"); if (!imageFile) { target.innerHTML = card("Choisissez d’abord une image à observer.", "result-card error"); return; } setStatus(target, action === "describe" ? "Je regarde l’image…" : "J’extrais puis ancre le texte…", true);
  const data = new FormData(); data.append("file", imageFile, imageFile.name); const query = action === "describe" && $("#image-question").value.trim() ? `?question=${encodeURIComponent($("#image-question").value.trim())}` : "";
  try { const result = await request(`/vision/${action}${query}`, { method: "POST", body: data }); target.innerHTML = action === "describe" ? card(result.description) : card(`Image ajoutée : ${result.chunks_ingested} fragment(s) indexé(s), ${result.kg_triples} lien(s) de connaissance.`, "result-card"); refreshStats(); }
  catch (error) { target.innerHTML = card(error.message, "result-card error"); }
}
$("#describe-image").addEventListener("click", () => imageAction("describe")); $("#ingest-image").addEventListener("click", () => imageAction("ingest"));

$("#ingest-form").addEventListener("submit", async (event) => { event.preventDefault(); const target = $("#ingest-result"); setStatus(target, "J’ancre cette pensée…", true); const label = $("#note-label").value.trim(); try { const result = await request("/ingest", { method: "POST", headers, body: JSON.stringify({ text: $("#note-text").value, doc_id: label, source: label }) }); target.innerHTML = card(`Ancrée : ${result.chunks_ingested} fragment(s), ${result.kg_triples} lien(s).`); $("#note-text").value = ""; refreshStats(); } catch (error) { target.innerHTML = card(error.message, "result-card error"); } });

async function refreshStats() { try { const stats = await request("/stats"); $("#stats").textContent = stats.chunks ?? "0"; $("#stats").title = `${stats.chunks ?? 0} fragments indexés`; } catch { $("#stats").textContent = "—"; } }
refreshStats();
