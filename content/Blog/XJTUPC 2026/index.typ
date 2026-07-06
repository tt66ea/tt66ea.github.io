#import "../index.typ": template, tufted

#show: template.with(
  title: "XJTUPC 2026部分题解",
  description: "XJTUPC的部分题解",
  date: datetime(year: 2026, month: 7, day: 6),
  lang: "zh",
  tags: ("OI-ACM"),
)

#import "@preview/theorion:0.6.0": *
#show: show-theorion
= XJTUPC 2026题解
实际上我参与了这场的验题，但是是为了确保低水平选手被区分下去（。

让我们跳过前六道签到题(A,B,C,D,E,F)，我只写补出来了的题

== G 机房分配

#quote-block[这题是事实上的签到题但我还是不会做（]

有一个简单的贪心算法：每次加入新同学时挑一个对风险值增加最小的机房加入

接下来通过贪心证明这个算法的正确性：

#proof([
  假设学生$i$与之前分配的学生之间的边权和为$W_i$，分布在$k$个机房中

  由抽屉原理有这里面一定存在一个机房，学生$i$加入之后新增加的边权和（风险值）$N_i <= W_i / k$

  则按照这个贪心策略，所有学生加入之后，总的风险值$T <= sum_(i=1)^(n) W_i /k = S/k <= ceil(S/k)$
])

```cpp
#include <algorithm>
#include <cstring>
#include <iostream>
#include <map>
#include <set>
#include <vector>
using namespace std;

const int N = 500010;

inline void read(int& x) {
  x = 0;
  char ch = getchar();
  int f = 1;
  while (ch < '0' || ch > '9') {
    if (ch == '-') {
      f = -1;
    }
    ch = getchar();
  }
  while (ch >= '0' && ch <= '9') {
    x = x * 10 + ch - '0';
    ch = getchar();
  }
  x *= f;
}

struct edge {
  int t;
  int val;
};

vector<edge> G[N];
int h[N];
int n, m, k;
int cnt;
set<int> used;
long long add[N];
vector<int> vis;

int main() {
  read(n), read(m), read(k);
  for (int i = 1; i <= m; i++) {
    int x, y, v;
    read(x), read(y), read(v);
    G[x].push_back({y, v});
    G[y].push_back({x, v});
  }
  for (int i = 1; i <= n; i++) {
    if (cnt < k) {
      h[i] = ++cnt;
      used.insert(cnt);
      continue;
    }
    vis.clear();
    for (auto edg : G[i]) {
      int t = edg.t;
      int val = edg.val;
      if (t < i) {
        int room = h[t];
        if (add[room] == 0) {
          vis.push_back(room);
        }
        add[room] += val;
        if (used.count(room)) {
          used.erase(room);
        }
      }
    }
    if (vis.size() < cnt) {
      h[i] = *used.begin();
    } else {
      int pos = 1;
      for (auto p : vis) {
        if (add[pos] > add[p]) {
          pos = p;
        }
      }
      h[i] = pos;
    }
    for (auto p : vis) {
      add[p] = 0;
      used.insert(p);
    }
  }
  printf("Yes\n");
  for (int i = 1; i <= n; i++) {
    printf("%d ", h[i]);
  }
  return 0;
}
```

#line(length: 100%)

== H 矩阵拆分

首先确定如下事实：$B$必须是一个对称矩阵且对角元必须为偶数，否则无解

接下来证明只要$B$是一个对称矩阵就可以找到解：

#quote-block()[坑了]

#line(length: 100%)

== J The Whole Rest

#quote-block()[考场上卡最后维护直径自刎归天了；虚树同样可以做，时间复杂度也是对的]

最保守的策略是把所有边都走一来一回，而且可以证明我们一条边最多走两次：

#theorem-box[][
  对一条合法且最短的的路径$P$，$P$中不可能存在一条边出现三次
]
#proof([
  这样的路径$P$可以看作将树上的若干条边复制若干次加入图中，得到的经过所有点的欧拉通路。我们最小化的目标是复制的次数

  由于图联通，由欧拉通路的存在充要条件有这样的图中至多有两个顶点的度数为奇数；显然，删去两条重复的边（保证图仍然联通）不会让任何节点的度数的奇偶性发生改变。即删去这两条边后，仍然存在遍历了所有边的欧拉回路

  由异或的性质有删去这两条边不会改变$P$中的权值异或和。
])

此时我们将问题转为了，将树上的所有边复制一份，我们要尽可能多地删除边使得
+ 保证存在欧拉通路
+ 保证权值异或和为0

由欧拉通路的存在性必要条件有我们至多删去树上一条异或和为0的连续的路径（否则会有多于两个顶点的度数为奇数）

现在只需要考虑如何找到这条最长的路径：

取根节点为$r$，记$"xor"_i$为根节点到节点$i$的路径的异或和。

则对于树上任意两点$x$,$y$，路径$P(x,y)$的异或和$"xor"(P(x,y))$ = $"xor"_x xor "xor"_y xor ("xor"_"lca(x,y)" xor "xor"_"lca(x,y)")="xor"_x xor "xor"_y$

则有$"xor"(P(x,y)) = 0 <=> "xor"_x = "xor"_y$

