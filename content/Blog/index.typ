#import "/config.typ": template, tufted
#show: template.with(
  title: "Blog",
  description: "Some blog examples",
)

= 博客 / Blog

中文博客样例可参考 #link("https://yousa-mirage.github.io/Blog")[我的个人网站]。

#for group in json("_index.json") {
  heading(level: 2, group.category)
  for post in group.posts {
    tufted.blog-entry(
      date: post.date,
      path: post.path,
      title: post.title,
    )
  }
}
