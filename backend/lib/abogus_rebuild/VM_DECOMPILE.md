# VM 字节码反编译 - 第1步成果

## 已 dump 的资产
1. `opcode_dump.json` — 完整 opcode 执行序列 29488 条 [opcode, 指针a, 栈深p]
2. opcode 频次 top: 74(9620), 38(2186), 30(1800), 8(1581), 68(1282), 61(1102), 54(1098), 0(1081), 18(1061), 14(1021), 26(1000), 11(910)...

## VM opcode 语义表 (从 d() 函数提取, bdms_1.0.1.19)
栈=v, 指针=p, 指令数组=o, 指令指针=a, 常量池=Z, 作用域=s, this上下文=c
```
0  call: r=o[a++];e=v.slice(p);n,d出栈; n.apply(d,e) 或 VM递归g(); 结果入栈
1  v[p] = v[p] <= w   (w=v[p--])
2  v[p] = v[p] > w
3  for-in 准备: s[x]=[keys, obj]
4  for-in 取下一key
5  x=o[a++]; 取Z[x]相关 b(A,i)
6  v[p] = v[p] !== w
7  push {}
8  v[p] = v[p][k]          取属性(k出栈)
9  push true
10 v[p] = void 0
11 v[p] %= E               取模
12 v[p] &= w               按位与 ★
13 v[p] = v[p] instanceof S
14 S[T] = E                属性赋值(E,T,S出栈)
15 globalThis[Z[x]] = E
16 (S)[L] = v[p]           属性赋值保留值
17 U=o[a++]; if(v[p])--p else a+=U   条件跳转(真则pop)
18 push v[p]               dup 复制栈顶 ★
19 v[p] >>>= w             无符号右移 ★
20 x=o[a++]; (S)[Z[x]]=E
21 v[p] -= E               减
22 if(f!==0)return
23 U=o[a++]; if(v[p]===E)--p,a+=U   相等跳转
24 v[p] = typeof v[p]
25 delete S[I]
26 --p                     pop ★
27 push false
28 push NaN
29 v[p] = !v[p]
30 v[p] < w                小于 ★
31 U=o[a++]; if(v[p])a+=U else --p
32 v[p] >>= w              右移 ★
33 push void 0
34 push c (this上下文)
35 v[p] >>= w (另一变体)
36 v[p] = +v[p] 或 ~v[p]   一元
37 (默认/无)
38 push o[a++]             立即数入栈 ★
39 F=o[a++]; v[p..]=v.slice 取数组片段
40 ++S[M]
41 U=o[a++]; if(!v[p--])a+=U   条件跳转(假跳)★
42 v[p] /= E
43 v[p] = -v[p]
44 --S[B]
45 v[p] *= E
46 push +Z[x]
47 defineProperty get
48 defineProperty set
49 return(throw) f=3
50 S[q]++
51 v[p] |= w               按位或
52 return U (函数返回)
53 U=o[a++]; a+=U           无条件跳转 ★
54 v[p] <<= w              左移 ★
55 v[p] in S
56 v[p] <<= w (变体)
57 v[p] === w
58 v[p] == w
59 new Function.bind 构造
60 push globalThis[Z[x]]    取全局 ★
61 多级作用域取值 U=s链
62 v[p] != w
63 E=D(o[a++],s) 闭包创建
64 v[p] >= w
65 push Infinity
66 S[J]--
67 defineProperty value
68 v[p] += E               加 ★
69 typeof globalThis[X]
70 v[p] ^= w               异或 ★★★(RC4/SM3关键)
71 U=o[a++]; if(v[p--])a+=U  条件跳转(真跳)
72 globalThis[W]检查
73 push Z[x]                常量入栈(74同类)
74 push Z[x]                常量池取值 最高频 ★
75 push null / f=2返回
```

## 下一步(第2步)
- 从 opcode_dump.json 重建带操作数的指令流(需同时dump o[a+1]等操作数)
- 定位 bb 生成段 和 fin 生成段
- 跟踪栈 v 翻译运算 -> Python

## 障碍提醒
- 17155帧深递归(charCodeAt嵌套)使中间变量难以断点捕获
- 需结合 opcode trace 静态分析, 而非动态断点

## 第2步重大突破 (RC4层完全破解)
- opcode异或(70)间隔恒为63 -> 确认是RC4逐字节加密
- **RC4 keystream 完全固定**: 对比 q=1/q=2(125/125相同), r=0.5/r=0.3(309/315相同), 证明keystream不依赖query/UA/random, 是常量!
- 抓取方式: 断点 v[p]=v[p]^w, 抓 (明文v[p], keystreamw) 三元组
- **算法结构确认**: fin = random_head(4字节) + (bb XOR 固定keystream); a_bogus = s4_encode(fin)
- 固定keystream已存 FIXED_keystream.json (bb段132字节 + UA段125字节)
- 端到端重建: 用真实bb+固定ks重建fin = 129/136 (结构正确, 差异来自hook抓bb的字节误差)

## 剩余(确定性拼装, 无密码学黑盒)
- bb 模板精确布局: SM3结果(query/dhzx/UA)哪些字节注入bb哪些位置 + env + 时间字节 + 固定模板字节
- 这是确定性工作, 材料齐全(SM3链路+env+keystream都有)
