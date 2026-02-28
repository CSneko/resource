import os
import json
import hashlib
import markdown
import shutil


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
<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "eab93a94af294e41b8f2d7e7c2d83b8a"}'></script><!-- End Cloudflare Web Analytics -->
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

        # 文件夹
        for dir_name in sorted(dirs):
            dir_path = os.path.join(root, dir_name)
            dir_size = format_size(get_dir_size(dir_path))
            content += dir_template.format(
                dir_name=dir_name,
                size=dir_size
            )

        # 文件
        for file_name in sorted(files):
            if file_name not in ['index.html', 'info.json', 'info.md']:
                file_path = os.path.join(root, file_name)
                file_size = format_size(os.path.getsize(file_path))
                icon = get_file_icon(file_name)

                content += file_template.format(
                    file_name=file_name,
                    size=file_size,
                    icon=icon
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
