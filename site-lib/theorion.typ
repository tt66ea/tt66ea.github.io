#import "@preview/theorion:0.6.0" as theorion

// A body-safe stylesheet link keeps the adapter self-contained; no copied asset.
#let stylesheet = "data:text/css;charset=utf-8," + read("theorion.css")
  .replace("%", "%25")
  .replace("#", "%23")
  .replace("\n", "%0A")

#let show-theorion(body) = context {
  if target() == "html" {
    html.link(rel: "stylesheet", href: stylesheet)
    // PDF indentation repair inserts fake paragraphs whose negative spacing
    // HTML cannot represent. Keep the upstream PDF behavior unchanged.
    theorion.set-indent-mode(none)
    show: theorion.show-theorion
    // Wrap the rendering, not the figure itself, so labels and refs survive.
    show figure.where(kind: "theorem"): it => html.div(
      class: "theorion-environment",
      it.body,
    )
    body
  } else {
    theorion.show-theorion(body)
  }
}

#let proof(..args) = context {
  if target() == "html" and theorion.get-result(here()) != "noanswer" {
    html.div(class: "theorion-environment", theorion.proof(..args))
  } else {
    theorion.proof(..args)
  }
}
