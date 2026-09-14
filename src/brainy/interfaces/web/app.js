(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const token = window.BRAINY_GATEWAY_TOKEN;
  const api = async (path, options = {}) => {
    const headers = { "X-DreamOS-Token": token, ...(options.headers || {}) };
    const response = await fetch(path, { ...options, headers });
    if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || "Une erreur est survenue.");
    return response.json();
  };
  const state = { month: new Date(new Date().getFullYear(), new Date().getMonth(), 1), attachments: [], events: [], history: [] };
  const types = { exam: "Examen", course: "Cours", assignment: "Devoir", personal: "Personnel" };
  const toast = (title, text) => {
    const el = document.createElement("div"); el.className = "toast"; el.innerHTML = `<strong>${title}</strong>${text}`;
    $("#toast-region").append(el); setTimeout(() => el.remove(), 4300);
  };
  const openModal = (html) => { $("#modal").innerHTML = html; $("#modal-backdrop").classList.remove("hidden"); };
  const closeModal = () => $("#modal-backdrop").classList.add("hidden");

  function navigate() {
    const id = location.hash.slice(1) || "home";
    $$(".page").forEach(p => p.classList.toggle("active", p.id === id));
    $$(".nav-link").forEach(a => a.classList.toggle("active", a.getAttribute("href") === `#${id}`));
    $("#navigation").classList.remove("open"); $("#menu-button").setAttribute("aria-expanded", "false");
    if (id === "calendar") renderCalendar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  addEventListener("hashchange", navigate); navigate();
  $("#menu-button").addEventListener("click", () => { const nav = $("#navigation"); nav.classList.toggle("open"); $("#menu-button").setAttribute("aria-expanded", nav.classList.contains("open")); });

  const formatDate = (value) => new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long", year: "numeric" }).format(new Date(`${value}T12:00:00`));
  const eventTime = (event) => event.start?.slice(11,16) === "00:00" ? "Toute la journée" : event.start?.slice(11,16);
  const normalizeType = (category = "") => ({ "Examen": "exam", "Cours": "course", "Devoir": "assignment", "Personnel": "personal" }[category] || "personal");
  async function loadEvents() {
    try { state.events = await api("/api/v1/events"); }
    catch { state.events = JSON.parse(localStorage.getItem("brainy-events") || "[]"); }
  }
  async function saveEvent(event) {
    try { const saved = await api("/api/v1/events", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(event) }); state.events.push(saved); }
    catch { event.id ||= crypto.randomUUID(); state.events.push(event); localStorage.setItem("brainy-events", JSON.stringify(state.events)); }
  }
  async function deleteEvent(event) {
    try { await api(`/api/v1/events/${event.id}`, { method: "DELETE" }); }
    catch { localStorage.setItem("brainy-events", JSON.stringify(state.events.filter(e => e.id !== event.id))); }
    state.events = state.events.filter(e => e.id !== event.id); renderCalendar();
  }
  function addMessage(role, text) {
    $(".welcome-message")?.remove(); const el = document.createElement("article"); el.className = `message ${role}`;
    el.innerHTML = `<div class="message-meta">${role === "user" ? "Vous" : "Brainy"}</div><div>${text.replace(/</g, "&lt;").replace(/\n/g, "<br>")}</div>`;
    $("#messages").append(el); el.scrollIntoView({ behavior: "smooth", block: "end" });
  }
  function dateFromMessage(message) {
    const months = { janvier:0, février:1, fevrier:1, mars:2, avril:3, mai:4, juin:5, juillet:6, août:7, aout:7, septembre:8, octobre:9, novembre:10, décembre:11, decembre:11 };
    const found = message.toLowerCase().match(/(?:le\s+)?(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)(?:\s+(\d{4}))?/);
    if (!found) return null; const year = Number(found[3] || new Date().getFullYear()); return `${year}-${String(months[found[2]] + 1).padStart(2,"0")}-${found[1].padStart(2,"0")}`;
  }
  function detectedEvent(message) {
    if (!/(examen|devoir|cours|rendez-vous|réunion|reunion)/i.test(message)) return null;
    const date = dateFromMessage(message); if (!date) return null;
    const time = message.match(/(?:à|a)\s*(\d{1,2})(?:h|:)(\d{2})?/i); const category = /examen/i.test(message) ? "Examen" : /devoir/i.test(message) ? "Devoir" : "Cours";
    const subject = message.match(/(?:de|d')\s+([\p{L}\s-]+?)(?:\s+le|\s+à|\.|$)/iu)?.[1]?.trim() || category;
    return { title: `${category} de ${subject[0].toUpperCase()}${subject.slice(1)}`, start: `${date}T${String(time?.[1] || "09").padStart(2,"0")}:${time?.[2] || "00"}:00`, category, description: "Événement détecté dans une conversation avec Brainy.", source_type: "chat", source_label: "Chat Brainy" };
  }
  function showDetectedEvent(event) {
    const card = document.createElement("aside"); card.className = "event-detected";
    card.innerHTML = `<h4>✦ Événement détecté</h4><p><b>${event.title}</b><br>▣ ${formatDate(event.start.slice(0,10))} · ${event.start.slice(11,16)}</p><button>Ajouter au calendrier</button>`;
    $("#messages").append(card); card.querySelector("button").onclick = async () => { await saveEvent(event); toast("Événement ajouté", "Votre calendrier a été mis à jour."); card.remove(); };
  }
  async function sendMessage(text) {
    addMessage("user", text); const typing = $("#typing"); typing.classList.remove("hidden");
    try {
      const result = await api("/api/v1/chat", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message:text, history:state.history.slice(-8)}) });
      addMessage("assistant", result.text || result.response || "J'ai bien reçu votre message.");
      state.history.push({role:"user",content:text},{role:"assistant",content:result.text || result.response || ""});
      if (result.event) { await loadEvents(); renderCalendar(); toast("Événement ajouté au calendrier", result.event.title); }
    } catch (error) {
      toast("Réponse indisponible", error.message || "Vérifiez qu’Ollama est démarré, puis réessayez.");
    } finally { typing.classList.add("hidden"); }
  }
  const input = $("#message-input"); const send = $("#send-button");
  input.addEventListener("input", () => { input.style.height = "auto"; input.style.height = `${Math.min(input.scrollHeight,110)}px`; send.disabled = !input.value.trim(); });
  $("#chat-form").addEventListener("submit", async e => { e.preventDefault(); const message = input.value.trim(); if (!message) return; input.value=""; input.dispatchEvent(new Event("input")); await sendMessage(message); });
  $$("[data-prompt]").forEach(b => b.addEventListener("click", () => { input.value = b.dataset.prompt; input.dispatchEvent(new Event("input")); input.focus(); }));
  $("#clear-chat").onclick = () => { $("#messages").innerHTML = ""; state.history=[]; toast("Conversation effacée", "Vous pouvez commencer un nouveau sujet."); };
  $("#new-chat").onclick = () => { location.hash="#chat"; state.history=[]; $("#messages").innerHTML = `<div class="welcome-message"><div class="brain-avatar">B</div><h3>Nouvelle conversation</h3><p>Quelle notion souhaitez-vous explorer aujourd'hui ?</p></div>`; };

  function uploadModal(kind) {
    const image = kind === "image"; openModal(`<h2>${image ? "Importer une photo" : "Importer un document"}</h2><p>${image ? "Ajoutez une photo de cours, un tableau ou une capture. Le texte sera lu localement sur votre ordinateur." : "Ajoutez un PDF, DOCX, TXT, XLSX ou CSV pour l’intégrer à votre étude."}</p><label class="drop-zone">${image ? "◧" : "▣"}<strong>Glissez votre fichier ici</strong>ou sélectionnez-le<input id="upload-input" type="file" ${image ? "accept='image/png,image/jpeg,image/webp'" : "accept='.pdf,.docx,.txt,.xlsx,.csv'"} hidden></label><div id="file-preview"></div><div class="modal-actions"><button class="button secondary" id="modal-close">Annuler</button><button class="button primary" id="confirm-upload" disabled>Analyser</button></div>`);
    $("#modal-close").onclick=closeModal; const fileInput=$("#upload-input"); fileInput.parentElement.onclick=()=>fileInput.click();
    fileInput.onchange=()=> { const file=fileInput.files[0]; if (!file) return; const supported=image?["image/png","image/jpeg","image/webp" ]:["application/pdf","application/vnd.openxmlformats-officedocument.wordprocessingml.document","text/plain","text/csv","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]; if (!supported.includes(file.type) || file.size > 10 * 1024 * 1024) { $("#file-preview").textContent="Format non pris en charge ou fichier supérieur à 10 Mo."; $("#confirm-upload").disabled=true; return; } $("#file-preview").innerHTML=`<div class="file-preview">${image ? "◧" : "▣"} ${file.name} · ${(file.size/1024).toFixed(1)} Ko</div>`; $("#confirm-upload").disabled=false; };
    $("#confirm-upload").onclick=async()=> { const file=fileInput.files[0]; if (!file) return; $("#confirm-upload").textContent="Analyse…"; try { const form=new FormData(); form.append("file",file); const result=await api(image?"/vision/ingest":"/api/v1/documents",{method:"POST",body:form}); state.attachments.push(file.name); renderAttachments(); closeModal(); await loadEvents(); renderCalendar(); const added=result.events_added || 0; toast(added ? "Événement ajouté au calendrier" : (image ? "Photo analysée" : "Document analysé"), added ? `${added} événement${added > 1 ? "s" : ""} ajouté${added > 1 ? "s" : ""} au calendrier.` : "Le contenu a été ajouté à votre mémoire."); } catch(error) { $("#confirm-upload").textContent="Analyser"; toast("Import impossible", error.message || "Le fichier n’a pas pu être analysé."); } };
  }
  function renderAttachments(){ $("#attachment-row").innerHTML=state.attachments.map(n=>`<span class="attachment">▣ ${n}</span>`).join(""); }
  ["#document-button","#open-document"].forEach(s=>$(s).onclick=()=>uploadModal("document")); ["#image-button","#open-image"].forEach(s=>$(s).onclick=()=>uploadModal("image"));
  async function configureLocalOcr() {
    try {
      const health = await fetch("/health").then(response => response.json());
      if (health.local_ocr) return;
      ["#image-button", "#open-image"].forEach(selector => {
        const button = $(selector); button.disabled = true; button.title = "Import photo indisponible : installez Tesseract OCR localement."; button.classList.add("unavailable");
      });
    } catch { /* The backend returns a clear error if OCR availability cannot be checked. */ }
  }
  configureLocalOcr();

  function monthName(date){return new Intl.DateTimeFormat("fr-FR",{month:"long",year:"numeric"}).format(date).replace(/^./,c=>c.toUpperCase());}
  function eventDate(e){ return new Date(e.start); }
  function renderCalendar() {
    $("#month-label").textContent=monthName(state.month); const first=new Date(state.month.getFullYear(),state.month.getMonth(),1); const startOffset=(first.getDay()+6)%7; const start=new Date(first); start.setDate(1-startOffset);
    const today=new Date(); const cells=[]; for(let i=0;i<42;i++){ const d=new Date(start);d.setDate(start.getDate()+i);const key=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`; const events=state.events.filter(e=>e.start?.slice(0,10)===key); const classes=`day-cell ${d.getMonth()!==state.month.getMonth()?"other":""} ${key===today.toISOString().slice(0,10)?"today":""}`; cells.push(`<div class="${classes}" data-date="${key}"><span class="day-number">${d.getDate()}</span>${events.slice(0,2).map(e=>`<div class="event-pill ${normalizeType(e.category)}" data-event="${e.id}" title="${e.title}">${e.title}</div>`).join("")}${events.length>2?`<div class="event-pill">+${events.length-2} autres</div>`:""}</div>`); }
    $("#calendar-grid").innerHTML=cells.join(""); $$(".event-pill[data-event]").forEach(el=>el.onclick=e=>{e.stopPropagation();showEvent(state.events.find(x=>x.id===el.dataset.event));}); $$(".day-cell").forEach(el=>el.onclick=()=>eventModal({start:`${el.dataset.date}T09:00:00`}));
    const now=today.toISOString().slice(0,10), inWeek=new Date(today);inWeek.setDate(today.getDate()+7); const future=state.events.filter(e=>new Date(e.start)>=today).sort((a,b)=>new Date(a.start)-new Date(b.start));
    $("#calendar-stats").innerHTML=[[`Aujourd'hui`,state.events.filter(e=>e.start?.slice(0,10)===now).length,"À votre programme"],["Cette semaine",state.events.filter(e=>eventDate(e)>=today&&eventDate(e)<inWeek).length,"Gardez le rythme"],["Examens à venir",future.filter(e=>normalizeType(e.category)==="exam").length,"À préparer"],["Prochain événement",future[0]?.title||"Aucun",future[0]?formatDate(future[0].start.slice(0,10)):"Ajoutez une échéance"]].map(([a,b,c])=>`<article class="stat-card"><span>${a}</span><strong>${b}</strong><small>${c}</small></article>`).join("");
    $("#event-list").innerHTML=future.slice(0,5).map(e=>`<article class="event-list-item ${normalizeType(e.category)}" data-event="${e.id}"><h4>${e.title}</h4><p>${formatDate(e.start.slice(0,10))} · ${eventTime(e)}</p></article>`).join("")||"<p style='color:#8493aa;font-size:11px'>Aucun événement à venir.</p>"; $$(".event-list-item").forEach(el=>el.onclick=()=>showEvent(state.events.find(x=>x.id===el.dataset.event)));
  }
  function eventModal(existing={}) { const e={title:"",start:"",end:"",category:"Cours",description:"",location:"",...existing}; openModal(`<h2>${existing.id?"Modifier l'événement":"Nouvel événement"}</h2><label>Titre</label><input id="event-title" value="${e.title}"><label>Date et heure</label><input id="event-start" type="datetime-local" value="${e.start?.slice(0,16)||""}"><label>Type</label><select id="event-category">${Object.entries(types).map(([k,v])=>`<option ${e.category===v?"selected":""}>${v}</option>`).join("")}</select><label>Description</label><textarea id="event-description" rows="3">${e.description||""}</textarea><div class="modal-actions"><button class="button secondary" id="modal-close">Annuler</button><button class="button primary" id="save-event">Enregistrer</button></div>`); $("#modal-close").onclick=closeModal; $("#save-event").onclick=async()=>{const event={...e,title:$("#event-title").value.trim(),start:$("#event-start").value,category:$("#event-category").value,description:$("#event-description").value};if(!event.title||!event.start)return toast("Informations manquantes","Ajoutez un titre et une date.");if(e.id){state.events=state.events.filter(x=>x.id!==e.id);await deleteEvent(e);}await saveEvent(event);closeModal();renderCalendar();toast("Calendrier mis à jour",event.title);}; }
  function showEvent(e){if(!e)return;openModal(`<div class="event-details"><p class="eyebrow">${e.category||"Événement"}</p><h2>${e.title}</h2><dl><dt>Date</dt><dd>${formatDate(e.start.slice(0,10))}</dd><dt>Heure</dt><dd>${e.start.slice(11,16)}</dd><dt>Description</dt><dd>${e.description||"Aucune note ajoutée."}</dd></dl></div><div class="modal-actions"><button class="button secondary danger" id="delete-event">Supprimer</button><button class="button secondary" id="modal-close">Fermer</button><button class="button primary" id="edit-event">Modifier</button></div>`);$("#modal-close").onclick=closeModal;$("#edit-event").onclick=()=>eventModal(e);$("#delete-event").onclick=async()=>{await deleteEvent(e);closeModal();toast("Événement supprimé",e.title);};}
  // Re-declared here so the details panel stays compact and only shows fields
  // actually extracted from the source.
  showEvent = function(e){if(!e)return;openModal(`<div class="event-details"><p class="eyebrow">${e.category||"Événement"}</p><h2>${e.title}</h2><dl><dt>Date</dt><dd>${formatDate(e.start.slice(0,10))}</dd><dt>Heure</dt><dd>${eventTime(e)}</dd>${e.location?`<dt>Lieu</dt><dd>${e.location}</dd>`:""}<dt>Description</dt><dd>${e.description||"Aucune note ajoutée."}</dd></dl></div><div class="modal-actions"><button class="button secondary danger" id="delete-event">Supprimer</button><button class="button secondary" id="modal-close">Fermer</button><button class="button primary" id="edit-event">Modifier</button></div>`);$("#modal-close").onclick=closeModal;$("#edit-event").onclick=()=>eventModal(e);$("#delete-event").onclick=async()=>{await deleteEvent(e);closeModal();toast("Événement supprimé",e.title);};};
  $("#new-event").onclick=()=>eventModal(); $("#previous-month").onclick=()=>{state.month.setMonth(state.month.getMonth()-1);renderCalendar();}; $("#next-month").onclick=()=>{state.month.setMonth(state.month.getMonth()+1);renderCalendar();}; $("#today-button").onclick=()=>{state.month=new Date(new Date().getFullYear(),new Date().getMonth(),1);renderCalendar();}; $("#modal-backdrop").onclick=e=>{if(e.target.id==="modal-backdrop")closeModal();};
  loadEvents().then(renderCalendar);
})();
