/**
 * AI小说转剧本工具 - 前端交互逻辑
 * 零配置：内置免费模型，用户开箱即用
 */

// ===== 全局状态 =====
const state = {
    currentStep: 1,
    provider: "rule",
    file: null,
    chapters: [],
    yamlOutput: "",
    screenplay: null,
    models: []
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// ===== 初始化 =====
document.addEventListener("DOMContentLoaded", async () => {
    initUpload();
    initNavigation();
    initExport();
    await loadModels();
});

// ===== Demo模式数据 =====
const DEMO_MODELS = [
    { key: "rule", name: "规则引擎（离线免费）", description: "不需要任何API Key，纯规则转换，一键使用", api_base: "", model: "rule-engine", need_key: false, tag: "免费·推荐", has_builtin_key: false, builtin_key: "" },
    { key: "free_fast", name: "Groq 免费", description: "免费70B大模型，需注册获取API Key", api_base: "https://api.groq.com/openai/v1", model: "llama-3.3-70b-versatile", need_key: true, tag: "免费", has_builtin_key: false, builtin_key: "" },
    { key: "free_cn", name: "硅基流动", description: "国内平台，新用户送14元余额", api_base: "https://api.siliconflow.cn/v1", model: "Qwen/Qwen2.5-7B-Instruct", need_key: true, tag: "免费额度", has_builtin_key: false, builtin_key: "" },
    { key: "cheap", name: "DeepSeek", description: "注册送500万token，效果好", api_base: "https://api.deepseek.com/v1", model: "deepseek-chat", need_key: true, tag: "极便宜", has_builtin_key: false, builtin_key: "" }
];

const DEMO_YAML = `metadata:
  title: 命运的相遇
  genre: 言情
  source_chapters: 3
  total_scenes: 3
  characters:
  - 林雪
  - 苏云
  - 王老师
  version: '1.0'

scenes:
  - scene_number: 1
    scene_heading: INT. 大学教室 - DAY
    location: 大学教室
    scene_type: INT
    time_of_day: DAY
    characters:
    - 林雪
    - 王老师
    summary: 林雪在教室被老师提问
    lines:
      - line_type: action
        action:
          content: 阳光透过窗户洒在课桌上，林雪坐在靠窗的位置发呆。
      - line_type: dialogue
        dialogue:
          character: 王老师
          content: 林雪同学，请回答一下这个问题。
      - line_type: action
        action:
          content: 林雪慌张地站起身。
      - line_type: dialogue
        dialogue:
          character: 林雪
          parenthetical: 小声
          content: 对不起，老师，我没有听清。

  - scene_number: 2
    scene_heading: INT. 图书馆 - AFTERNOON
    location: 图书馆
    scene_type: INT
    time_of_day: DAY
    characters:
    - 林雪
    - 苏云
    summary: 林雪在图书馆遇到苏云
    lines:
      - line_type: action
        action:
          content: 林雪走到文学区的书架前，踮起脚尖想要拿最高层的一本书。
      - line_type: dialogue
        dialogue:
          character: 苏云
          content: 需要帮忙吗？
      - line_type: action
        action:
          content: 林雪转过头，看到一个高挑的男生正微笑着看着她。
      - line_type: dialogue
        dialogue:
          character: 林雪
          parenthetical: 微微脸红
          content: 谢谢，那本《百年孤独》。

  - scene_number: 3
    scene_heading: INT. 图书馆角落 - EVENING
    location: 图书馆角落
    scene_type: INT
    time_of_day: EVENING
    characters:
    - 林雪
    - 苏云
    summary: 两人发现共同爱好
    lines:
      - line_type: dialogue
        dialogue:
          character: 苏云
          content: 你也喜欢马尔克斯？他的魔幻现实主义真的很迷人。
      - line_type: dialogue
        dialogue:
          character: 林雪
          parenthetical: 眼睛亮了起来
          content: 是的！尤其是《百年孤独》，我已经读了三遍了。
      - line_type: dialogue
        dialogue:
          character: 苏云
          content: 我叫苏云，中文系的。你呢？
      - line_type: dialogue
        dialogue:
          character: 林雪
          content: 我叫林雪，外语系的。`;

// ===== 检测是否为Demo模式 =====
let isDemoMode = false;

// ===== 从后端加载内置模型列表 =====
async function loadModels() {
    try {
        const res = await fetch("/api/models");
        if (!res.ok) throw new Error("API not available");
        const data = await res.json();
        state.models = data.models;
        state.provider = data.default;
        renderProviderGrid(data.models, data.default);
    } catch (e) {
        console.log("后端不可用，启用Demo模式");
        isDemoMode = true;
        state.models = DEMO_MODELS;
        state.provider = "rule";
        renderProviderGrid(DEMO_MODELS, "rule");
        // 显示Demo模式提示
        const hint = document.createElement("div");
        hint.style.cssText = "background:#fef3c7;border:1px solid #fde68a;border-radius:8px;padding:10px 16px;margin-bottom:16px;font-size:0.85rem;color:#92400e;text-align:center;";
        hint.innerHTML = "⚡ <b>Demo模式</b> — 当前为在线预览，完整功能请本地运行 <code>python main.py</code>";
        const steps = $(".steps");
        if (steps) steps.parentNode.insertBefore(hint, steps.nextSibling);
    }
}

function renderProviderGrid(models, defaultKey) {
    const grid = $("#provider-grid");
    if (!grid) return;

    grid.innerHTML = models.map(m => `
        <button class="provider-btn ${m.key === defaultKey ? 'active' : ''}"
                data-provider="${m.key}"
                onclick="selectProvider('${m.key}')">
            <span class="provider-icon">${getProviderIcon(m.key)}</span>
            <span class="provider-name">${m.name}</span>
            <span class="provider-tag ${getTagClass(m.tag)}">${m.tag}</span>
        </button>
    `).join("");

    selectProvider(defaultKey);
}

function getProviderIcon(key) {
    const icons = {
        free_fast: "⚡", free_cn: "☁️", cheap: "🔮",
        ollama: "🦙", openai: "🤖", rule: "📐"
    };
    return icons[key] || "🔧";
}

function getTagClass(tag) {
    if (tag.includes("免费") || tag.includes("离线")) return "free";
    if (tag.includes("便宜")) return "cheap";
    return "paid";
}

// ===== 提供商选择 =====
function selectProvider(providerKey) {
    state.provider = providerKey;
    const model = state.models.find(m => m.key === providerKey);
    if (!model) return;

    $$(".provider-btn").forEach(b => b.classList.remove("active"));
    const btn = $(`.provider-btn[data-provider="${providerKey}"]`);
    if (btn) btn.classList.add("active");

    // 更新提示（带获取Key链接）
    let hint = `<p>💡 ${model.description}</p>`;
    if (model.need_key && !model.has_builtin_key) {
        const keyLinks = {
            free_fast: 'https://console.groq.com',
            free_cn: 'https://cloud.siliconflow.cn',
            cheap: 'https://platform.deepseek.com',
            openai: 'https://platform.openai.com'
        };
        const url = keyLinks[providerKey] || '#';
        hint = `<p>💡 ${model.description} — <a href="${url}" target="_blank" style="color:var(--primary)">点击获取免费 API Key →</a></p>`;
    }
    $("#provider-hint").innerHTML = hint;

    // 更新表单
    $("#api-base").value = model.api_base;
    $("#model").value = model.model;

    // 控制API配置区显隐 + 自动填充Key
    if (providerKey === "rule") {
        // 规则引擎：隐藏API配置区
        $("#api-config-section").classList.add("disabled");
        $("#api-key").value = "";
    } else if (model.has_builtin_key && model.builtin_key) {
        // 有内置Key：自动填充，用户可直接用
        $("#api-config-section").classList.remove("disabled");
        $("#api-key").value = model.builtin_key;
        $("#api-key").placeholder = "已自动填充内置Key";
    } else if (model.need_key) {
        // 需要Key但没有内置：提示用户填写
        $("#api-config-section").classList.remove("disabled");
        $("#api-key").value = "";
        $("#api-key").placeholder = "请输入你的 API Key";
    } else {
        // 不需要Key的模型（如Ollama本地）
        $("#api-config-section").classList.add("disabled");
        $("#api-key").value = "";
    }
}
// 暴露到全局，供onclick调用
window.selectProvider = selectProvider;

// ===== 文件上传 =====
function initUpload() {
    const uploadArea = $("#upload-area");
    const fileInput = $("#file-input");

    uploadArea.addEventListener("click", () => fileInput.click());

    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.classList.add("dragover");
    });

    uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragover"));

    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
    });

    $("#btn-remove").addEventListener("click", () => {
        state.file = null;
        state.chapters = [];
        $("#file-info").classList.add("hidden");
        $("#upload-area").classList.remove("hidden");
        $("#btn-next-1").disabled = true;
        $("#file-input").value = "";
    });
}

