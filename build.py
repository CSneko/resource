import os
import json
import hashlib
import markdown
import shutil
import re
from PIL import Image  # 用于生成缩略图

# =========================
# HTML 模板（已修改 JavaScript）
# =========================

template = """
<html>
<head>
<meta charset="utf-8">
<title>{full_path} - CrystalNekoの资源站</title>

<style>
html, body {{
    margin: 0;
    padding: 0;
    min-height: 100vh;
    background-size: cover;
    background-position: center;
}}

body {{
    background: url('https://www.loliapi.com/acg') fixed;
    font-family: Arial, sans-serif;
}}

.container {{
    max-width: 800px;
    margin: 20px auto;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 0 20px rgba(0,0,0,0.2);
}}

.entry {{
    text-decoration: none !important;
    color: #333 !important;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    margin: 8px 0;
    background: rgba(245, 245, 245, 0.9);
    border-radius: 8px;
    transition: all 0.3s;
    cursor: pointer;
}}

.entry:hover {{
    transform: translateX(10px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    background: rgba(235, 245, 255, 0.9);
}}

.file-info {{
    display: flex;
    gap: 15px;
    color: #666;
    font-size: 0.9em;
}}

h1 {{
    color: #333;
}}

a {{
    color: #2c82c9;
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

/* 视图控制条 */
.view-controls {{
    display: flex;
    gap: 10px;
    align-items: center;
}}
.view-controls select, .view-controls button {{
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #ccc;
    background: white;
    cursor: pointer;
}}
.view-controls button.active {{
    background: #2c82c9;
    color: white;
    border-color: #2c82c9;
}}

/* 图标视图 */
.icon-view {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 15px;
}}
.icon-view .entry {{
    flex-direction: column;
    text-align: center;
    padding: 15px 8px;
    transform: none !important;
}}
.icon-view .entry:hover {{
    transform: scale(1.03) !important;
}}
.icon-view .entry-icon {{
    font-size: 3em;
    margin-bottom: 8px;
    width: 100%;
    overflow: hidden;
}}
.icon-view .entry-icon img {{
    max-width: 100%;
    max-height: 120px;
    object-fit: contain;
    border-radius: 6px;
}}
.icon-view .entry-name {{
    word-break: break-all;
    font-size: 0.9em;
    margin-bottom: 4px;
}}
.icon-view .file-info {{
    justify-content: center;
}}

/* 模态框通用 */
.modal {{
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.5);
}}

.modal-content {{
    background: rgba(255,255,255,0.95);
    margin: 5% auto;
    padding: 25px;
    border-radius: 12px;
    width: 80%;
    max-width: 800px;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 5px 30px rgba(0,0,0,0.3);
    position: relative;
}}

.btn {{
    padding: 8px 20px;
    border: none;
    border-radius: 6px;
    background: #2c82c9;
    color: white;
    cursor: pointer;
    font-size: 14px;
    margin-right: 10px;
}}

.btn:hover {{
    background: #1a5c8a;
}}

.btn-close {{
    background: #999;
}}

/* 下载模态框进度条 */
.progress-container {{
    margin: 15px 0;
}}

.progress-bar {{
    width: 100%;
    height: 20px;
    background: #eee;
    border-radius: 10px;
    overflow: hidden;
    margin: 8px 0;
}}

.progress-fill {{
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    transition: width 0.2s;
}}

.sub-progress {{
    height: 10px;
    margin: 2px 0;
    background: #f0f0f0;
}}

.sub-fill {{
    height: 100%;
    width: 0%;
    background: #64B5F6;
}}

/* 文本预览 */
.text-preview {{
    white-space: pre-wrap;
    font-family: monospace;
    background: #f8f8f8;
    padding: 15px;
    border-radius: 8px;
    max-height: 50vh;
    overflow: auto;
    margin-bottom: 50px;
}}

.text-download-btn {{
    position: absolute;
    bottom: 20px;
    right: 25px;
}}
</style>
</head>

<body>

<div class="container">

<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
<h1>📁 {full_path}</h1>
<div style="display:flex; gap:15px; align-items:center;">
  <div class="view-controls">
    <select id="sortSelect">
      <option value="name-asc">名称 ↑</option>
      <option value="name-desc">名称 ↓</option>
      <option value="size-asc">大小 ↑</option>
      <option value="size-desc">大小 ↓</option>
    </select>
    <button id="listViewBtn" class="active">📋 列表</button>
    <button id="iconViewBtn">🎨 图标</button>
  </div>
  <a href="/settings.html">⚙ 设置</a>
</div>
</div>

{info}

<div style="margin: 20px 0;">
<a href="../">⬆ 上级目录</a>
</div>

<div id="fileContainer">
{content}
</div>

<hr>
<div style="text-align:center;">
<img src="https://c.cneko.org/c/@CrystalNeko?p=res" alt="访问计数" />
</div>

</div>

<!-- 下载模态框（仅用于分片大文件） -->
<div id="downloadModal" class="modal">
  <div class="modal-content">
    <h3 id="dlFileName"></h3>
    <p id="dlFileSize"></p>
    <label><input type="checkbox" id="dlMultiThread" checked> 启用多线程下载</label>
    <div id="dlProgressArea" class="progress-container"></div>
    <button id="dlStartBtn" class="btn">开始下载</button>
    <button id="dlCloseBtn" class="btn btn-close">关闭</button>
  </div>
</div>

<!-- 预览模态框（音视频/图片/文本） -->
<div id="previewModal" class="modal">
  <div class="modal-content">
    <h3 id="prevTitle"></h3>
    <div id="prevContent" style="margin:15px 0;"></div>
    <button id="prevCloseBtn" class="btn btn-close" style="position:absolute; top:15px; right:15px;">关闭</button>
  </div>
</div>

<!-- 错误模态框 -->
<div id="errorModal" class="modal">
  <div class="modal-content">
    <h3>⚠ 错误</h3>
    <p id="errorMsg"></p>
    <button id="errorCloseBtn" class="btn btn-close">关闭</button>
  </div>
</div>

<script>
(function(){{
    const settings = JSON.parse(localStorage.getItem("siteSettings") || "{{}}");

    if(settings.bgUrl){{
        document.body.style.background = `url('${{settings.bgUrl}}') fixed`;
        document.body.style.backgroundSize = "cover";
    }}
    if(settings.fontColor) document.body.style.color = settings.fontColor;
    if(settings.fontSize) document.body.style.fontSize = settings.fontSize + "px";
    if(settings.linkColor) document.querySelectorAll("a").forEach(a=>a.style.color = settings.linkColor);
    if(settings.folderWidth) document.querySelector(".container").style.maxWidth = settings.folderWidth + "px";
    if(settings.folderHeight) document.querySelectorAll(".entry").forEach(e=>e.style.minHeight = settings.folderHeight + "px");
    if(settings.folderColor) document.querySelectorAll(".entry").forEach(e=>e.style.background = settings.folderColor);
    if(settings.bgColor) document.body.style.backgroundColor = settings.bgColor;
    if(settings.bgOpacity) document.querySelector(".container").style.background = `rgba(255,255,255,${{settings.bgOpacity}})`;
}})();
</script>

<script>
// ============ 工具函数 ============

function formatSize(size) {{
    for (const unit of ['B', 'KB', 'MB', 'GB', 'TB']) {{
        if (size < 1024.0) return `${{size.toFixed(1)}} ${{unit}}`;
        size /= 1024.0;
    }}
    return `${{size.toFixed(1)}} PB`;
}}

function formatSpeed(bytesPerSec) {{
    if (bytesPerSec < 1024) return bytesPerSec.toFixed(1) + ' B/s';
    if (bytesPerSec < 1024*1024) return (bytesPerSec/1024).toFixed(1) + ' KB/s';
    return (bytesPerSec/(1024*1024)).toFixed(1) + ' MB/s';
}}

// ============ 下载与合并 ============

async function downloadWithProgress(url, onProgress) {{
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
    const contentLength = response.headers.get('Content-Length');
    const total = contentLength ? parseInt(contentLength, 10) : 0;
    const reader = response.body.getReader();
    const chunks = [];
    let received = 0;
    while (true) {{
        const {{ done, value }} = await reader.read();
        if (done) break;
        chunks.push(value);
        received += value.length;
        if (onProgress && total > 0) onProgress(received, total);
    }}
    const buf = new Uint8Array(received);
    let pos = 0;
    for (const chunk of chunks) {{
        buf.set(chunk, pos);
        pos += chunk.length;
    }}
    return buf.buffer;
}}

async function downloadAllParts(parts, useMulti, concurrency, progressCallbacks) {{
    const results = new Array(parts.length);
    let active = 0;
    let index = 0;
    const dlPart = async (i) => {{
        const part = parts[i];
        const onProg = (loaded, total) => {{
            if (progressCallbacks.partProgress) progressCallbacks.partProgress(i, loaded, total);
        }};
        const data = await downloadWithProgress(part.name, onProg);
        results[i] = data;
        if (progressCallbacks.partComplete) progressCallbacks.partComplete(i);
    }};
    return new Promise((resolve, reject) => {{
        const next = () => {{
            while (active < concurrency && index < parts.length) {{
                const i = index++;
                active++;
                dlPart(i).then(() => {{ active--; next(); }}).catch(reject);
            }}
            if (active === 0 && index === parts.length) resolve(results);
        }};
        next();
    }});
}}

async function mergePartsToBlob(partsInfo, useMulti = true, onProgress, onPartProgress) {{
    const totalSize = partsInfo.reduce((s, p) => s + p.size, 0);
    const partTotals = partsInfo.map(p => p.size);
    const partLoaded = new Array(partsInfo.length).fill(0);
    let downloaded = 0;
    
    const progressCallbacks = {{
        partProgress: (i, loaded, total) => {{
            const delta = loaded - partLoaded[i];
            if (delta > 0) {{
                downloaded += delta;
                partLoaded[i] = loaded;
                if (onProgress) onProgress(downloaded, totalSize);
            }}
            if (onPartProgress) onPartProgress(i, loaded, total);
        }},
        partComplete: (i) => {{
            const remaining = partTotals[i] - partLoaded[i];
            if (remaining > 0) {{
                downloaded += remaining;
                partLoaded[i] = partTotals[i];
                if (onProgress) onProgress(downloaded, totalSize);
            }}
            if (onPartProgress) onPartProgress(i, partTotals[i], partTotals[i]);
        }}
    }};
    
    const results = await downloadAllParts(partsInfo, useMulti, useMulti ? 4 : 1, progressCallbacks);
    const totalLength = results.reduce((sum, buf) => sum + buf.byteLength, 0);
    const merged = new Uint8Array(totalLength);
    let offset = 0;
    for (const buf of results) {{
        merged.set(new Uint8Array(buf), offset);
        offset += buf.byteLength;
    }}
    return new Blob([merged]);
}}

async function downloadFileAsBlob(url, onProgress) {{
    const buf = await downloadWithProgress(url, onProgress);
    return new Blob([buf]);
}}

function saveBlob(blob, filename) {{
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 5000);
}}

// 直接下载（浏览器默认下载，无模态框）
function downloadFileDirectly(name, url) {{
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}}

// ============ 预览与下载分发 ============

const previewModal = document.getElementById('previewModal');
const prevTitle = document.getElementById('prevTitle');
const prevContent = document.getElementById('prevContent');
const errorModal = document.getElementById('errorModal');
const errorMsg = document.getElementById('errorMsg');

function showError(msg) {{
    errorMsg.textContent = msg;
    errorModal.style.display = 'block';
}}

// 下载窗格（仅用于分片文件）
async function startDownloadFlow(entryEl) {{
    const name = entryEl.dataset.name;
    const parts = entryEl.dataset.parts ? JSON.parse(entryEl.dataset.parts) : null;
    const size = parseInt(entryEl.dataset.size);

    const modal = document.getElementById('downloadModal');
    const progressArea = document.getElementById('dlProgressArea');
    const startBtn = document.getElementById('dlStartBtn');
    const closeBtn = document.getElementById('dlCloseBtn');

    document.getElementById('dlFileName').textContent = '📥 下载: ' + name;
    document.getElementById('dlFileSize').textContent = '总大小: ' + formatSize(size) + ' (' + parts.length + ' 个分片)';
    document.getElementById('dlMultiThread').checked = true;
    progressArea.innerHTML = '';
    startBtn.disabled = false;
    closeBtn.disabled = false;

    const newStart = startBtn.cloneNode(true);
    startBtn.parentNode.replaceChild(newStart, startBtn);
    newStart.addEventListener('click', async () => {{
        const useMulti = document.getElementById('dlMultiThread').checked;
        newStart.disabled = true;
        closeBtn.disabled = true;

        progressArea.innerHTML = '';
        const mainBar = document.createElement('div');
        mainBar.className = 'progress-bar';
        mainBar.innerHTML = '<div class="progress-fill" id="mainFill" style="width:0%"></div>';
        progressArea.appendChild(mainBar);
        const mainFill = document.getElementById('mainFill');

        const percentSpan = document.createElement('span');
        percentSpan.id = 'dlPercent';
        percentSpan.textContent = '0%';
        percentSpan.style.marginLeft = '10px';
        progressArea.appendChild(percentSpan);

        const speedSpan = document.createElement('span');
        speedSpan.id = 'dlSpeed';
        speedSpan.textContent = '0 B/s';
        speedSpan.style.marginLeft = '10px';
        progressArea.appendChild(speedSpan);

        let subBars = [];
        if (useMulti) {{
            const subContainer = document.createElement('div');
            parts.forEach((p, i) => {{
                const bar = document.createElement('div');
                bar.className = 'progress-bar sub-progress';
                bar.innerHTML = `<div class="progress-fill sub-fill" id="subFill${{i}}" style="width:0%"></div>`;
                subContainer.appendChild(bar);
            }});
            progressArea.appendChild(subContainer);
            subBars = parts.map((_, i) => document.getElementById(`subFill${{i}}`));
        }}

        let lastTime = Date.now();
        let lastLoaded = 0;
        const maxSpeed = 10 * 1024 * 1024; // 10 MB/s 颜色阈值

        try {{
            const blob = await mergePartsToBlob(parts, useMulti, 
                (loaded, total) => {{
                    const percent = (loaded / total * 100).toFixed(1);
                    mainFill.style.width = percent + '%';
                    percentSpan.textContent = percent + '%';
                    
                    const now = Date.now();
                    const elapsed = (now - lastTime) / 1000;
                    if (elapsed > 0.3) {{  // 避免更新过快
                        const speed = (loaded - lastLoaded) / elapsed;
                        speedSpan.textContent = formatSpeed(speed);
                        const ratio = Math.min(speed / maxSpeed, 1);
                        const red = 255;
                        const green = Math.round(255 * (1 - ratio));
                        const blue = Math.round(255 * (1 - ratio));
                        speedSpan.style.color = `rgb(${{red}},${{green}},${{blue}})`;
                        speedSpan.style.fontWeight = speed > maxSpeed ? 'bold' : 'normal';
                        lastTime = now;
                        lastLoaded = loaded;
                    }}
                }},
                (i, loaded, total) => {{
                    if (useMulti && subBars[i]) {{
                        subBars[i].style.width = (loaded / total * 100) + '%';
                    }}
                }}
            );
            if (useMulti) subBars.forEach(b => b.style.width = '100%');
            saveBlob(blob, name);
            modal.style.display = 'none';
        }} catch (err) {{
            showError('下载失败: ' + err.message);
        }} finally {{
            newStart.disabled = false;
            closeBtn.disabled = false;
        }}
    }});

    closeBtn.onclick = () => modal.style.display = 'none';
    modal.style.display = 'block';
}}

// 图片预览
async function previewImage(entryEl) {{
    const name = entryEl.dataset.name;
    const url = entryEl.dataset.url;
    const parts = entryEl.dataset.parts ? JSON.parse(entryEl.dataset.parts) : null;
    prevTitle.textContent = '🖼 ' + name;
    prevContent.innerHTML = '<div style="text-align:center">加载中...</div>';
    previewModal.style.display = 'block';

    try {{
        let imgSrc;
        if (parts) {{
            const blob = await mergePartsToBlob(parts, true);
            imgSrc = URL.createObjectURL(blob);
            const release = () => URL.revokeObjectURL(imgSrc);
            previewModal.addEventListener('close', release, {{once: true}});
        }} else {{
            imgSrc = url;
        }}
        prevContent.innerHTML = `<img src="${{imgSrc}}" alt="${{name}}" style="max-width:100%;max-height:70vh;display:block;margin:0 auto;">`;
    }} catch (err) {{
        prevContent.innerHTML = `<p style="color:red">加载失败: ${{err.message}}</p>`;
    }}
}}

// 文本预览
async function previewText(entryEl) {{
    const name = entryEl.dataset.name;
    const url = entryEl.dataset.url;
    const parts = entryEl.dataset.parts ? JSON.parse(entryEl.dataset.parts) : null;
    prevTitle.textContent = '📄 ' + name;
    prevContent.innerHTML = '<div style="text-align:center">加载中...</div>';
    previewModal.style.display = 'block';

    try {{
        let text, blob;
        if (parts) {{
            blob = await mergePartsToBlob(parts, true);
            text = await blob.text();
        }} else {{
            const resp = await fetch(url);
            blob = await resp.blob();
            text = await blob.text();
        }}
        prevContent.innerHTML = `
            <div class="text-preview">${{text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}}</div>
            <button id="textDownloadBtn" class="btn text-download-btn">⬇ 下载</button>
        `;
        document.getElementById('textDownloadBtn').onclick = () => {{
            saveBlob(blob, name);
        }};
    }} catch (err) {{
        prevContent.innerHTML = `<p style="color:red">加载失败: ${{err.message}}</p>`;
    }}
}}

// 音视频预览
async function previewMedia(entryEl) {{
    const name = entryEl.dataset.name;
    const url = entryEl.dataset.url;
    const parts = entryEl.dataset.parts ? JSON.parse(entryEl.dataset.parts) : null;
    const type = entryEl.dataset.type;

    prevTitle.textContent = (type === 'video' ? '🎬 ' : '🎵 ') + name;
    prevContent.innerHTML = '<div style="text-align:center">加载中...</div>';
    previewModal.style.display = 'block';

    try {{
        let blobUrl;
        if (parts) {{
            const blob = await mergePartsToBlob(parts, true);
            blobUrl = URL.createObjectURL(blob);
            const release = () => URL.revokeObjectURL(blobUrl);
            previewModal.addEventListener('close', release, {{once: true}});
        }} else {{
            blobUrl = url;
        }}

        if (type === 'video') {{
            prevContent.innerHTML = `<video controls autoplay style="max-width:100%;max-height:60vh;" src="${{blobUrl}}"></video>`;
        }} else {{
            prevContent.innerHTML = `<audio controls autoplay style="width:100%;" src="${{blobUrl}}"></audio>`;
        }}
    }} catch (err) {{
        prevContent.innerHTML = `<p style="color:red">加载失败: ${{err.message}}</p>`;
    }}
}}

// 文件条目点击入口
function handleFileClick(entryEl) {{
    const type = entryEl.dataset.type;
    const size = parseInt(entryEl.dataset.size);
    const name = entryEl.dataset.name;
    const url = entryEl.dataset.url;
    const parts = entryEl.dataset.parts ? JSON.parse(entryEl.dataset.parts) : null;

    // 分片文件：必须弹窗下载
    if (parts && parts.length > 0) {{
        startDownloadFlow(entryEl);
        return;
    }}

    // 普通文件：根据类型处理
    if (type === 'video' || type === 'audio') {{
        previewMedia(entryEl);
    }} else if (type === 'image') {{
        previewImage(entryEl);
    }} else if (type === 'text' && size < 1048576) {{
        previewText(entryEl);
    }} else {{
        // 其它所有无法预览的文件直接交给浏览器处理（导航到链接）
        window.location.href = url;
    }}
}}

// ============ 排序与视图 ============

const fileContainer = document.getElementById('fileContainer');
let currentSort = 'name-asc';
let currentView = 'list';

function applySort() {{
    const entries = [...fileContainer.querySelectorAll('.file-entry')];
    const [key, order] = currentSort.split('-');
    entries.sort((a, b) => {{
        let valA, valB;
        if (key === 'name') {{
            valA = a.dataset.name.toLowerCase();
            valB = b.dataset.name.toLowerCase();
        }} else {{
            valA = parseInt(a.dataset.size);
            valB = parseInt(b.dataset.size);
        }}
        if (valA < valB) return order === 'asc' ? -1 : 1;
        if (valA > valB) return order === 'asc' ? 1 : -1;
        return 0;
    }});
    entries.forEach(e => fileContainer.appendChild(e));
}}

function applyView() {{
    fileContainer.classList.toggle('icon-view', currentView === 'icon');
    document.getElementById('listViewBtn').classList.toggle('active', currentView === 'list');
    document.getElementById('iconViewBtn').classList.toggle('active', currentView === 'icon');

    if (currentView === 'icon') {{
        fileContainer.querySelectorAll('.file-entry').forEach(entry => {{
            const iconDiv = entry.querySelector('.entry-icon');
            if (!iconDiv) return;
            const thumb = entry.dataset.thumb;
            if (thumb) {{
                if (!iconDiv.querySelector('img[data-thumb]')) {{
                    iconDiv.innerHTML = `<img data-thumb src="${{thumb}}" alt="${{entry.dataset.name}}" style="max-width:100%;max-height:120px;object-fit:contain;">`;
                }}
            }}
        }});
    }}
}}

function saveViewSettings() {{
    localStorage.setItem('fileViewSettings', JSON.stringify({{
        sort: currentSort,
        view: currentView
    }}));
}}

// 绑定控件事件
document.getElementById('sortSelect').addEventListener('change', function() {{
    currentSort = this.value;
    applySort();
    saveViewSettings();
}});
document.getElementById('listViewBtn').addEventListener('click', () => {{
    currentView = 'list';
    applyView();
    saveViewSettings();
}});
document.getElementById('iconViewBtn').addEventListener('click', () => {{
    currentView = 'icon';
    applyView();
    saveViewSettings();
}});

// 初始化
document.addEventListener('DOMContentLoaded', () => {{
    const saved = JSON.parse(localStorage.getItem('fileViewSettings') || '{{}}');
    if (saved.sort) {{
        currentSort = saved.sort;
        document.getElementById('sortSelect').value = currentSort;
    }}
    if (saved.view) {{
        currentView = saved.view;
        applyView();
    }}
    applySort();

    fileContainer.addEventListener('click', (e) => {{
        const entry = e.target.closest('.file-entry');
        if (entry) handleFileClick(entry);
    }});

    document.getElementById('prevCloseBtn').onclick = () => {{
        previewModal.style.display = 'none';
        // 触发 close 事件以便清理 blob
        previewModal.dispatchEvent(new Event('close'));
    }};
    document.getElementById('errorCloseBtn').onclick = () => errorModal.style.display = 'none';
    window.onclick = (event) => {{
        if (event.target == previewModal) {{
            previewModal.style.display = 'none';
            previewModal.dispatchEvent(new Event('close'));
        }}
        if (event.target == errorModal) errorModal.style.display = 'none';
        if (event.target == document.getElementById('downloadModal')) document.getElementById('downloadModal').style.display = 'none';
    }};

    // 处理 ?target= 参数
    const params = new URLSearchParams(window.location.search);
    const target = params.get('target');
    if (target) {{
        const found = [...fileContainer.querySelectorAll('.file-entry')].find(e => e.dataset.name === target);
        if (found) {{
            handleFileClick(found);
        }} else {{
            showError('文件不存在：' + target);
        }}
    }}
}});
</script>
</body>
</html>
"""

