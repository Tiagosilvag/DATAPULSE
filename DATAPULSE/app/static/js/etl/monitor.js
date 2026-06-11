// ======================================
// ESTADO GLOBAL
// ======================================
let paginaAtual = 1;
let grafico = null;
let baseSelecionada = null;


// ======================================
// UTIL
// ======================================
function setText(selector, value) {
    const el = document.querySelector(selector);
    if (el) el.innerText = value;
}


// ======================================
// FETCH
// ======================================
async function fetchJSON(url) {
    try {
        const resp = await fetch(url, { credentials: "include" });
        const text = await resp.text();

        if (text.startsWith("<!DOCTYPE")) {
            console.error("Sessão expirada");
            return null;
        }

        return JSON.parse(text);

    } catch (err) {
        console.error("Erro fetch:", err);
        return null;
    }
}


// ======================================
// PROCESSAMENTO CENTRAL (🔥 CORE)
// ======================================
function renderTudo(data) {
    if (!data) return;

    atualizarMetricas(data.metrics);
    atualizarPipeline(data.pipeline);
    atualizarDetalhes(data.detalhe);
    atualizarGrafico(data.volumetria);
    atualizarValidacao(data.validacao);
    atualizarLogs(data.logs);
}


// ======================================
// BOTÕES DISPARO (ROBUSTO)
// ======================================
function configurarEventosGlobais() {

    document.addEventListener("click", (e) => {

        // ✅ marcar todas
        if (e.target.id === "btn-all") {
            document.querySelectorAll('#bases-list input[type="checkbox"]')
                .forEach(c => c.checked = true);
        }

        // ✅ limpar
        if (e.target.id === "btn-clear") {
            document.querySelectorAll('#bases-list input[type="checkbox"]')
                .forEach(c => c.checked = false);
        }

        // ✅ clique na fila
        const linha = e.target.closest(".linha-fila");
        if (linha) {

            document.querySelectorAll(".linha-fila")
                .forEach(l => l.classList.remove("ativa"));

            linha.classList.add("ativa");

            carregarBase(linha.dataset.base);
        }
    });
}


// ======================================
// METRICAS
// ======================================
function atualizarMetricas(m = {}) {
    setText("#metric-total", m.total || 0);
    setText("#metric-concluidas", m.concluidas || 0);
    setText("#metric-executando", m.executando || 0);
    setText("#metric-pendentes", m.pendentes || 0);
    setText("#metric-falhas", m.falhas || 0);

    atualizarProgressoGeral(m);
}


// ======================================
// PROGRESSO
// ======================================
function atualizarProgressoGeral(m) {

    const total = m.total || 1;
    const done = m.concluidas || 0;
    const pct = Math.round((done / total) * 100);

    setText("#metric-progresso", pct + "%");

    const circle = document.getElementById("progress-circle");
    const text = document.getElementById("progress-text");

    if (!circle || !text) return;

    const radius = 24;
    const circ = 2 * Math.PI * radius;
    const offset = circ - (pct / 100) * circ;

    circle.style.strokeDasharray = circ;
    circle.style.strokeDashoffset = offset;

    text.innerText = pct + "%";
}


// ======================================
// STATUS
// ======================================
function formatarStatus(s) {
    if (s === "concluido") return "Concluído";
    if (s === "executando") return "Executando";
    if (s === "falha") return "Falha";
    return "Pendente";
}


// ======================================
// FILA
// ======================================
async function carregarFila() {

    const data = await fetchJSON(`/etl/fila?page=${paginaAtual}`);
    if (!data || !data.dados) return;

    const tbody = document.getElementById("fila-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    data.dados.forEach(item => {

        const tr = document.createElement("tr");
        tr.classList.add("linha-fila");
        tr.dataset.base = item.base;

        // ✅ mantém seleção visual
        if (item.base === baseSelecionada) {
            tr.classList.add("ativa");
        }

        tr.innerHTML = `
            <td>${item.ordem}</td>

            <td>
                <div class="base-cell">
                    <i data-lucide="database"></i>
                    <div class="base-info">
                        <div class="base-title">${item.base}</div>
                    </div>
                </div>
            </td>

            <td>
                <span class="status-badge ${item.status}">
                    <i data-lucide="${
                        item.status === "concluido" ? "check-circle" :
                        item.status === "executando" ? "loader" :
                        item.status === "falha" ? "x-circle" : "clock"
                    }"></i>
                    ${formatarStatus(item.status)}
                </span>
            </td>

            <td>${item.data_execucao}</td>
            <td>${item.dt_inicio}</td>
            <td>${item.dt_fim}</td>
            <td>${item.duracao}</td>
            <td>${item.qtd}</td>
        `;

        tbody.appendChild(tr);
    });

    // ✅ recria ícones
    if (window.lucide) {
        lucide.createIcons();
    }

    // ✅ paginação correta
    setText("#pagina-atual", `Página ${data.page} de ${data.total_paginas}`);

    // ✅ define base inicial APENAS UMA VEZ
    if (!baseSelecionada && data.dados.length > 0) {
        baseSelecionada = data.dados[0].base;
        carregarBase(baseSelecionada);
    }
}