也就是说我们只需要找到尽可能长的路径，使得起点$s$和终点$t$的$"xor"$相等

我们可以简单地把所有权值相等的点挑出来，动态维护直径。

#theorem-box(
  [考虑已知目前树的直径上的两点为$s,t$，现在加入新的点$p$，则新的直径，根据$"dis"(s,p),"dis"(s,t),"dis"(p,t)$的大小关系会是如下三种情形之一：
    - $s,t$ ，如果$"dis"(s,t)$最大
    - $s,p$ ，如果$"dis"(s,p)$最大
    - $p,t$ ，如果$"dis"(p,t)$最大
  ],
)

由反证法可以验证这个算法的正确性，按下不表

我们只需要采用倍增法求lca就可以以单次$O(log n)$的时间复杂度完成一次$"dis"(x,y)$的查询；完成一次直径维护的时间复杂度是$O(K log n)$，其中$K$为该树大小

完成所有权值的如上维护的总时间复杂度是$O(n log n)$，足以通过

最后写一个dfs来完成对路径的输出即可，代码如下：

```cpp
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <vector>
using namespace std;

const int N = 500010;

inline void read(int& x) {
  x = 0;
  char ch = getchar();
  int f = 1;
  while (ch < '0' || ch > '9') {
    if (ch == '-') {
      f = -1;
    }
    ch = getchar();
  }
  while (ch >= '0' && ch <= '9') {
    x = x * 10 + ch - '0';
    ch = getchar();
  }
  x *= f;
}

struct edge {
  int t;
  int nxt;
  int val;
};

edge e[N << 1];
int head[N], cnt = -1;
int xr[N], dep[N];
int n;
map<int, vector<int>> mp;
int fa[N][20];
int vis[N];

void add(int x, int y, int val) {
  e[++cnt].nxt = head[x];
  e[cnt].t = y;
  e[cnt].val = val;
  head[x] = cnt;
}

void dfs(int p, int fat, int v) {
  xr[p] = v;
  fa[p][0] = fat;
  mp[v].push_back(p);
  dep[p] = dep[fat] + 1;
  for (int i = head[p]; i + 1; i = e[i].nxt) {
    int t = e[i].t;
    if (t == fat) {
      continue;
    }
    dfs(t, p, v ^ e[i].val);
  }
}

void lca_init() {
  for (int j = 1; j <= 19; j++) {
    for (int i = 1; i <= n; i++) {
      fa[i][j] = fa[fa[i][j - 1]][j - 1];
    }
  }
}

int lca(int x, int y) {
  if (dep[x] < dep[y]) {
    swap(x, y);
  }
  int depx = dep[x] - dep[y];
  for (int j = 0; depx; j++) {
    if (depx & 1) {
      x = fa[x][j];
    }
    depx >>= 1;
  }
  if (x == y) {
    return x;
  }
  for (int j = 19; j >= 0 && x != y; j--) {
    if (fa[x][j] == fa[y][j]) {
      continue;
    }
    x = fa[x][j];
    y = fa[y][j];
  }
  return fa[x][0];
}

int dist(int x, int y) { return dep[x] + dep[y] - dep[lca(x, y)] * 2; }

vector<int> ans;

void print_sub(int p) {
  vis[p] = 1;
  ans.push_back(p);
  for (int i = head[p]; i + 1; i = e[i].nxt) {
    int t = e[i].t;
    if (vis[t]) {
      continue;
    }
    print_sub(t);
    ans.push_back(p);
  }
}

int path_nx[N];

void print_ans(int s, int t) {
  int lc = lca(s, t);
  for (int p = s; p != lc; p = fa[p][0]) {
    vis[p] = 1;
    path_nx[p] = fa[p][0];
  }
  for (int p = t; p != lc; p = fa[p][0]) {
    vis[p] = 1;
    path_nx[fa[p][0]] = p;
  }
  vis[lc] = 1;
  for (int p = s; p != t; p = path_nx[p]) {
    print_sub(p);
  }
  print_sub(t);
  int siz = ans.size();
  printf("%d\n", siz);
  for (int i = 0; i < siz; i++) {
    printf("%d ", ans[i]);
  }
}

int main() {
  memset(head, -1, sizeof(head));
  read(n);
  for (int i = 1; i < n; i++) {
    int x, y, val;
    read(x), read(y), read(val);
    add(x, y, val);
    add(y, x, val);
  }
  dep[1] = 1;
  dfs(1, 1, 0);
  lca_init();
  int s = 1, t = 1;
  for (auto p : mp) {
    int val = p.first;
    vector<int>& V = p.second;
    int siz = V.size();
    if (siz <= 1) {
      continue;
    }
    int sp = V[0], tp = V[1];
    int disp = dist(sp, tp);
    for (int i = 2; i < siz; i++) {
      int t = V[i];
      int dis1 = dist(sp, t), dis2 = dist(t, tp);
      if (max(dis1, dis2) > disp) {
        if (dis1 > dis2) {
          tp = t;
          disp = dis1;
        } else {
          sp = t;
          disp = dis2;
        }
      }
    }
    if (dist(s, t) < disp) {
      s = sp;
      t = tp;
    }
  }
  print_ans(s, t);
  return 0;
}
```