async function handleFile(file) {
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["txt", "docx"].includes(ext)) {
        return;
    }

    state.file = file;
    $("#file-name").textContent = file.name;
    $("#file-size").textContent = formatFileSize(file.size);
    $("#file-info").classList.remove("hidden");
    $("#upload-area").classList.add("hidden");

    // Demo模式：模拟章节解析
    if (isDemoMode) {
        const demoChapters = [
            { title: "第一章 命运的相遇", char_count: 312 },
            { title: "第二章 图书馆的秘密", char_count: 286 },
            { title: "第三章 约定", char_count: 258 }
        ];
        state.chapters = demoChapters;
        $("#chapter-list").innerHTML = demoChapters.map(ch =>
            `<div class="chapter-item">
                <span class="chapter-title">${ch.title}</span>
                <span class="chapter-chars">${ch.char_count} 字</span>
            </div>`
        ).join("");
        $("#btn-next-1").disabled = false;
        return;
    }

    try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch("/api/parse", { method: "POST", body: formData });
        if (!res.ok) {
            let detail = "解析失败";
            try { detail = (await res.json()).detail || detail; } catch(e) {}
            throw new Error(detail);
        }
        const data = await res.json();

        state.chapters = data.chapters;
        $("#chapter-list").innerHTML = data.chapters.map(ch =>
            `<div class="chapter-item">
                <span class="chapter-title">${ch.title}</span>
                <span class="chapter-chars">${ch.char_count} 字</span>
            </div>`
        ).join("");

        $("#btn-next-1").disabled = false;
    } catch (err) {
        console.warn("API解析失败:", err.message);
    }
}

