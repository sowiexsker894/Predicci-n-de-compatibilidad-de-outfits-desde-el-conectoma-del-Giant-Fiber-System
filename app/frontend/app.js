// Frontend del dashboard de Modelo Fly: habla con la API de app/backend/main.py.

const TONOS = {
  negro: "#1F1F1F", blanco: "#FFFFFF", beige: "#D9C3A0", azul: "#2F5DA8", dorado: "#C9A227", gris: "#8C8C8C",
  rojo: "#C0392B", marron: "#7B4A2A", rosa: "#E89BB5", plateado: "#C8CCD0", crema: "#F3E6CC", amarillo: "#F2C94C",
  verde: "#3E8E41", naranja: "#E8710A", teal: "#1F8A8A", morado: "#7D4BA8",
};
const SLOTS = {
  exterior: "Abrigo", arriba: "Parte de arriba", vestido: "Vestido", abajo: "Parte de abajo",
  calzado: "Calzado", bolso: "Bolso", accesorio: "Accesorio", joyeria: "Joyería",
};
const CLIMA = { frio: "frío", templado: "templado", calido: "cálido" };

const $ = (s) => document.querySelector(s);
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = (x) => `${Math.round(x * 100)} %`;
const dec = (x, n = 3) => Number(x).toFixed(n).replace(".", ",");

let usuarios = [];
let actual = null;
let closet = [];
let filtroSlot = "todos";

async function api(ruta, opciones) {
  const r = await fetch(ruta, opciones);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
}

// ---------- estado del servidor ----------
async function vigilarEstado() {
  const caja = $("#estado");
  try {
    const e = await api("/api/estado");
    $("#pie-bd").textContent = e.bd;
    if (e.estado === "cargando") {
      caja.className = "estado cargando"; caja.textContent = "Cargando modelo y BD…";
    } else if (e.estado === "error") {
      caja.className = "estado error"; caja.textContent = "Error al cargar"; caja.title = e.error;
    } else if (e.error_escritura) {
      caja.className = "estado error"; caja.textContent = "No se pudo guardar en la BD"; caja.title = e.error_escritura;
    } else if (e.escrituras_pendientes > 0) {
      caja.className = "estado guardando"; caja.textContent = `Guardando en la BD (${e.escrituras_pendientes})…`;
      caja.title = "El Excel tarda 2–3 min en guardarse; puedes seguir usando el dashboard";
    } else {
      caja.className = "estado listo";
      caja.textContent = e.ultima_escritura ? `BD al día · ${e.ultima_escritura}` : "Listo";
      caja.title = `${e.experimento} · α = ${e.alfa}, β = ${e.beta}`;
    }
    if (e.estado === "listo" && !usuarios.length) await iniciar();
  } catch {
    caja.className = "estado error"; caja.textContent = "Sin conexión con el backend";
  }
  setTimeout(vigilarEstado, 3000);
}

async function iniciar() {
  usuarios = await api("/api/usuarios");
  $("#buscar").disabled = false;
  pintarLista();
  cargarResumen();
  const enlace = decodeURIComponent(location.hash.slice(1));
  if (enlace === "resultados") document.querySelector('.pestana[data-vista="resultados"]').click();
  else if (usuarios.some((u) => u.user_id === enlace)) abrirUsuario(enlace);
}

// ---------- lista de usuarios ----------
function pintarLista() {
  const q = $("#buscar").value.trim().toLowerCase();
  const visibles = usuarios.filter((u) =>
    !q || [u.user_id, u.ciudad, u.estilo_fav, u.grupo].some((v) => String(v).toLowerCase().includes(q)));
  $("#lista-usuarios").innerHTML = visibles.slice(0, 120).map((u) => `
    <li><button data-id="${esc(u.user_id)}" class="${u.user_id === actual ? "activo" : ""}">
      <span>${esc(u.user_id)}</span><small>${esc(u.ciudad)} · ${esc(u.estilo_fav)}</small>
    </button></li>`).join("") || `<li class="nota">Sin resultados</li>`;
}

$("#buscar").addEventListener("input", pintarLista);
$("#lista-usuarios").addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-id]");
  if (b) abrirUsuario(b.dataset.id);
});

