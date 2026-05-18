import os
import json
import hashlib
import markdown
import shutil
import re  # 新增用于分片文件名匹配


# =========================
# HTML 模板
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

/* 下载模态框 */
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
    margin: 10% auto;
    padding: 25px;
    border-radius: 12px;
    width: 80%;
    max-width: 600px;
    box-shadow: 0 5px 30px rgba(0,0,0,0.3);
}}

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
</style>
</head>

<body>

<div class="container">

<div style="display:flex;justify-content:space-between;align-items:center;">
<h1>📁 {full_path}</h1>
<a href="/settings.html">⚙ 设置</a>
</div>

{info}

<div style="margin: 20px 0;">
<a href="../">⬆ 上级目录</a>
</div>

{content}

<hr>
<div style="text-align:center;">
<img src="https://c.cneko.org/c/@CrystalNeko?p=res" alt="访问计数" />
</div>

</div>

<!-- 下载模态框 -->
<div id="downloadModal" class="modal">
  <div class="modal-content">
    <h3 id="dlFileName"></h3>
    <p id="dlFileSize"></p>
    <label>
      <input type="checkbox" id="dlMultiThread" checked> 启用多线程下载
    </label>
    <div id="dlProgressArea" class="progress-container"></div>
    <button id="dlStartBtn" class="btn">开始下载</button>
    <button id="dlCloseBtn" class="btn btn-close">关闭</button>
  </div>
</div>


<script>
(function(){{
    const settings = JSON.parse(localStorage.getItem("siteSettings") || "{{}}");

    if(settings.bgUrl){{
        document.body.style.background = `url('${{settings.bgUrl}}') fixed`;
        document.body.style.backgroundSize = "cover";
    }}

    if(settings.fontColor){{
        document.body.style.color = settings.fontColor;
    }}

    if(settings.fontSize){{
        document.body.style.fontSize = settings.fontSize + "px";
    }}

    if(settings.linkColor){{
        document.querySelectorAll("a").forEach(a=>{{
            a.style.color = settings.linkColor;
        }});
    }}

    if(settings.folderWidth){{
        document.querySelector(".container").style.maxWidth = settings.folderWidth + "px";
    }}

    if(settings.folderHeight){{
        document.querySelectorAll(".entry").forEach(e=>{{
            e.style.minHeight = settings.folderHeight + "px";
        }});
    }}

    if(settings.folderColor){{
        document.querySelectorAll(".entry").forEach(e=>{{
            e.style.background = settings.folderColor;
        }});
    }}

    if(settings.bgColor){{
        document.body.style.backgroundColor = settings.bgColor;
    }}

    if(settings.bgOpacity){{
        document.querySelector(".container").style.background =
            `rgba(255,255,255,${{settings.bgOpacity}})`;
    }}

}})();
</script>

<script>
// ============ 分片下载逻辑 ============

// 下载单个文件（带进度回调）
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
        if (onProgress && total > 0) {{
            onProgress(received, total);
        }}
    }}

    // 合并chunks为ArrayBuffer
    const buf = new Uint8Array(received);
    let pos = 0;
    for (const chunk of chunks) {{
        buf.set(chunk, pos);
        pos += chunk.length;
    }}
    return buf.buffer;
}}

// 控制并发下载
async function downloadAllParts(parts, useMulti, concurrency, progressCallbacks) {{
    const results = new Array(parts.length);
    let active = 0;
    let index = 0;

    const dlPart = async (i) => {{
        const part = parts[i];
        const url = part.name; // 相对路径
        const onProg = (loaded, total) => {{
            if (progressCallbacks.partProgress) {{
                progressCallbacks.partProgress(i, loaded, total);
            }}
        }};
        const data = await downloadWithProgress(url, onProg);
        results[i] = data;
        if (progressCallbacks.partComplete) {{
            progressCallbacks.partComplete(i);
        }}
    }};

    return new Promise((resolve, reject) => {{
        const next = () => {{
            while (active < concurrency && index < parts.length) {{
                const i = index++;
                active++;
                dlPart(i).then(() => {{
                    active--;
                    next();
                }}).catch(reject);
            }}
            if (active === 0 && index === parts.length) {{
                resolve(results);
            }}
        }};
        next();
    }});
}}

