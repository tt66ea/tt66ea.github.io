#import "/config.typ": template, tufted

#let post-template(post, body) = {
  let parts = post.date.split("-")
  let date = datetime(
    year: int(parts.at(0)),
    month: int(parts.at(1)),
    day: int(parts.at(2)),
  )
  template.with(
    title: post.title,
    description: post.description,
    date: date,
    lang: post.lang,
  )(body)
}