// ---------- un usuario ----------
async function abrirUsuario(id) {
  actual = id;
  history.replaceState(null, "", `#${encodeURIComponent(id)}`);
  pintarLista();
  const d = await api(`/api/usuarios/${encodeURIComponent(id)}`);
  const p = d.perfil;
  $("#bienvenida").classList.add("oculto");
  $("#panel-usuario").classList.remove("oculto");
  $("#titulo-usuario").textContent = `Usuario ${p.user_id}`;
  $("#sub-usuario").textContent = `${p.n_closet} prendas en su clóset · ${d.historial.aceptados} de ${d.historial.outfits_vistos} outfits aceptados en su historial`;
  $("#perfil").classList.remove("oculto");
  $("#perfil").innerHTML = `
    <span class="etiqueta">Perfil</span>
    <dl>
      <dt>Edad</dt><dd>${esc(p.edad)} años</dd>
      <dt>Ciudad</dt><dd>${esc(p.ciudad)}</dd>
      <dt>Clima</dt><dd>${esc(CLIMA[p.clima] || p.clima)}</dd>
      <dt>Estilo favorito</dt><dd>${esc(p.estilo_fav)}</dd>
      <dt>Clóset</dt><dd>${p.grupo === "mixto" ? "mixto (Polyvore + propio)" : "100 % catálogo propio"}</dd>
    </dl>`;
  $("#recomendaciones").innerHTML = "";
  $("#previas").innerHTML = d.recomendaciones_previas.map((o) => tarjetaOutfit(o, false)).join("")
    || `<p class="nota">Todavía no tiene recomendaciones. Pulsa «Recomendar 3 outfits».</p>`;
  closet = d.closet;
  filtroSlot = "todos";
  pintarCloset();
}

$("#btn-recomendar").addEventListener("click", async () => {
  const btn = $("#btn-recomendar");
  btn.disabled = true; btn.textContent = "Buscando en su clóset…";
  try {
    const outfits = await api(`/api/usuarios/${encodeURIComponent(actual)}/recomendar`, { method: "POST" });
    $("#recomendaciones").innerHTML = outfits.map((o) => tarjetaOutfit(o, true)).join("");
  } catch (e) {
    $("#recomendaciones").innerHTML = `<p class="nota">No se pudo recomendar: ${esc(e.message)}</p>`;
  } finally {
    btn.disabled = false; btn.textContent = "Recomendar otros 3";
  }
});

function prenda(it) {
  const color = TONOS[it.tono];
  const detalle = [SLOTS[it.slot] || it.slot, it.tono, it.material, it.estilo]
    .filter((v) => v && v !== "desconocido").join(" · ");
  return `<li class="prenda">
    <span class="muestra ${color ? "" : "desconocido"}" style="${color ? `background:${color}` : ""}" title="${esc(it.tono)}"></span>
    <span class="prenda-txt"><b title="${esc(it.name)}">${esc(it.name)}</b><small>${esc(detalle)}</small></span>
  </li>`;
}

function tarjetaOutfit(o, nuevo) {
  const fecha = o.fecha.replace("T", " ").slice(0, 16);
  const marca = (v) => (o.aceptado === v ? "marcado" : "");
  return `<article class="outfit ${nuevo ? "nuevo" : ""}" data-outfit="${esc(o.outfit_id)}">
    <div class="outfit-cab">
      <span class="rango">${o.rango}</span>
      <div><h4>Outfit ${o.rango}</h4><small>${esc(fecha)} · puntaje ${dec(o.score_final)}</small></div>
    </div>
    <ul class="prendas">${o.prendas.map(prenda).join("")}</ul>
    <div class="puntajes">
      <div class="puntaje" title="Fase 1 · DeepFM: probabilidad de que le guste según su historial"><b>${pct(o.p_deepfm)}</b><small>Su gusto</small></div>
      <div class="puntaje" title="Fase 2 · TTMn: probabilidad de que el outfit sea real (lo armaría una persona)"><b>${pct(o.p_ttmn)}</b><small>Parece real</small></div>
      <div class="puntaje" title="Fase 2 · DLMn: reglas de armonía cumplidas (0–7)"><b>${dec(o.dlmn, 1)}/7</b><small>Armonía</small></div>
    </div>
    <div class="opinion" role="group" aria-label="¿Te gusta este outfit?">
      <button class="si ${marca(1)}" data-valor="1">Me gusta</button>
      <button class="no ${marca(0)}" data-valor="0">No me gusta</button>
    </div>
  </article>`;
}

