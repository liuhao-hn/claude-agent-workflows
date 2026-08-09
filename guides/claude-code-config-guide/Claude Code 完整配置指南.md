# Claude Code 完整配置指南

**DeepSeek 版 · 零基础保姆级教程**

---

> 在实证研究中，Claude Code 是一套强大的 AI 自主智能体系统。本文从"零编程基础"出发，详细梳理从 Node.js 安装、Git 配置、Claude Code 本体安装，到 DeepSeek API 连接、自定义 Skill 导入的全流程。特别补充了 Windows PowerShell 权限问题的解决方案。

---

## 一、整体流程预览

整个安装分为 6 步：

1. **安装 Node.js**（电脑的翻译器）
2. **安装 Git**（文件管理器）
3. **安装 Claude Code 本体**（AI 大脑）
4. **安装编辑器**（VS Code 或 Trae）
5. **配置 API 连接**（让 AI 连上 DeepSeek 服务器）
6. **导入 Skill**（安装别人分享的专属 AI 能力包）

---

## 二、第一步：安装 Node.js

Claude Code 需要 Node.js 作为运行环境，可以把它理解成一个"翻译器"。

### Windows

1. 打开浏览器，访问 https://nodejs.org/en/download/
2. 点击 **Windows Installer (.msi)** 下载
3. 双击下载的文件，一路点 **Next**（所有默认选项都对）
4. 验证安装：按 `Win` 键，输入 **PowerShell**，回车打开

```bash
node -v
```

看到类似 `v20.10.0` 就成功了。

```bash
npm -v
```

**如果 npm -v 报红字错误（常见于首次使用 PowerShell）**，先输入：

```powershell
Set-ExecutionPolicy RemoteSigned
```

会提示你输入 `Y` 确认，输完后再试 `npm -v` 看到版本号就正常了。

### Mac

1. 访问 https://nodejs.org/en/download/
2. 点击 **macOS Installer (.pkg)** 下载
3. 双击安装，按提示操作
4. 打开终端（在启动台搜索"终端"），验证：

```bash
node -v
npm -v
```

---

## 三、第二步：安装 Git

Git 是版本管理工具，Claude Code 需要它来管理文件。

### Windows

1. 访问 https://git-scm.com/downloads
2. 下载 Windows 版本，双击安装
3. 大部分选项保持默认，重点注意：当看到 **"Adjusting your PATH environment"** 页面时，选择中间那个选项：**Git from the command line and also from 3rd-party software**
4. 其他页面直接点 Next

```bash
git --version
```

看到版本号即成功。

### Mac

Mac 通常自带 Git。打开终端输入：

```bash
git --version
```

如果没装，系统会自动弹窗提示安装 Xcode Command Line Tools，点安装即可。

---

## 四、第三步：安装 Claude Code 本体

打开 **PowerShell**（Windows）或**终端**（Mac），输入：

```bash
npm install -g @anthropic-ai/claude-code --registry=https://registry.npmmirror.com
```

> `--registry=https://registry.npmmirror.com` 是使用国内镜像，下载更快。

等待几分钟，看到文字停止滚动且没有红色 `error` 字样，即安装成功。

> **注意：** 不要在命令前加 `sudo`，否则可能导致权限问题。

---

## 五、第四步：安装编辑器

编辑器是 Claude Code 的工作台，通过它和 AI 对话。二选一即可。

### 选项一：VS Code（推荐）

- 下载地址：https://code.visualstudio.com/
- Windows：下载后双击安装，建议勾选"添加到 PATH"和"添加右键菜单"
- Mac：下载后把 `Visual Studio Code.app` 拖到应用程序文件夹

### 选项二：Trae IDE

- 下载地址：https://www.trae.cn/
- 字节跳动旗下产品，基于 VS Code，界面对中文用户更友好
- 下载后双击安装即可

---

## 六、第五步：配置 API 连接

这是最关键的一步。

### 6.1 安装 Claude Code 插件

1. 打开 VS Code 或 Trae
2. 点击侧边栏的**扩展图标**（四个方块图案）
3. 搜索：**Claude Code for VS Code**
4. 点击安装

### 6.2 获取 DeepSeek API Key

1. 打开浏览器，访问 https://platform.deepseek.com/
2. 注册 / 登录账号
3. 进入 **API Keys** 页面，点击"创建新的 API Key"
4. 复制保存这串 Key（格式类似 `sk-xxxxxxxxxxxxxxxx`）

> **重要：** API Key 相当于密码，请妥善保管，不要分享给他人或发到网上。

### 6.3 写入配置文件

1. 在 VS Code / Trae 中，按快捷键：
   - Windows：`Ctrl + Shift + P`
   - Mac：`Cmd + Shift + P`
