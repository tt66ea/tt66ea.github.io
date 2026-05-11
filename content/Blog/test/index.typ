#import "../index.typ": template, tufted

#show: template.with(
  title: "test",
  description: "test",
  date: datetime(year: 2026, month: 4, day: 16),
  lang: "zh",
)

#set text(font: "Hack", size: 12pt)

= Typst 测试文档

== 文本样式

*粗体文字* 和 _斜体文字_ 以及 #underline[下划线] 和 #strike[删除线]。

还可以使用 #strong[粗体] 和 #emph[斜体] 函数。

#text(fill: red)[红色文字]，#text(fill: blue, weight: "bold")[蓝色粗体]。

== 标题层级

= 一级标题
== 二级标题
=== 三级标题
==== 四级标题

== 列表

无序列表：
- 项目一
- 项目二
  - 嵌套项目
- 项目三

有序列表：
+ 第一项
+ 第二项
+ 第三项

术语列表：

== 链接与引用

#link("https://typst.app")[Typst 官方网站]

== 代码块

```python
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(10))
```

行内代码 `x = y + 1`.

== 数学公式

=== 行内公式

勾股定理：$a^2 + b^2 = c^2$。欧拉恒等式：$e^(i pi) + 1 = 0$。

=== 块级公式

二次方程求根公式：

$ x = (-b plus.minus sqrt(b^2 - 4 a c)) / (2 a) $

=== 分数与根式

$ 1/2 + 1/3 = 5/6 $

$ sqrt(a + b) + root(3, x) $

=== 求和与积分

$ sum_(k=1)^n k = (n(n+1)) / 2 $

$ integral_a^b f(x) dif x $

$ product_(i=0)^n a_i $

$ limits(x -> oo) (1 + 1/x)^x = e $

=== 希腊字母

$ alpha, beta, gamma, delta, epsilon, zeta, eta, theta $

$ Gamma, Delta, Theta, Lambda, Xi, Pi, Sigma, Phi, Psi, Omega $

=== 矩阵

$
  mat(
    1, 2, 3;
    4, 5, 6;
    7, 8, 9;
  )
$

$
  mat(
    delim: "[",
    a_11, a_12;
    a_21, a_22;
  )
$

=== 分段函数

$
  f(x) = cases(
    1 & "if " x > 0,
    0 & "if " x = 0,
    -1 & "if " x < 0
  )
$

=== 对齐公式

$
         x + y & = z \
         a + b & = c + d \
  alpha + beta & = gamma
$

$
  (x + y)^2 & = x^2 + 2 x y + y^2 \
            & = x^2 + y^2 + 2 x y
$

=== 上下标与重音符

$ x_1 + x_2 + dots + x_n $

$ hat(x), tilde(y), vec(v), dot(x), dots(x), bar(z) $

$ overline("AB"), underline("CD") $

=== 集合与逻辑

$ x in RR, y in NN, z in ZZ, w in QQ $

$ A subset B, C supset D, E subset.eq F $

$ forall x in RR, exists y in RR: x + y = 0 $

$ top, bot, not p, p and q, p or q, p => q, p <=> q $

=== 箭头

$ a -> b, c <- d, e => f, g <= h $

$ x arrow.r.long f(x) $

$ a arrow.l.double.r b $

=== 括号

$ (x + 1) (x - 1) = x^2 - 1 $

$ lr([a + b]) lr({x / y}) lr(|integral f|) $

$ abs(x) = cases(x & "if " x >= 0, -x & "if " x < 0) $

$ norm(v) = sqrt(v_1^2 + v_2^2 + dots + v_n^2) $

=== 常用运算符

$ sin theta, cos theta, tan theta $

$ arcsin x, arccos x, arctan x $

$ log_a b, ln x $

$ lim_(x -> 0) sin x / x = 1 $

$ partial f / partial x = nabla dot F $

=== 二项式与组合

$ binom(n, k) = (n!)/(k!(n-k)!) $

=== 堆叠与注解

$
  a + b + c + dots + z \
  = (a+z) + (b+y) + (c+x) + dots
$

$ underbrace(1 + 2 + ... + n, "sum of first n integers") $

$ overbrace(a + b + c, "first three") + overbrace(d + e + f, "last three") $

== 表格

#table(
  columns: (auto, auto, auto),
  align: center,
  [*姓名*], [*年龄*], [*城市*],
  [张三], [25], [北京],
  [李四], [30], [上海],
  [王五], [28], [广州],
)

== 引用

#quote(block: true)[
  学而不思则罔，思而不学则殆。
]

== 水平线

#line(length: 100%)

#v(1em)
此处显示分隔线。

== 脚注

这是一个脚注示例。#footnote[这是脚注的内容]

== 定理与证明