document.addEventListener("click", async (ev) => {
  const b = ev.target.closest(".opinion button");
  if (!b) return;
  const tarjeta = b.closest(".outfit");
  const aceptado = b.dataset.valor === "1";
  try {
    await api("/api/opiniones", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ outfit_id: tarjeta.dataset.outfit, aceptado }),
    });
    document.querySelectorAll(`.outfit[data-outfit="${CSS.escape(tarjeta.dataset.outfit)}"] .opinion button`).forEach((x) =>
      x.classList.toggle("marcado", x.dataset.valor === b.dataset.valor));
  } catch (e) {
    alert(`No se pudo guardar la opinión: ${e.message}`);
  }
});

// ---------- clóset ----------
function pintarCloset() {
  const slots = [...new Set(closet.map((i) => i.slot))];
  $("#n-closet").textContent = `(${closet.length} prendas)`;
  $("#filtros-slot").innerHTML = ["todos", ...slots].map((s) =>
    `<button data-slot="${esc(s)}" class="${s === filtroSlot ? "activo" : ""}">${s === "todos" ? "Todas" : esc(SLOTS[s] || s)}</button>`).join("");
  const visibles = closet.filter((i) => filtroSlot === "todos" || i.slot === filtroSlot);
  $("#closet").innerHTML = visibles.map(prenda).join("");
}

$("#filtros-slot").addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-slot]");
  if (b) { filtroSlot = b.dataset.slot; pintarCloset(); }
});

// ---------- resultados ----------
async function cargarResumen() {
  const r = await api("/api/resumen");
  const NOMBRES = { azar: "Azar (sin modelo)", techo: "Techo (gusto real)" };
  const filas = r.ranking.map((f) => ({ ...f, nombre: NOMBRES[f.experimento]
    || (f.experimento === "anexo" ? `Anexo · ${f.modelo}` : `${f.experimento} · ${f.modelo}`) }));
  $("#grafico-ranking").innerHTML = filas.map((f) => {
    const clase = String(f.experimento) === "3" ? "destacada" : f.modelo.includes("GFS (A)") ? "gfs" : f.experimento in NOMBRES ? "ref" : "";
    return `<div class="barra ${clase}" title="${esc(f.nombre)}: NDCG@5 = ${dec(f.valor)}">
      <span class="barra-nombre">${esc(f.nombre)}</span>
      <span class="barra-pista"><span class="barra-relleno" style="width:${(f.valor * 100).toFixed(1)}%">
        <span class="barra-valor">${dec(f.valor)}</span></span></span>
    </div>`;
  }).join("");
  $("#tabla-ranking").innerHTML = `<tr><th>Experimento</th><th>NDCG@5</th></tr>` +
    filas.map((f) => `<tr><td>${esc(f.nombre)}</td><td>${dec(f.valor)}</td></tr>`).join("");
  $("#impacto").innerHTML = r.impacto.map((i) => `
    <div class="dato"><b>${esc(i.valor.replace(/(\d)\.(\d)/g, "$1,$2"))}</b><p>${esc(i.indicador)}</p><small>${/^\d/.test(i.meta_ods) ? `Meta ODS ${esc(i.meta_ods)}` : esc(i.meta_ods)}</small></div>`).join("");
}

// ---------- pestañas ----------
document.querySelectorAll(".pestana").forEach((t) => t.addEventListener("click", () => {
  document.querySelectorAll(".pestana").forEach((x) => {
    x.classList.toggle("activa", x === t); x.setAttribute("aria-selected", x === t);
  });
  $("#vista-closet").classList.toggle("oculto", t.dataset.vista !== "closet");
  $("#vista-resultados").classList.toggle("oculto", t.dataset.vista !== "resultados");
}));

vigilarEstado();