// ======================================
// BASE
// ======================================
async function carregarBase(base) {

    baseSelecionada = base;

    const input = document.getElementById("anomes");
    const anoMes = input && input.value
        ? input.value.replace("-", "")
        : null;

    const data = await fetchJSON(`/etl/monitor/data?base=${base}&ano_mes=${anoMes}`);
    if (!data) return;

    renderTudo(data); // ✅ único ponto de render
}


// ======================================
// PIPELINE
// ======================================
function atualizarPipeline(pipeline = []) {
    const box = document.getElementById("pipeline");
    if (!box) return;

    if (!pipeline.length) {
        box.innerHTML = `<div class="pipeline-loading">Sem dados</div>`;
        return;
    }

    box.innerHTML = "";

    pipeline.forEach(step => {

        const status = (step.status || "pendente").toLowerCase();

        const icon =
            status === "concluido" ? "✔" :
            status === "executando" ? "⏳" :
            status === "falha" ? "⚠" :
            "○";

        const div = document.createElement("div");
        div.className = `pipeline-step ${status}`;

        div.innerHTML = `
            <div class="pipeline-icon">${icon}</div>
            <div class="pipeline-title">${step.ordem}. ${step.nome}</div>
        `;

        box.appendChild(div);
    });
}


// ======================================
// LOGS
// ======================================
function atualizarLogs(lista = []) {

    const box = document.getElementById("logs-container");
    if (!box) return;

    if (!lista.length) {
        box.innerHTML = `<div class="logs-loading">Nenhum log</div>`;
        return;
    }

    box.innerHTML = "";

    lista.forEach(log => {

        const div = document.createElement("div");
        div.className = `log-item log-${(log.nivel || "info").toLowerCase()}`;

        div.innerHTML = `
            <span>[${log.hora}]</span>
            <span><b>${log.nivel}</b> - ${log.mensagem}</span>
        `;

        box.appendChild(div);
    });
}


// ======================================
// DETALHES
// ======================================
function atualizarDetalhes(d) {

    if (!d) return;

    setText("#exec-inicio", d.inicio || "-");
    setText("#exec-tempo", d.tempo || "-");
    setText("#exec-previsao", d.previsao || "-");

    setText("#exec-status", d.status || "-");
    setText("#exec-etapa", d.etapa || "-");
    setText("#exec-base", d.base || "-");
}


// ======================================
// VALIDAÇÃO
// ======================================
function atualizarValidacao(v) {

    if (!v) return;

    const alertBox = document.getElementById("val-alert");
    if (alertBox) {
        alertBox.style.display = v.status === "divergente" ? "block" : "none";
    }

    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
    };

    set("val-backup", v.qtd_backup?.toLocaleString() || "-");
    set("val-atual", v.qtd_atual?.toLocaleString() || "-");
    set("val-diff", v.diferenca?.toLocaleString() || "-");
    set("val-var", v.variacao != null ? v.variacao + "%" : "-");
}


// ======================================
// GRÁFICO
// ======================================
function atualizarGrafico(v) {

    const ctx = document.getElementById("grafico-volume");
    if (!ctx || !v || !v.atual || v.atual.length === 0) return;

    if (grafico) grafico.destroy();

    const maxValor = Math.max(...v.atual);

    // ✅ cor dinâmica (destaca queda)
    const cores = v.atual.map((valor, i, arr) => {
        if (i === 0) return "#3b82f6";
        return valor < arr[i - 1] ? "#ef4444" : "#22c55e";
    });

    grafico = new Chart(ctx, {
        type: "line",
        data: {
            labels: v.labels,
            datasets: [
                {
                    label: "Volume",
                    data: v.atual,
                    borderColor: "#ef4444",
                    backgroundColor: "rgba(239,68,68,0.08)",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: cores
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: ctx => "Volume: " + ctx.raw.toLocaleString()
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        autoSkip: true,
                        maxRotation: 0
                    }
                },
                y: {
                    beginAtZero: true,
                    suggestedMax: maxValor * 1.1,
                    ticks: {
                        callback: value => value.toLocaleString()
                    }
                }
            }
        }
    });
}


// ======================================
// REALTIME
// ======================================
async function atualizarTudo() {

    const data = await fetchJSON("/etl/monitor/data");
    if (!data) return;

    atualizarMetricas(data.metrics);

    if (baseSelecionada) {
        atualizarLogs(data.logs); // ✅ só logs
    }
}
// ======================================
// PAGINAÇÃO (🔥 FALTAVA ISSO)
// ======================================
window.mudarPagina = function (dir) {

    paginaAtual += dir;

    if (paginaAtual < 1) {
        paginaAtual = 1;
    }

    carregarFila();
};


// ======================================
// INIT
// ======================================
document.addEventListener("DOMContentLoaded", () => {

    configurarEventosGlobais();
    carregarFila();

    setInterval(atualizarTudo, 5000);
});