2. 输入：**Preferences: Open User Settings (JSON)**
3. 回车，会打开一个 JSON 配置文件
4. 将以下内容粘贴进去（如果文件已有其他内容，合并时注意 JSON 格式）：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "你的DeepSeek-API-Key粘贴在这里",
    "ANTHROPIC_MODEL": "DeepSeek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "DeepSeek-v4-flash",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "DeepSeek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "DeepSeek-v4-pro[1m]",
    "ANTHROPIC_REASONING_MODEL": "DeepSeek-v4-pro[1m]",
    "ENABLE_TOOL_SEARCH": "true"
  },
  "includeCoAuthoredBy": false,
  "enabledPlugins": {
    "claude-hud@claude-hud": true,
    "skill-creator@claude-plugins-official": true
  },
  "extraKnownMarketplaces": {
    "claude-hud": {
      "source": {
        "source": "github",
        "repo": "jarrodwatts/claude-hud"
      }
    }
  },
  "effortLevel": "high"
}
```

**关键操作：** 找到 `"你的DeepSeek-API-Key粘贴在这里"` 这一行，把中文部分替换成你的 DeepSeek API Key。**其他地方不要动。**

替换后类似：`"sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"`

### 6.4 保存并重启

- 按 `Ctrl + S`（Windows）或 `Cmd + S`（Mac）保存
- **完全关闭** VS Code / Trae，再重新打开
- 重启后配置才能生效

### 6.5 测试

1. 打开 VS Code / Trae，随便打开一个文件夹
2. 点击 Claude Code 图标（通常在侧边栏或右上角）
3. 输入 `你好`
4. AI 回复你了 → 配置成功！

---

## 七、第六步：导入 Skill（AI 能力包）

Skill 是别人配置好的专属 AI 能力，导入后 Claude Code 会自动识别并加载。

### 7.1 获取 Skill 包

你会拿到一个 `claude-skills-export.tar.gz` 文件，把它放到桌面上。

### 7.2 解压安装

**Mac 用户——打开终端，输入：**

```bash
tar -xzf ~/Desktop/claude-skills-export.tar.gz -C ~/.claude/skills/
```

**Windows 用户——打开 PowerShell，输入：**

```powershell
tar -xzf "$env:USERPROFILE\Desktop\claude-skills-export.tar.gz" -C "$env:USERPROFILE\.claude\skills\"
```

> 如果 Windows 提示找不到 tar 命令，先安装 7-Zip 手动解压，再把解压出的 4 个文件夹复制到 `C:\Users\你的用户名\.claude\skills\` 目录下。

### 7.3 验证

解压完成后，确保目录结构像这样：

```
~/.claude/skills/
├── academic-search/
│   └── SKILL.md
├── coder-critic-review-team/
│   └── SKILL.md
├── deeppapernote/
│   └── SKILL.md
└── gaodun-essay-grader/
    └── SKILL.md
```

重启 Claude Code 后，输入对话触发相应功能即可自动加载 Skill。

### 7.4 本 Skill 包包含的能力

| Skill | 说明 |
| :--- | :--- |
| `academic-search` | 经济学论文搜索、引用分析，支持中英文多平台（arXiv、SSRN、NBER、知网等） |
| `coder-critic-review-team` | 多 Agent 代码审查协作工作流 |
| `deeppapernote` | 论文深度阅读笔记生成（输出 Obsidian 格式） |
| `gaodun-essay-grader` | 申论大作文五维度批改（40分制评分体系） |

---

## 八、常见问题

### npm install 提示权限错误（EACCES）

不要用 sudo。按以下步骤修复：

**Mac：**

```bash
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

重新打开终端，再次尝试安装。

### npm -v 报错（Windows PowerShell）

```powershell
Set-ExecutionPolicy RemoteSigned
```

输入 `Y` 确认，然后重新执行 `npm -v`。

### API 连接失败

1. 确认 API Key 复制正确，没有多余空格和换行
2. 确认 settings.json 中的 JSON 格式正确（注意逗号和引号不能错）
3. 确认已**完全关闭并重新打开**编辑器
4. 检查网络连接是否正常（DeepSeek API 需要稳定的网络）

### Skill 没有生效

1. 确认文件夹放在了正确的路径（`~/.claude/skills/` 下）
2. 每个 Skill 文件夹里必须有一个 `SKILL.md` 文件
3. 重启 Claude Code

---

## 九、安装完成检查清单

| | 检查项 |
| :--- | :--- |
| ☐ | Node.js 已安装（`node -v` 显示版本号） |
| ☐ | Git 已安装（`git --version` 显示版本号） |
| ☐ | Claude Code 已安装（`claude --version` 无报错） |
| ☐ | VS Code 或 Trae 已安装 |
| ☐ | Claude Code 插件已安装 |
| ☐ | DeepSeek API Key 已配置到 settings.json |
| ☐ | 启动后输入"你好"得到 AI 回复 |
| ☐ | Skill 包已解压到 `~/.claude/skills/` 目录 |

全部打勾？恭喜，配置完成！
