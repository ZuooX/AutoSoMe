import re

with open("xhs_publish_page.html", encoding="utf-8") as f:
    html = f.read()

# 找 input[type=file]
print("=== FILE INPUT 元素 ===")
for m in re.finditer(r"<input[^>]*type=[\"']file[\"'][^>]*>", html):
    start = max(0, m.start() - 100)
    print(repr(html[start : m.end() + 50]))
    print()

# 找上传图片按钮附近
print("=== 上传图片 按钮上下文 ===")
idx = html.find("上传图片")
if idx >= 0:
    print(repr(html[max(0, idx - 300) : idx + 200]))
