#import "../index.typ": template, tufted
#show: template.with(
  title: "Blog",
  description: "Some blog examples",
)

= 博客 / Blog

中文博客样例可参考 #link("https://yousa-mirage.github.io/Blog")[我的个人网站]。

== OI-ACM

#tufted.blog-entry(
  date: datetime(year: 2026, month: 7, day: 6),
  path: "XJTUPC 2026/",
  title: "XJTUPC 2026部分题解",
)

== 未分类

#tufted.blog-entry(
  date: datetime(year: 2026, month: 5, day: 11),
  path: "tmp/",
  title: "1",
)

#tufted.blog-entry(
  date: datetime(year: 2026, month: 4, day: 16),
  path: "test/",
  title: "test",
)
