#!/bin/bash

# 获取脚本所在的相对目录
SCRIPT_DIR=$(dirname "$0")

# 生成目录索引的函数
generate_index() {
    local dir=$1
    local content="<html>
<head>
<meta charset=\"utf-8\">
<title>$dir</title>
</head>
<body>
<h1>$dir</h1>
<hr>"
    
    # 添加上级目录链接
    if [[ "$dir" != "$SCRIPT_DIR" ]]; then
        content+="\n<a href=\"../\">../</a><br>"
    fi

    # 遍历目录中的文件和文件夹，添加链接
    local item
    for item in "$dir"/*; do
        item=${item##*/}
        content+="\n<a href=\"$item\">$item</a><br>"
    done

    content+="\n</body>
</html>"
    echo "$content"
}

# 在当前目录及子目录下生成 index.html 文件
find "$SCRIPT_DIR" -type d -exec sh -c 'generate_index "$0" > "$0/index.html"' {} \;
