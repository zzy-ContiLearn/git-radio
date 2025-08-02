# 🎵 Git Radio

一个智能的GitHub动态播报工具，每天为你播报关注仓库的重要更新和GitHub热门项目趋势。

## ✨ 功能特色

- 📊 **智能监控**: 分析你starred的仓库过去24小时的重要动态
- 🔥 **热门趋势**: 获取GitHub今日trending项目
- 🤖 **AI摘要**: 使用GPT智能生成播报内容
- 🎙️ **语音播报**: 自动语音播报，解放双眼
- 📈 **重点筛选**: 自动识别热门PR、新版本发布等重要事件

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装Python 3.7+，然后安装依赖：

```bash
# 克隆项目
git clone <your-repo-url>
cd git-radio

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件并添加必要的API密钥：

```env
GITHUB_TOKEN=your_github_personal_access_token
OPENAI_API_KEY=your_openai_api_key  # 可选，用于AI摘要
```

#### 获取GitHub Token
1. 访问 [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. 点击 "Generate new token (classic)"
3. 选择权限：`repo`, `user:read`
4. 复制生成的token到 `.env` 文件

#### 获取OpenAI API Key（可选）
1. 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 创建新的API密钥
3. 复制到 `.env` 文件

> 💡 如果不配置OpenAI API，程序会使用内置的简单摘要功能

### 3. 运行程序

```bash
python git_radio.py
```

程序将自动：
1. 🔍 分析你starred的仓库过去24小时动态
2. 📈 获取GitHub今日热门项目
3. 🤖 生成智能摘要
4. 🎙️ 语音播报结果

## 📋 功能详解

### 智能事件筛选
程序会自动识别以下重要事件：
- 🔥 **热门PR**: 评论数超过5的Pull Request
- 🚀 **新版本发布**: Release事件
- 💡 **新功能**: 新的Pull Request
- 🐛 **问题跟踪**: Issues的创建和更新
- 📝 **代码提交**: 重要的Push事件

### Trending分析
- 📊 获取GitHub今日trending项目
- 🌟 显示今日新增star数
- 💻 标注编程语言
- 📖 提供项目描述

### AI摘要生成
- 🤖 使用GPT生成自然语言摘要
- 🗣️ 口语化表达，适合语音播报
- 📝 备用简单摘要（无需OpenAI API）

## ⚙️ 自定义配置

### 语音设置
在 `init_tts_engine()` 函数中可以调整：
- `rate`: 语速（默认150）
- `volume`: 音量（默认0.9）
- `voice`: 语音类型（默认女声）

### 监控范围
- 默认检查最近更新的10个starred仓库
- 可在 `main()` 函数中修改 `recent_repos[:10]` 调整数量

### 摘要风格
在 `summarize_with_gpt()` 函数中可以：
- 修改prompt模板
- 调整摘要长度
- 改变语言风格

## 🔧 系统要求

- **Python**: 3.7+
- **操作系统**: 
  - ✅ Windows（直接运行）
  - ✅ macOS（直接运行）
  - ✅ Linux（需安装espeak: `sudo apt install espeak`）

## 🏗️ 技术架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub API    │───▶│   数据处理模块    │───▶│   AI摘要生成     │
│ (Starred Repos) │    │ (事件筛选/分析)   │    │  (GPT/简单摘要)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             ▼
│ GitHub Trending │───▶│   网页解析模块    │    ┌─────────────────┐
│   (热门项目)     │    │ (BeautifulSoup)  │───▶│    语音播报      │
└─────────────────┘    └──────────────────┘    │   (pyttsx3)     │
                                               └─────────────────┘
```

## ⚠️ 注意事项

### API限制
- **GitHub API**: 每小时5000次请求（已登录）
- **OpenAI API**: 根据你的套餐限制
- 程序已内置延时机制避免触发限制

### 故障处理
- 🔄 网络异常时会自动重试
- 🛡️ API失败时使用备用方案
- 📝 详细的错误日志输出

### 隐私安全
- 🔐 API密钥存储在本地.env文件
- 🚫 不会上传任何个人数据
- 👀 只读取公开的GitHub信息

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

3. **语音优化**：
   - 需要更自然语音时可改用Google TTS：
     ```python
     engine.setProperty('voice', 'com.apple.speech.synthesis.voice.meijia')
     ```

此程序每日运行时将自动获取您关注的仓库动态和GitHub趋势，通过AI摘要后以清晰语音报告。您可将其设置为定时任务（如使用cron或Windows任务计划程序），实现每日自动化信息播报。