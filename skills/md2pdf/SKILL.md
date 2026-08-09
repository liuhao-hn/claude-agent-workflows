---
name: md2pdf
description: |
  将 Markdown 文档转换为专业排版的中文 PDF——严格遵循 TFP 测度方法详解的排版风格。
  工作流：MD（内容草稿）→ TEX（ctexart 排版）→ PDF（xelatex 编译）。
  自动触发：用户要求"生成 PDF""排版""转为 PDF""输出为 PDF""按 TFP 格式输出"等。
---

# MD → TEX → PDF 专业排版 Skill

遵循 TFP 测度方法详解的排版风格，将 Markdown 文档转换为 A4 纸专业 PDF。

## 排版规范（参照 TFP_测度方法详解）

### 文档类与包
```latex
\documentclass[12pt,a4paper]{ctexart}

% ==== 段落容错（减少 Overfull 警告）====
\emergencystretch=1em

% ==== Packages ====
\usepackage{amsmath,amssymb}
\usepackage[margin=2.5cm]{geometry}
\usepackage[hidelinks]{hyperref}   % 去掉目录和链接的红框
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{array}
\usepackage{ragged2e}              % \RaggedRight 防止表格列溢出
\usepackage{fancyvrb}
\usepackage{fvextra}               % 支持代码块内自动断行
\usepackage{xcolor}
\usepackage{enumitem}
```

### 代码块环境
- 用 `\DefineVerbatimEnvironment` 自定义环境名（如 `shcode`、`stata`、`jsoncode`）
- 样式：`fontsize=\small,frame=single,framesep=4pt,rulecolor=\color{gray!50}`
- 每种语言使用独立的环境名

### 表格规范

**核心原则：三线表 + 全篇宽度一致。** 使用 `booktabs` 的三线风格（顶线、中线、底线），全篇表格宽度统一为 `\textwidth`，通过列宽比例分配实现视觉一致。

**基础模板：**

```latex
{\centering
\begin{tabular}{>{\RaggedRight\arraybackslash}p{Xcm}>{\RaggedRight\arraybackslash}p{Ycm}>{\RaggedRight\arraybackslash}p{Zcm}}
\toprule
列1 & 列2 & 列3 \\
\midrule
内容 & 内容 & 内容 \\
\bottomrule
\end{tabular}
\par}
```

**全篇宽度一致规则：**

1. 全篇所有表格的 `p{}` 列宽之和需等于 `\textwidth`（A4 纸 margin=2.5cm 时，textwidth ≈ 16cm）
2. 根据列数和内容性质分配列宽比例：
   - 2 列表：`p{4cm}p{12cm}` 或 `p{5cm}p{11cm}` 或 `p{8cm}p{8cm}`（总和 16cm）
   - 3 列表：按 4:6:6、5:5:6、4:4:8 等比例，总和 16cm
   - 4 列表：每列约 4cm，或根据内容调整为 3:5:4:4
   - 5+ 列表：压缩每列宽度，必要时缩小字号到 `\small`
3. 同一文档中，信息密度相近的表格尽量用相同的列宽分配
4. 宽表用 `\small` 或 `\footnotesize` 缩小字号以容纳更多列，但不同表之间字号保持一致

**常见列宽搭配（总和≈16cm）：**

```latex
% 2列：标签-内容型
{p{3cm}p{13cm}}  或  {p{4cm}p{12cm}}  或  {p{5cm}p{11cm}}

% 3列：对比型
{p{4cm}p{6cm}p{6cm}}  或  {p{5cm}p{5.5cm}p{5.5cm}}

% 3列：属性-值-值型
{p{3cm}p{6.5cm}p{6.5cm}}

% 4列：多维度型
{p{3cm}p{4.3cm}p{4.3cm}p{4.3cm}}

% 5+列：数据密集型
\small
{p{3cm}p{3.2cm}p{3.2cm}p{3.2cm}p{3.2cm}}
```

**其他规则：**