// 触发浏览器保存对话框
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

// 主下载流程
async function startDownload(originalName, parts, useMulti) {{
    const modal = document.getElementById('downloadModal');
    const progressArea = document.getElementById('dlProgressArea');
    const startBtn = document.getElementById('dlStartBtn');
    const closeBtn = document.getElementById('dlCloseBtn');

    // 清除之前的进度条
    progressArea.innerHTML = '';

    // 创建主进度条
    const mainBar = document.createElement('div');
    mainBar.className = 'progress-bar';
    mainBar.innerHTML = '<div class="progress-fill" id="mainFill" style="width:0%"></div>';
    progressArea.appendChild(mainBar);

    let subBars = [];
    if (useMulti) {{
        // 为每个分片创建子进度条
        const subContainer = document.createElement('div');
        subContainer.id = 'subBars';
        parts.forEach((p, i) => {{
            const bar = document.createElement('div');
            bar.className = 'progress-bar sub-progress';
            bar.innerHTML = `<div class="progress-fill sub-fill" id="subFill${{i}}" style="width:0%"></div>`;
            subContainer.appendChild(bar);
        }});
        progressArea.appendChild(subContainer);
        subBars = parts.map((_, i) => document.getElementById(`subFill${{i}}`));
    }}

    const mainFill = document.getElementById('mainFill');

    // 总大小
    const totalSize = parts.reduce((s, p) => s + p.size, 0);
    let downloadedBytes = 0;
    const partSizes = parts.map(p => p.size);

    // 进度回调
    const progressCallbacks = {{
        partProgress: (i, loaded, total) => {{
            // 更新子进度
            if (useMulti && subBars[i]) {{
                const percent = total ? (loaded / total * 100) : 0;
                subBars[i].style.width = percent + '%';
            }}
            // 更新主进度（累计已下载）
            // 需要知道之前完成的累计字节
        }},
        partComplete: (i) => {{
            // 一个分片下载完成，更新累计
            downloadedBytes += partSizes[i];
            const totalPercent = totalSize ? (downloadedBytes / totalSize * 100) : 0;
            mainFill.style.width = totalPercent + '%';
            if (useMulti && subBars[i]) {{
                subBars[i].style.width = '100%';
            }}
        }}
    }};

    // 开始下载
    startBtn.disabled = true;
    closeBtn.disabled = true;

    try {{
        const concurrency = useMulti ? 4 : 1; // 多线程时并发4个
        const results = await downloadAllParts(parts, useMulti, concurrency, progressCallbacks);

        // 合并 ArrayBuffer
        const totalLength = results.reduce((sum, buf) => sum + buf.byteLength, 0);
        const merged = new Uint8Array(totalLength);
        let offset = 0;
        for (const buf of results) {{
            merged.set(new Uint8Array(buf), offset);
            offset += buf.byteLength;
        }}

        const blob = new Blob([merged]);
        saveBlob(blob, originalName);

        // 下载完成后关闭模态框
        modal.style.display = 'none';
        startBtn.disabled = false;
        closeBtn.disabled = false;
    }} catch (err) {{
        alert('下载失败: ' + err.message);
        startBtn.disabled = false;
        closeBtn.disabled = false;
    }}
}}