# =========================
# 条目模板（用于生成HTML片段）
# =========================

dir_template = """
<a href="{dir_name}/index.html" class="entry">
<span>📂 {dir_name}</span>
<span class="file-info"><span>{size}</span></span>
</a>
"""

file_entry_template = """
<div class="entry file-entry" data-name="{name}" data-url="{url}" data-type="{type}" data-size="{size}" data-thumb="{thumb}" {parts_attr}>
  <span class="entry-icon">{icon}</span>
  <span class="entry-name">{name}</span>
  <span class="file-info"><span>{size_text}</span></span>
</div>
"""


# =========================
# 工具函数
# =========================

def get_dir_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}PB"


def get_file_icon(name):
    ext = name.lower().split('.')[-1]
    icons = {
        "zip": "📦", "rar": "📦", "7z": "📦",
        "mp4": "🎬", "mkv": "🎬", "webm": "🎬", "avi": "🎬",
        "mp3": "🎵", "flac": "🎵", "wav": "🎵", "ogg": "🎵", "m4a": "🎵",
        "png": "🖼", "jpg": "🖼", "jpeg": "🖼", "gif": "🖼", "bmp": "🖼", "svg": "🖼",
        "pdf": "📕", "txt": "📄", "py": "🐍", "html": "🌐", "css": "🎨", "js": "📜",
        "json": "📊", "xml": "📊", "md": "📝", "log": "📜", "yaml": "📄"
    }
    return icons.get(ext, "📄")


