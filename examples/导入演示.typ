= 重构导入演示

这篇文章只用于独立预览副本，展示从一份普通 Typst 正文导入博客的完整流程。

== 元数据与正文分离

正文仍然使用 Typst。文章标题、描述、日期、语言和分类放在同目录的 `_post.json` 中；修改元数据后，运行索引重建和构建即可更新页面。

== 一个公式

$ sum_(i=1)^n i = (n(n+1))/2 $

== 索引重建

目录页读取 `_index.json`，不再由 Python 正则改写。导入时会自动重建索引，随后可以运行只读检查：

```sh
python tools/blog.py check
uv run build.py build -f
```
