# 🪙 比特币地址生成器

> **⚠️ 仅供教育用途** - 本项目专为学习比特币密码学和地址生成概念而设计。切勿将生成的私钥用于真实的比特币交易。

一个用于学习比特币地址生成和密码学概念的全栈教育项目，支持多种地址类型和个性化地址生成。

## ✨ 功能特性

- 🎯 **多种地址类型**：支持 P2PKH、P2SH-P2WPKH、P2WPKH 和 P2TR (Taproot)
- 🔍 **模式匹配**：生成具有自定义前缀、后缀或包含特定字符串的地址
- ⚡ **双重生成模式**：
  - 后端生成器，支持 WebSocket 实时更新
  - 前端生成器，支持离线批量生成
- 📊 **实时可视化**：实时生成进度显示，支持暂停/恢复功能
- 📋 **历史管理**：自动保存生成的地址，支持搜索、过滤和导出功能
- 🔒 **安全特性**：私钥默认隐藏，仅本地存储
- 📱 **响应式界面**：现代化 Vue.js 界面，适配所有设备
- 📤 **导出功能**：支持将历史记录导出为 JSON 文件

## 🚀 快速开始

### 方式一：自动化安装（推荐）

```bash
# 克隆并安装所有依赖
git clone https://github.com/GoodmanNegev/bitcoin_address_generator.git
cd bitcoin_address_generator
chmod +x setup.sh
./setup.sh
```

### 方式二：手动安装

#### 后端安装
```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### 前端安装
```bash
cd frontend
chmod +x node_modules/.bin/vite 
npm install
npm run dev
#npm run dev -- --host 0.0.0.0 
```

### 访问应用
在浏览器中打开：**http://localhost:5173**

## 🏗️ 项目结构

```
bitcoin_address_generator/
├── 📁 backend/                 # FastAPI 后端
│   ├── 🐍 main.py             # FastAPI 应用程序入口
│   ├── 🔧 btc_generator.py    # 完整的比特币地址生成器
│   ├── 🔧 btc_generator_simple.py # 简化版本（仅标准库）
│   └── 📋 requirements.txt    # Python 依赖
├── 📁 frontend/               # Vue.js 前端
│   ├── 📁 src/
│   │   ├── 🎨 App.vue         # 主 Vue 组件
│   │   ├── 🎨 FrontendGenerator.vue # 浏览器端生成器
│   │   ├── ⚙️ CryptoWorker.js  # Web Worker 加密操作
│   │   └── 🚀 main.js         # 应用程序入口
│   ├── 📋 package.json        # Node.js 依赖
│   ├── ⚙️ vite.config.js      # Vite 配置
│   └── 🌐 index.html         # HTML 模板
├── 🔧 setup.sh               # 自动化安装脚本
└── 📖 README.md              # 本文件
```

## 🎮 使用指南

### 生成器模式

#### 🖥️ 后端生成器
- **适用场景**：单个地址生成，需要实时进度显示
- **功能特性**：WebSocket 连接、暂停/恢复、实时统计
- **使用要求**：需要后端服务器运行

#### 🌐 前端生成器
- **适用场景**：批量生成、离线使用
- **功能特性**：纯浏览器端、无服务器依赖、Web Worker 支持
- **使用要求**：仅需现代浏览器

### 支持的地址类型

| 类型 | 格式 | 示例 | 描述 |
|------|------|------|------|
| **P2PKH** | `1...` | `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` | 传统地址 |
| **P2SH-P2WPKH** | `3...` | `3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy` | 嵌套隔离见证 |
| **P2WPKH** | `bc1q...` | `bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4` | 原生隔离见证 |
| **P2TR** | `bc1p...` | `bc1p5d7rjq7g6rdk2yhzks9smlaqtedr4dekq08ge8ztwac72sfr9rusxg3297` | Taproot 地址 |

### 模式匹配

- **前缀匹配**：生成以特定字符开头的地址
- **后缀匹配**：生成以特定字符结尾的地址
- **包含匹配**：生成包含特定字符串的地址
- **大小写敏感**：可选的大小写敏感匹配

### 历史记录管理

- 📝 **自动保存**：所有生成的地址自动保存
- 🔍 **搜索过滤**：按地址类型过滤或按内容搜索
- 👁️ **隐私保护**：私钥默认隐藏，点击显示
- 📊 **统计信息**：查看总尝试次数和生成时间
- 🗑️ **记录管理**：删除单条记录或清空所有历史
- 📤 **导出功能**：下载历史记录为 JSON 文件

## 🔧 API 接口

### REST 端点

```http
GET  /                    # API 状态
GET  /address-types       # 支持的地址类型
POST /generate           # 生成单个地址
```

### WebSocket

```http
WS   /ws/generate         # 实时地址生成
```

#### WebSocket 消息格式

```json
{
  "address_type": "P2WPKH",
  "pattern": "abc",
  "position": "start",
  "case_sensitive": false
}
```

## 🛠️ 开发指南

### 添加新的地址类型

1. 在 `btc_generator.py` 中实现生成逻辑
2. 将新类型添加到 `main.py` 的 `/address-types` 端点
3. 更新 `App.vue` 中的前端下拉菜单

### 扩展模式匹配

`check_pattern_match()` 函数可以扩展支持：
- 正则表达式
- 多个模式
- 自定义验证规则
- 高级匹配算法



## 🔒 安全注意事项

### ⚠️ 重要警告

- **仅供教育使用**：切勿将生成的密钥用于真实比特币
- **密码学安全性**：简化实现不适用于生产环境
- **私钥暴露**：密钥显示仅用于学习目的
- **本地存储**：历史记录仅保存在本地，不传输到服务器

### 最佳实践

- 🧹 **定期清理**：在共享设备上定期清空历史记录
- 🔐 **安全导出**：谨慎处理导出的 JSON 文件
- 🚫 **禁止实用**：切勿向生成的地址发送真实比特币
- 🔄 **隐私浏览**：敏感学习时使用无痕/隐私浏览模式

## 🐛 故障排除

### 后端问题

**导入错误**
```bash
# 安装缺失的依赖
pip install -r requirements.txt
```

**端口冲突**
```python
# 在 main.py 中更改端口
uvicorn.run(app, host="0.0.0.0", port=8001)  # 从 8000 更改
```

### 前端问题

**CORS 错误**
- 确保后端在 8000 端口运行
- 检查 `main.py` 中的 CORS 配置

**WebSocket 连接失败**
- 验证后端 WebSocket 端点可访问性
- 检查浏览器控制台的详细错误信息

**Node.js 版本**
- 需要 Node.js 16+ 和 npm
- 使用 `nvm` 更新或从 nodejs.org 下载

## 📋 系统要求

### 后端
- Python 3.8+
- FastAPI 0.104.1+
- uvicorn 0.24.0+
- websockets 12.0+

### 前端
- Node.js 16+
- Vue.js 3.3.8+
- 支持 WebSocket 的现代浏览器

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支
3. 进行修改
4. 如适用，添加测试
5. 提交 Pull Request

## 📄 许可证

本项目仅供教育用途。依赖库的许可证请参见各个库的许可证。

## 🙏 致谢

- Bitcoin Core 开发者提供的密码学标准
- Vue.js 和 FastAPI 社区
- Cursor/Trae/Github copilot
- 教育密码学资源

---

**请记住**：这是一个学习工具。真实的比特币应用程序需要适当的密码学库、安全审计和生产级实现。