// ===== 步骤导航 =====
function initNavigation() {
    $("#btn-next-1").addEventListener("click", () => goToStep(2));
    $("#btn-back-2").addEventListener("click", () => goToStep(1));
    $("#btn-next-2").addEventListener("click", startConversion);
    $("#btn-back-3").addEventListener("click", () => goToStep(2));
    $("#btn-back-4").addEventListener("click", () => goToStep(2));
    $("#btn-new").addEventListener("click", resetAll);
}

function goToStep(step) {
    $$(".section").forEach(s => s.classList.add("hidden"));
    $(`#step-${step}`).classList.remove("hidden");

    $$(".step").forEach(s => {
        const sn = parseInt(s.dataset.step);
        s.classList.remove("active", "done");
        if (sn === step) s.classList.add("active");
        else if (sn < step) s.classList.add("done");
    });

    state.currentStep = step;
}
window.goToStep = goToStep;

// ===== 开始转换 =====
async function startConversion() {
    const model = state.models.find(m => m.key === state.provider);

    // Demo模式：直接展示示例结果
    if (isDemoMode) {
        goToStep(3);
        const log = $("#conversion-log");
        const progressFill = $("#progress-fill");
        const progressText = $("#progress-text");
        log.innerHTML = "";
        progressFill.style.width = "0%";
        addLog("📐 Demo模式 — 展示示例转换结果", log);
        progressFill.style.width = "30%";
        progressText.textContent = "正在解析文件...";
        await sleep(500);
        addLog("📄 解析完成：3 章，856 字", log);
        progressFill.style.width = "60%";
        progressText.textContent = "正在转换中...";
        await sleep(500);
        addLog("📊 提取元数据：命运的相遇 / 言情", log);
        progressFill.style.width = "90%";
        progressText.textContent = "正在转换中 90%...";
        await sleep(500);
        progressFill.style.width = "100%";
        progressText.textContent = "转换完成！";
        addLog("🎉 转换完成！共生成 3 个场景", log, "success");
        state.yamlOutput = DEMO_YAML;
        state.screenplay = { title: "命运的相遇", characters: ["林雪", "苏云", "王老师"] };
        setTimeout(() => showResult({ yaml: DEMO_YAML, scene_count: 3, metadata: state.screenplay }), 800);
        return;
    }

    // 规则引擎模式
    if (state.provider === "rule") {
        await startRuleConversion();
        return;
    }

    // AI模式
    const userApiKey = $("#api-key").value.trim();
    const apiBase = $("#api-base").value.trim();
    const modelName = $("#model").value.trim();
    const novelTitle = $("#novel-title").value.trim();

    goToStep(3);
    const log = $("#conversion-log");
    const progressFill = $("#progress-fill");
    const progressText = $("#progress-text");
    log.innerHTML = "";
    progressFill.style.width = "0%";

    try {
        addLog(`🚀 正在使用 ${model?.name || state.provider} 一键转换...`, log);

        const formData = new FormData();
        formData.append("file", state.file);
        formData.append("provider", state.provider);
        formData.append("api_key", userApiKey);
        formData.append("api_base", apiBase);
        formData.append("model", modelName);
        formData.append("novel_title", novelTitle);
        formData.append("batch_size", 3);

        const res = await fetch("/api/convert/stream", { method: "POST", body: formData });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                try {
                    handleStreamEvent(JSON.parse(line.slice(6)), log, progressFill, progressText);
                } catch (e) {}
            }
        }
    } catch (err) {
        addLog(`❌ 错误: ${err.message}`, log, "error");
    }
}