- 每列必须用 `>{\RaggedRight\arraybackslash}p{...}` 防止长文本溢出
- 数字列可用 `>{\RaggedLeft\arraybackslash}p{...}` 右对齐
- 等宽字体内容（`\texttt`）在表格中加 `\small` 或 `\footnotesize`
- 表内文字过长时优先调列宽比例，不是缩小总宽度

### 列表规范
- `\begin{enumerate}[nosep]` 或 `\begin{itemize}[nosep]`（紧凑间距）

### 章节编号规范

**推荐方案：一级标题用"第X章"，二级标题用 1.1 式阿拉伯数字。** 这样顶层有中文章名的大气，子层有阿拉伯数字的精确对齐。

```latex
% ==== 章节编号：section 用“第X章”，subsection 用 1.1 ====
\ctexset{
  section/name = {第,章},
  section/number = \chinese{section},
  subsection/number = \arabic{section}.\arabic{subsection},
  subsubsection/number = \arabic{section}.\arabic{subsection}.\arabic{subsubsection}
}
```

**示例效果：**
```
第一章  四大核心板块
  1.1  增长率
    1.1.1  一般增长
  1.2  比重
第二章  特殊比率
  2.1  贡献率与拉动增长率
```

**规则：**
- `\section{}` 标题中不再写"第一部分"等手工编号，LaTeX 会自动加"第X章"
- `\subsection{}` 和 `\subsubsection{}` 标题中也去掉"一、"和"1.1"等前缀，由 LaTeX 编号
- 对于非教科书的实用文档（如手册），可改用 ctexart 默认编号（一、二、三...），不设此配置

### 数学规范
- 行内公式用 `$...$`
- 行间公式用 `\begin{equation}...\end{equation}`

### 文档结构
```latex
% ==== 段落容错 ====
\emergencystretch=1em

% ==== Packages ====
...
\begin{document}
\maketitle
\begin{abstract}...\end{abstract}

\newpage           % 摘要单独一页

\tableofcontents

\newpage           % 目录单独一页

% 正文...
\end{document}
```

**页面结构：** 第 1 页标题+摘要 → 第 2 页目录 → 第 3 页起正文

### 内容约定
- 代码块中 `_` 需转义为 `\_`（LaTeX 下标符）
- URL 用 `\url{...}` 包裹
- 中文引号用 `` `` 和 '' ``
- 反斜线 `\` 在代码块外用 `\textbackslash`，代码块内用 `\textbackslash` 或直接写
- `~` 在路径中保持原样（Verbatim 环境内）
- 破折号用 `--` 或 `---`
- `→` 用 `$\to$`

## 工作流程

### Step 1: 确认内容
- 如果用户提供了 MD 文件，直接读取
- 如果用户口述内容，先写成 MD 文件保存到桌面，请用户确认
- MD 文件使用清晰的章节结构（`#`、`##`、`###`）

### Step 2: 生成 TEX 文件
- 参照 references/tex-template.tex 的模板结构
- 将 MD 内容按排版规范转换为 TEX
- 选择合适的代码块环境名（shcode / jsoncode / stata / pythoncode 等）
- TEX 文件保存到 MD 同目录，同名不同后缀

### Step 3: 编译 PDF
```bash
cd <tex文件所在目录> && xelatex -interaction=nonstopmode <文件名>.tex && xelatex -interaction=nonstopmode <文件名>.tex
```
- 编译两遍：第一遍生成目录/交叉引用，第二遍写入
- 编译后清理辅助文件（.aux, .log, .out, .toc），保留 .tex 和 .pdf

### Step 4: 输出
- 将 PDF 路径告知用户
- 如果用户要求调整格式，修改 TEX 文件后重新编译

## 关键检查项
- [ ] TEX 文件含 `\documentclass[12pt,a4paper]{ctexart}`
- [ ] 代码块使用 `fancyvrb` + `\DefineVerbatimEnvironment`
- [ ] 表格使用 `booktabs`（toprule/midrule/bottomrule）
- [ ] 列表使用 `[nosep]`
- [ ] 中文引号正确转义
- [ ] 编译两遍 xelatex
- [ ] PDF 可正常打开
