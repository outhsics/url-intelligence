const form = document.querySelector("#analyze-form");
const urlInput = document.querySelector("#url-input");
const fillDemoButton = document.querySelector("#fill-demo");
const quickPickButtons = document.querySelectorAll(".chip");
const statusCard = document.querySelector("#status-card");
const statusTitle = document.querySelector(".status-title");
const statusText = document.querySelector(".status-text");
const resultTitle = document.querySelector("#result-title");
const resultSubtitle = document.querySelector("#result-subtitle");
const sourcePill = document.querySelector("#source-pill");
const metaAuthor = document.querySelector("#meta-author");
const metaPublished = document.querySelector("#meta-published");
const metaLanguage = document.querySelector("#meta-language");
const metaImages = document.querySelector("#meta-images");
const contentPreview = document.querySelector("#content-preview");
const contentKind = document.querySelector("#content-kind");
const copyContentButton = document.querySelector("#copy-content");
const analysisCard = document.querySelector("#analysis-card");
const analysisSummary = document.querySelector("#analysis-summary");
const analysisPoints = document.querySelector("#analysis-points");
const analysisEntities = document.querySelector("#analysis-entities");
const analysisRisks = document.querySelector("#analysis-risks");
const analysisQuestions = document.querySelector("#analysis-questions");

fillDemoButton.addEventListener("click", () => {
  urlInput.value = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
  urlInput.focus();
});

copyContentButton.addEventListener("click", async () => {
  const text = contentPreview.textContent?.trim();
  if (!text || text === "结果会显示在这里。") {
    setError("没有可复制内容", "先提取一个链接，再复制全文。");
    return;
  }

  try {
    await copyText(text);
    const oldLabel = copyContentButton.textContent;
    copyContentButton.textContent = "已复制";
    copyContentButton.disabled = true;
    window.setTimeout(() => {
      copyContentButton.textContent = oldLabel;
      copyContentButton.disabled = false;
    }, 1500);
    setReady("全文已复制", "正文 / 字幕的完整文本已经复制到剪贴板。");
  } catch (error) {
    setError("复制失败", "浏览器没有完成复制，请重试。");
  }
});

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch (error) {
      // Fall through to the legacy copy path for in-app browsers.
    }
  }

  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "fixed";
  textArea.style.opacity = "0";
  textArea.style.pointerEvents = "none";
  textArea.style.left = "-9999px";
  textArea.style.top = "0";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  textArea.setSelectionRange(0, text.length);

  const copied = document.execCommand("copy");
  document.body.removeChild(textArea);

  if (!copied) {
    throw new Error("copy failed");
  }
}

for (const button of quickPickButtons) {
  button.addEventListener("click", () => {
    urlInput.value = button.dataset.url || "";
    urlInput.focus();
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitter = event.submitter;
  const mode = submitter?.dataset.mode || "extract";
  const url = urlInput.value.trim();

  if (!url) {
    setError("还没输入链接。", "先粘贴一个微信公众号、X、YouTube 或网页链接。");
    return;
  }

  setLoading(
    mode === "analyze" ? "正在提取并分析" : "正在提取内容",
    "请求已经发给本地服务，通常几秒内会返回。"
  );

  try {
    const endpoint = mode === "analyze" ? "/extract-and-analyze" : "/extract";
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "请求失败");
    }

    const content = payload.content || payload;
    const analysis = payload.analysis || null;
    renderContent(content, analysis);
    setReady(
      analysis ? "提取和分析已完成" : "提取已完成",
      analysis
        ? "页面已经拿到结构化正文和 AI 分析结果。"
        : "页面已经拿到结构化正文，你可以继续切到“提取并分析”。"
    );
  } catch (error) {
    setError("请求失败", error.message || "未知错误");
  }
});

function renderContent(content, analysis) {
  resultTitle.textContent = content.title || "未提取到标题";
  resultSubtitle.textContent = content.url || "-";
  sourcePill.textContent = content.source_type || "-";
  metaAuthor.textContent = content.author || "-";
  metaPublished.textContent = content.published_at || "-";
  metaLanguage.textContent = content.language || "-";
  metaImages.textContent = String((content.images || []).length);
  contentKind.textContent = content.transcript ? "正文 + 字幕" : "正文";
  contentPreview.textContent = content.markdown || content.transcript || "没有提取到正文。";

  if (!analysis) {
    analysisCard.classList.add("hidden");
    return;
  }

  analysisCard.classList.remove("hidden");
  analysisSummary.textContent = analysis.summary || "-";
  fillList(analysisPoints, analysis.key_points);
  fillList(analysisEntities, analysis.entities);
  fillList(analysisRisks, analysis.risks);
  fillList(analysisQuestions, analysis.suggested_questions);
}

function fillList(node, items) {
  node.innerHTML = "";
  const safeItems = items && items.length ? items : ["-"];
  for (const item of safeItems) {
    const li = document.createElement("li");
    li.textContent = item;
    node.appendChild(li);
  }
}

function setLoading(title, text) {
  statusCard.classList.add("is-loading");
  statusCard.classList.remove("is-error");
  statusTitle.textContent = title;
  statusText.textContent = text;
}

function setReady(title, text) {
  statusCard.classList.remove("is-loading");
  statusCard.classList.remove("is-error");
  statusTitle.textContent = title;
  statusText.textContent = text;
}

function setError(title, text) {
  statusCard.classList.remove("is-loading");
  statusCard.classList.add("is-error");
  statusTitle.textContent = title;
  statusText.textContent = text;
}
