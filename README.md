## 🌐 在线体验

无需部署，直接访问体验：

**🦆 DuckCloud域名：** https://jimeng_xiaohongshu.duckcloud.fun/

**🌐 IP直连：** http://115.190.165.156:5500/

⚡ 即开即用，体验AI小红书内容创作！

> 💡 **使用提示**：访问后点击右上角"设置"按钮，配置您的API Key即可开始创作。支持Google Gemini、即梦等多种AI服务。

---

## ✨ 效果展示

### 输入一句话,就能生成完整的小红书图文

#### 提示词：秋季显白美甲（暗广一个：小香蕉牌美甲），图片 是我的小红书主页。符合我的风格生成

#### 同时我还截图了我的小红书主页，包括我的头像，签名，背景，姓名什么的

![示例1](./images/example-1.png)

#### 然后等待10-20秒后，就会有每一页的大纲，大家可以根据的自己的需求去调整页面顺序（不建议），自定义每一个页面的内容（这个很建议）

![示例2](./images/example-2.png)

#### 首先生成的是封面页

![示例3](./images/example-3.png)

#### 然后稍等一会儿后，会生成后面的所有页面（这里是并发生成的所有页面（默认是15个），如果大家的API供应商无法支持高并发的话，记得要去改一下设置）

![示例4](./images/example-4.png)

---

## 🏗️ 技术架构

### 后端
- **语言**: Python 3.11+
- **框架**: Flask
- **AI 模型**:
  - Gemini 3 (文案生成)
  - Google Gemini Image 3 Pro (图片生成)
  - OpenAI DALL-E 3 (图片生成)
  - 即梦（JiMeng）4.5 (图片生成)
- **包管理**: uv

### 前端
- **框架**: Vue 3 + TypeScript
- **构建**: Vite
- **状态管理**: Pinia

---

## 📦 如何自己部署

### 方式一：Docker 部署（推荐）

**最简单的部署方式，一行命令即可启动：**

```bash
  docker run -d -p 5500:5500 \
    -v ./history:/app/history \
    -v ./output:/app/output \
    -v ./text_providers.yaml:/app/text_providers.yaml \
    -v ./image_providers.yaml:/app/image_providers.yaml \
    wwwzhouhui569/jimeng_xiaohongshu:latest
```

访问 http://localhost:5500，在 Web 界面的**设置页面**配置你的 API Key 即可使用。

**使用 docker-compose（可选）：**