// ===== 规则引擎转换 =====
async function startRuleConversion() {
    goToStep(3);
    const log = $("#conversion-log");
    const progressFill = $("#progress-fill");
    const progressText = $("#progress-text");
    log.innerHTML = "";
    progressFill.style.width = "10%";

    addLog("📐 使用规则引擎模式（离线免费）...", log);
    addLog("📄 正在解析文件...", log);
    progressFill.style.width = "20%";
    progressText.textContent = "解析中...";

    try {
        addLog("⚙️ 正在应用规则转换...", log);
        progressFill.style.width = "50%";
        progressText.textContent = "规则转换中...";

        const formData = new FormData();
        formData.append("file", state.file);
        formData.append("novel_title", $("#novel-title").value.trim());

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 25000);

        const res = await fetch("/api/convert/rule", {
            method: "POST",
            body: formData,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (!res.ok) {
            let detail = "转换失败";
            try { detail = (await res.json()).detail || detail; } catch(e) {}
            throw new Error(detail);
        }
        const data = await res.json();

        progressFill.style.width = "100%";
        progressText.textContent = "转换完成！";
        addLog(`✅ 规则转换完成！生成 ${data.scene_count} 个场景`, log, "success");

        state.yamlOutput = data.yaml;
        state.screenplay = data.metadata;
        setTimeout(() => showResult(data), 1000);
    } catch (err) {
        addLog(`❌ 错误: ${err.message}`, log, "error");
        progressText.textContent = "转换失败";
    }
}

function handleStreamEvent(event, log, progressFill, progressText) {
    switch (event.step) {
        case "parsing":
            progressText.textContent = "正在解析文件...";
            progressFill.style.width = "10%";
            break;
        case "parsed":
            addLog(`📄 ${event.detail}`, log);
            progressFill.style.width = "20%";
            break;
        case "metadata":
            addLog(`📊 ${event.detail}`, log);
            progressFill.style.width = "30%";
            break;
        case "converting":
            const pct = 30 + (event.current / event.total * 65);
            progressFill.style.width = pct + "%";
            progressText.textContent = `正在转换中 ${Math.round(pct)}%...`;
            break;
        case "chapter_done":
            // 静默处理，不显示每批细节
            break;
        case "done":
            progressFill.style.width = "100%";
            progressText.textContent = "转换完成！";
            addLog(`🎉 转换完成！共生成 ${event.scene_count} 个场景`, log, "success");
            state.yamlOutput = event.yaml;
            state.screenplay = event.metadata;
            setTimeout(() => showResult(event), 1000);
            break;
        case "error":
            addLog(`❌ ${event.detail}`, log, "error");
            progressText.textContent = "转换失败";
            break;
    }
}

// ===== 结果展示 =====
function showResult(event) {
    goToStep(4);
    $("#yaml-output").textContent = event.yaml;
    $("#stat-scenes").textContent = `${event.scene_count} 个场景`;
    const charCount = event.metadata?.characters?.length || 0;
    $("#stat-chars").textContent = `${charCount} 个角色`;
}

// ===== 导出 =====
function initExport() {
    $("#btn-copy").addEventListener("click", () => {
        navigator.clipboard.writeText(state.yamlOutput).then(() => {
            const btn = $("#btn-copy");
            btn.textContent = "✅ 已复制";
            setTimeout(() => btn.textContent = "📋 复制YAML", 2000);
        });
    });

    $("#btn-download").addEventListener("click", () => {
        const blob = new Blob([state.yamlOutput], { type: "text/yaml;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = (state.screenplay?.title || "screenplay") + ".yaml";
        a.click();
        URL.revokeObjectURL(url);
    });
}

// ===== 重置 =====
function resetAll() {
    state.file = null;
    state.chapters = [];
    state.yamlOutput = "";
    state.screenplay = null;
    $("#file-input").value = "";
    $("#api-key").value = "";
    $("#novel-title").value = "";
    $("#file-info").classList.add("hidden");
    $("#upload-area").classList.remove("hidden");
    $("#btn-next-1").disabled = true;
    goToStep(1);
}

// ===== 工具函数 =====
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function addLog(text, container, type = "") {
    const div = document.createElement("div");
    div.className = "log-entry" + (type ? " " + type : "");
    div.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}