def classify_file(name):
    ext = name.lower().split('.')[-1]
    video_exts = {'mp4', 'mkv', 'webm', 'avi', 'mov', 'flv', 'wmv'}
    audio_exts = {'mp3', 'flac', 'wav', 'ogg', 'm4a', 'aac', 'wma'}
    image_exts = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp'}
    text_exts = {'txt', 'py', 'js', 'html', 'css', 'json', 'xml', 'md', 'log', 'yaml', 'yml', 'sh', 'bat'}
    if ext in video_exts:
        return 'video'
    if ext in audio_exts:
        return 'audio'
    if ext in image_exts:
        return 'image'
    if ext in text_exts:
        return 'text'
    return 'other'


def generate_thumbnail(file_path, thumb_name="thumb.jpg", size=(200, 200)):
    """
    生成缩略图并保存到同目录下。返回缩略图文件名（相对路径），失败返回 None。
    """
    try:
        img = Image.open(file_path)
        img.thumbnail(size)
        thumb_dir = os.path.dirname(file_path)
        thumb_path = os.path.join(thumb_dir, thumb_name)
        # 统一转为JPEG格式（RGBA转RGB）
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
            background = Image.new('RGBA', img.size, (255, 255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background.convert('RGB')
        else:
            img = img.convert('RGB')
        img.save(thumb_path, 'JPEG', quality=85)
        return thumb_name
    except Exception as e:
        print(f"⚠️ 缩略图生成失败 ({file_path}): {e}")
        return None


# =========================
# 复制文件
# =========================

def copy_files(source_dir, output_dir):
    exclude_dir = os.path.basename(output_dir)

    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != exclude_dir]
        files = [f for f in files if not f.startswith('.')]

        rel_path = os.path.relpath(root, source_dir)
        dest_dir = os.path.join(output_dir, rel_path)
        os.makedirs(dest_dir, exist_ok=True)

        for file in files:
            src = os.path.join(root, file)
            dst = os.path.join(dest_dir, file)
            shutil.copy2(src, dst)


# =========================
# 生成 index.html
# =========================

def generate_index_html(root_dir):
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        files = [f for f in files if not f.startswith('.')]

        rel_path = os.path.relpath(root, root_dir)
        full_path = rel_path if rel_path != '.' else 'Home'

        content = ""

        # --- 分片文件识别 ---
        part_pattern = re.compile(r'^(.+)\.(\d{3,})$')
        potential_parts = {}
        for fn in files:
            if fn in ['index.html', 'info.json', 'info.md']:
                continue
            m = part_pattern.match(fn)
            if m:
                base = m.group(1)
                part_num = int(m.group(2))
                potential_parts.setdefault(base, []).append((fn, part_num))

        part_groups = {}
        all_part_files = set()
        for base, parts in potential_parts.items():
            parts.sort(key=lambda x: x[1])
            numbers = [p[1] for p in parts]
            if len(parts) >= 2 and numbers == list(range(1, len(parts) + 1)):
                part_groups[base] = parts
                for fn, _ in parts:
                    all_part_files.add(fn)

        # 生成文件夹条目
        for dir_name in sorted(dirs):
            dir_path = os.path.join(root, dir_name)
            dir_size = format_size(get_dir_size(dir_path))
            content += dir_template.format(
                dir_name=dir_name,
                size=dir_size
            )

        # 生成分片组条目（大文件）
        for base in sorted(part_groups.keys()):
            parts = part_groups[base]
            total_size = sum(os.path.getsize(os.path.join(root, fn)) for fn, _ in parts)
            parts_info = []
            for fn, num in parts:
                fpath = os.path.join(root, fn)
                fsize = os.path.getsize(fpath)
                parts_info.append({"name": fn, "size": fsize})
            parts_json = json.dumps(parts_info, ensure_ascii=False)
            icon = get_file_icon(base)
            ftype = classify_file(base)
            content += file_entry_template.format(
                name=base,
                url="",
                type=ftype,
                size=total_size,
                size_text=format_size(total_size),
                icon=icon,
                thumb="",
                parts_attr=f'data-parts=\'{parts_json}\''
            )

        # 生成普通文件条目
        for file_name in sorted(files):
            if file_name in ['index.html', 'info.json', 'info.md']:
                continue
            if file_name in all_part_files:
                continue
            file_path = os.path.join(root, file_name)
            file_size = os.path.getsize(file_path)
            icon = get_file_icon(file_name)
            ftype = classify_file(file_name)

            # 构建缩略图（仅图片文件）
            thumb_url = ""
            if ftype == 'image':
                thumb_filename = file_name + ".thumb.jpg"
                thumb_result = generate_thumbnail(file_path, thumb_filename)
                if thumb_result:
                    thumb_url = thumb_filename
                else:
                    thumb_url = ""

            content += file_entry_template.format(
                name=file_name,
                url=file_name,
                type=ftype,
                size=file_size,
                size_text=format_size(file_size),
                icon=icon,
                thumb=thumb_url,
                parts_attr=""
            )

        # 生成 info.json
        info = {"files": [], "dirs": []}
        for file_name in files:
            if file_name not in ['index.html', 'info.json', 'info.md']:
                file_path = os.path.join(root, file_name)
                with open(file_path, 'rb') as f:
                    sha256_hash = hashlib.sha256(f.read()).hexdigest()
                info["files"].append({
                    "name": file_name,
                    "sha256": sha256_hash,
                    "size": os.path.getsize(file_path)
                })

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            info["dirs"].append({
                "name": dir_name,
                "size": get_dir_size(dir_path)
            })

        with open(os.path.join(root, 'info.json'), 'w') as f:
            json.dump(info, f, indent=4)

        # info.md 支持
        info_md_path = os.path.join(root, 'info.md')
        info_placeholder = ""
        if os.path.exists(info_md_path):
            with open(info_md_path, 'r', encoding='utf-8') as f:
                info_html = markdown.markdown(f.read())
                info_placeholder = f"<div>{info_html}</div>"

        index_content = template.format(
            full_path=full_path,
            content=content,
            info=info_placeholder
        )

        with open(os.path.join(root, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_content)


# =========================
# 主程序
# =========================

if __name__ == "__main__":
    source_dir = "."
    output_dir = "output"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    copy_files(source_dir, output_dir)

    generate_index_html(output_dir)

    print("✅ 生成完成")