下载 [docker-compose.yml](https://github.com/xiaohuihui202504/JiMeng_XiaoHongShu/blob/main/docker-compose.yml) 后：

```bash
docker-compose up -d
```

**Docker 部署说明：**
- 容器内不包含任何 API Key，需要在 Web 界面配置
- 使用 `-v ./history:/app/history` 持久化历史记录
- 使用 `-v ./output:/app/output` 持久化生成的图片
- 可选：挂载自定义配置文件 `-v ./text_providers.yaml:/app/text_providers.yaml`
- 可选：挂载图片生成配置文件 `-v ./image_providers.yaml:/app/image_providers.yaml`

---

### 方式二：本地开发部署

**前置要求：**
- Python 3.11+
- Node.js 18+
- pnpm
- uv

### 1. 克隆项目
```bash
git clone https://github.com/xiaohuihui202504/JiMeng_XiaoHongShu.git
cd JiMeng_XiaoHongShu
```

### 2. 配置 API 服务

复制配置模板文件：
```bash
cp text_providers.yaml.example text_providers.yaml
cp image_providers.yaml.example image_providers.yaml
```

编辑配置文件，填入你的 API Key 和服务配置。也可以启动后在 Web 界面的**设置页面**进行配置。

### 3. 安装后端依赖
```bash
uv sync
```

### 4. 安装前端依赖
```bash
cd frontend
pnpm install
```

### 5. 启动服务

**启动后端:**
```bash
uv run python -m backend.app
```
访问: http://localhost:5500

**启动前端:**
```bash
cd frontend
pnpm dev
```
访问: http://localhost:5173

---

## 🎮 使用指南

### 基础使用
1. **输入主题**: 在首页输入想要创作的主题,如"如何在家做拿铁"
2. **生成大纲**: AI 自动生成 6-9 页的内容大纲
3. **编辑确认**: 可以编辑和调整每一页的描述
4. **生成图片**: 点击生成,实时查看进度
5. **下载使用**: 一键下载所有图片

### 进阶使用
- **上传参考图片**: 适合品牌方,保持品牌视觉风格
- **修改描述词**: 精确控制每一页的内容和构图
- **重新生成**: 对不满意的页面单独重新生成

---

## 🔧 配置说明

### 配置方式

项目支持两种配置方式：

1. **Web 界面配置（推荐）**：启动服务后，在设置页面可视化配置
2. **YAML 文件配置**：直接编辑配置文件

### 文本生成配置

配置文件: `text_providers.yaml`

```yaml
# 当前激活的服务商
active_provider: openai

providers:
  # OpenAI 官方或兼容接口
  openai:
    type: openai_compatible
    api_key: sk-xxxxxxxxxxxxxxxxxxxx
    base_url: https://api.openai.com/v1
    model: gpt-4o

  # Google Gemini（原生接口）
  gemini:
    type: google_gemini
    api_key: AIzaxxxxxxxxxxxxxxxxxxxxxxxxx
    model: gemini-2.0-flash
```

### 图片生成配置

配置文件: `image_providers.yaml`

```yaml
# 当前激活的服务商
active_provider: gemini

providers:
  # Google Gemini 图片生成
  gemini:
    type: google_genai
    api_key: AIzaxxxxxxxxxxxxxxxxxxxxxxxxx
    model: gemini-3-pro-image-preview
    high_concurrency: false  # 高并发模式

  # OpenAI 兼容接口
  openai_image:
    type: image_api
    api_key: sk-xxxxxxxxxxxxxxxxxxxx
    base_url: https://your-api-endpoint.com
    model: dall-e-3
    high_concurrency: false

  # 即梦（JiMeng）4.5 图片生成
  jimeng:
    type: image_api  # 使用通用image_api类型
    api_key: your-jimeng-api-key
    base_url: https://jimeng1.duckcloud.fun
    model: jimeng-4.5
    image_size: 2k  # 支持: 1k, 2k, 4k（小写格式）
    default_aspect_ratio: 3:4  # 支持: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
    endpoint_type: /v1/images/generations  # 文生图端点
    high_concurrency: false
```

### 高并发模式说明

- **关闭（默认）**：图片逐张生成，适合 GCP 300$ 试用账号或有速率限制的 API
- **开启**：图片并行生成（最多15张同时），速度更快，但需要 API 支持高并发

⚠️ **GCP 300$ 试用账号不建议启用高并发**，可能会触发速率限制导致生成失败。

### 即梦（JiMeng）API 配置说明

即梦4.5图片生成器支持文生图和图生图功能，使用通用的 `image_api` 类型配置。

**关键配置项：**

1. **base_url**: `https://jimeng1.duckcloud.fun`
   - 即梦API的Base URL地址

2. **image_size**: 推荐使用 `2k`（小写）
   - ✅ 支持：`1k`, `2k`, `4k`
   - ❌ 不支持：`1K`, `2K`, `4K`（大写格式会报错）

3. **endpoint_type**:
   - 文生图：`/v1/images/generations`（默认）
   - 图生图：自动切换到 `/v1/images/compositions`（当使用参考图片时）

4. **支持的功能**：
   - ✅ 文生图：直接根据提示词生成图片
   - ✅ 图生图：上传1-4张参考图片，保持风格一致
   - ✅ 多种宽高比：1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
   - ✅ 自动重试：失败后自动重试最多3次

**图生图功能：**
当上传参考图片时，系统会自动：
- 使用 `/v1/images/compositions` 端点
- 压缩参考图片至200KB以内
- 保持参考图的风格、色彩和构图
- 生成符合要求的新图片

---

## ⚠️ 注意事项

1. **API 配额限制**:
   - 注意 即梦和图片生成 API 的调用配额
   - GCP 试用账号建议关闭高并发模式

2. **生成时间**:
   - 图片生成需要时间,请耐心等待（不要离开页面）

3. **即梦API特殊注意事项**:
   - ⚠️ 分辨率格式必须使用小写：`1k`, `2k`, `4k`（大写会导致API错误）
   - ⚠️ 确保API Key有效且未过期
   - ⚠️ 图生图功能需要上传1-4张参考图片
   - 📁 参考图片会自动压缩至200KB以内
   - 🔄 系统会自动重试失败的请求（最多3次）

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request!

如果这个项目对你有帮助,欢迎给个 Star ⭐

### 未来计划
- [ ] 支持更多图片格式，例如一句话生成一套PPT什么的
- [x] 历史记录管理优化
- [ ] 导出为各种格式(PDF、长图等)
- [ ] 支持视频生成功能
- [ ] 批量生成和管理功能
- [ ] 自定义风格模板

---

## 更新日志

### v1.5.1 (2025-12-10)
- 🔧 修复即梦API分辨率格式问题，支持小写格式（1k, 2k, 4k）
- 🔧 修复即梦API响应处理错误，避免NoneType异常
- 🔧 优化即梦API参数映射：ratio、resolution、negativePrompt
- ✨ 完善即梦图生图功能，自动切换端点（/v1/images/compositions）
- 📝 更新README文档，添加即梦API配置详细说明

### v1.5.0 (2025-12-09)
- ✨ 新增即梦（JiMeng）4.5图片生成器支持
- ✨ 支持多种图片生成服务：Google Gemini、OpenAI DALL-E 3、即梦
- 🔧 增强错误处理和API兼容性，优化生成图片功能
- 🔧 添加自动重试机制，提高生成成功率
- 🔧 支持参考图片URL，优化图生图功能
- 📦 完善Docker配置，提供空白配置模板

### v1.4.0 (2025-11-30)
- 🏗️ 后端架构重构：拆分单体路由为模块化蓝图（history、images、generation、outline、config）
- 🏗️ 前端组件重构：提取可复用组件（ImageGalleryModal、OutlineModal、ShowcaseBackground等）
- ✨ 优化首页设计，移除冗余内容区块
- ✨ 背景图片预加载和渐入动画，提升加载体验
- ✨ 历史记录持久化支持（Docker部署）
- 🔧 修复历史记录预览和大纲查看功能
- 🔧 优化Modal组件可见性控制
- 🧪 新增65个后端单元测试

### v1.3.0 (2025-11-26)
- ✨ 新增 Docker 支持，一键部署
- ✨ 发布官方 Docker 镜像到 Docker Hub: `histonemax/LitBanana`
- 🔧 Flask 自动检测前端构建产物，支持单容器部署
- 🔧 Docker 镜像内置空白配置模板，保护 API Key 安全
- 📝 更新 README，添加 Docker 部署说明

### v1.2.0 (2025-11-26)
- ✨ 新增版权信息展示，所有页面显示开源协议和项目链接
- ✨ 优化图片重新生成功能，支持单张图片重绘
- ✨ 重新生成图片时保持风格一致，传递完整上下文（封面图、大纲、用户输入）
- ✨ 修复图片缓存问题，重新生成的图片立即刷新显示
- ✨ 统一文本生成客户端接口，支持 Google Gemini 和 OpenAI 兼容接口自动切换
- ✨ 新增 Web 界面配置功能，可视化管理 API 服务商
- ✨ 新增高并发模式开关，适配不同 API 配额
- ✨ API Key 脱敏显示，保护密钥安全
- ✨ 配置自动保存，修改即时生效
- 🔧 调整默认 max_output_tokens 为 8000，兼容更多模型限制
- 🔧 优化前端路由和页面布局，提升用户体验
- 🔧 简化配置文件结构，移除冗余参数
- 🔧 优化历史记录图片显示，使用缩略图节省带宽
- 🔧 历史记录重新生成时自动从文件系统加载封面图作为参考
- 🐛 修复 `store.updateImage` 方法缺失导致的重新生成失败问题
- 🐛 修复历史记录加载时图片 URL 拼接错误
- 🐛 修复下载功能中原图参数处理问题
- 🐛 修复图片加载 500 错误问题

---

## 📄 开源协议

### 个人使用 - CC BY-NC-SA 4.0

本项目采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 协议进行开源

**你可以自由地：**
- ✅ **个人使用** - 用于学习、研究、个人项目
- ✅ **分享** - 在任何媒介以任何形式复制、发行本作品
- ✅ **修改** - 修改、转换或以本作品为基础进行创作

**但需要遵守以下条款：**
- 📝 **署名** - 必须给出适当的署名，提供指向本协议的链接，同时标明是否对原始作品作了修改
- 🚫 **非商业性使用** - 不得将本作品用于商业目的
- 🔄 **相同方式共享** - 如果你修改、转换或以本作品为基础进行创作，你必须以相同的协议分发你的作品

---

### 免责声明

本软件按"原样"提供，不提供任何形式的明示或暗示担保，包括但不限于适销性、特定用途的适用性和非侵权性的担保。在任何情况下，作者或版权持有人均不对任何索赔、损害或其他责任负责。

---

## 🙏 致谢

本项目基于以下开源项目的二次开发和改造：

- **[RedInk](https://github.com/HisMax/RedInk)** 