// 绑定分片条目的点击事件
document.addEventListener('DOMContentLoaded', () => {{
    const partEntries = document.querySelectorAll('.part-entry');
    partEntries.forEach(entry => {{
        entry.addEventListener('click', (e) => {{
            e.preventDefault();
            const originalName = entry.dataset.originalName;
            const parts = JSON.parse(entry.dataset.parts);
            const totalSize = parts.reduce((s, p) => s + p.size, 0);

            // 显示下载模态框
            const modal = document.getElementById('downloadModal');
            document.getElementById('dlFileName').textContent = '📥 下载: ' + originalName;
            document.getElementById('dlFileSize').textContent = '总大小: ' + formatSize(totalSize) + ' (' + parts.length + ' 个分片)';
            document.getElementById('dlMultiThread').checked = true;
            document.getElementById('dlProgressArea').innerHTML = '';
            document.getElementById('dlStartBtn').disabled = false;
            document.getElementById('dlCloseBtn').disabled = false;

            // 绑定开始按钮
            const startBtn = document.getElementById('dlStartBtn');
            const newStartBtn = startBtn.cloneNode(true);
            startBtn.parentNode.replaceChild(newStartBtn, startBtn);
            newStartBtn.addEventListener('click', () => {{
                const useMulti = document.getElementById('dlMultiThread').checked;
                startDownload(originalName, parts, useMulti);
            }});

            // 关闭按钮
            document.getElementById('dlCloseBtn').onclick = () => {{
                modal.style.display = 'none';
            }};

            modal.style.display = 'block';
        }});
    }});

    // 点击模态框外部关闭
    window.onclick = (event) => {{
        const modal = document.getElementById('downloadModal');
        if (event.target == modal) {{
            modal.style.display = 'none';
        }}
    }};
}});

function formatSize(size) {{
    for (const unit of ['B', 'KB', 'MB', 'GB', 'TB']) {{
        if (size < 1024.0) return `${{size.toFixed(1)}} ${{unit}}`;
        size /= 1024.0;
    }}
    return `${{size.toFixed(1)}} PB`;
}}
</script>
<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "eab93a94af294e41b8f2d7e7c2d83b8a"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>
"""


dir_template = """
<a href="{dir_name}/index.html" class="entry">
<span>📂 {dir_name}</span>
<span class="file-info"><span>{size}</span></span>
</a>
"""

file_template = """
<a href="{file_name}" class="entry">
<span>{icon} {file_name}</span>
<span class="file-info"><span>{size}</span></span>
</a>
"""

# 分片文件条目模板
part_file_template = """
<div class="entry part-entry" data-original-name="{original_name}" data-parts='{parts_json}' style="cursor:pointer;">
<span>🧩 {original_name} <small style="color:#888;">(分片)</small></span>
<span class="file-info"><span>{size}</span></span>
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
        "zip":"📦","rar":"📦","7z":"📦",
        "mp4":"🎬","mkv":"🎬",
        "mp3":"🎵","flac":"🎵",
        "png":"🖼","jpg":"🖼","jpeg":"🖼","gif":"🖼",
        "pdf":"📕","txt":"📄",
        "py":"🐍","html":"🌐"
    }
    return icons.get(ext,"📄")


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

        part_groups = {}  # base -> list of (filename, part_num) sorted
        all_part_files = set()
        for base, parts in potential_parts.items():
            parts.sort(key=lambda x: x[1])
            # 检查是否从1开始且连续，至少两个文件
            numbers = [p[1] for p in parts]
            if len(parts) >= 2 and numbers == list(range(1, len(parts)+1)):
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

        # 生成分片组条目
        for base in sorted(part_groups.keys()):
            parts = part_groups[base]
            total_size = sum(os.path.getsize(os.path.join(root, fn)) for fn, _ in parts)
            # 构建 parts JSON 列表
            parts_info = []
            for fn, num in parts:
                fpath = os.path.join(root, fn)
                fsize = os.path.getsize(fpath)
                parts_info.append({"name": fn, "size": fsize})
            parts_json = json.dumps(parts_info, ensure_ascii=False)
            content += part_file_template.format(
                original_name=base,
                size=format_size(total_size),
                parts_json=parts_json
            )

        # 生成普通文件条目（排除分片内的文件）
        for file_name in sorted(files):
            if file_name in ['index.html', 'info.json', 'info.md']:
                continue
            if file_name in all_part_files:
                continue
            file_path = os.path.join(root, file_name)
            file_size = format_size(os.path.getsize(file_path))
            icon = get_file_icon(file_name)

            content += file_template.format(
                file_name=file_name,
                size=file_size,
                icon=icon
            )

        # 生成 info.json（保持记录所有真实文件，包括分片）
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
