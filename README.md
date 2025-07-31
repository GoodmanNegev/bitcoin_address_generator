# 比特币地址生成器（教育用途）

这是一个用于学习比特币地址生成和密码学概念的教育项目。

## 功能特性
- ✅ 支持传统地址 (P2PKH)、嵌套隔离见证 (P2SH-P2WPKH)、原生隔离见证 (P2WPKH) 和 Taproot (P2TR) 地址类型
- ✅ 个性化字符串匹配（开头、中间、结尾位置）
- ✅ 基于 WebSocket 的实时生成可视化
- ✅ 暂停/恢复功能
- ✅ 复制到剪贴板功能
- ✅ 响应式网页界面

## 快速开始

### 方式一：使用 Python 3 运行（无额外依赖）
应用程序包含一个仅使用 Python 3 标准库的简化版本：

```bash
# 1. 启动后端
cd backend
pip install -r requirements.txt
python3 main.py

# 2. 打开另一个终端并启动前端（需要 Node.js）
cd frontend
npm install  # 仅首次需要
npm run dev

# 3. 在浏览器中打开 http://localhost:5173
```

### 方式二：完整版本（包含所有依赖）
如果您有 pip 可用，可以安装完整依赖以获得更准确的比特币地址生成：

```bash
# 安装后端依赖
cd backend
python3 -m pip install fastapi uvicorn websockets ecdsa base58 bech32

# 然后按上述方式运行
python3 main.py
```

## 项目结构
```
btc-address-generator/
├── backend/                    # FastAPI 后端
│   ├── main.py                # FastAPI 应用程序
│   ├── btc_generator.py       # 完整的比特币地址生成器
│   ├── btc_generator_simple.py # 简化版本（仅标准库）
│   ├── test.py               # 测试脚本
│   └── requirements.txt      # Python 依赖
├── frontend/                  # Vue.js 前端
│   ├── src/
│   │   ├── App.vue          # 主要 Vue 组件
│   │   └── main.js          # 入口点
│   ├── package.json         # Node.js 依赖
│   ├── vite.config.js       # Vite 配置
│   └── index.html           # HTML 模板
└── README.md                 # 本文件
```

## 工作原理

### 后端 (FastAPI + Python)
- 使用密码学安全的随机数生成私钥
- 使用适当的密码学函数实现所有 4 种比特币地址类型
- 提供 REST API 和 WebSocket 端点进行实时通信
- 支持可配置位置的模式匹配

### 前端 (Vue.js)
- 具有实时更新的现代响应式界面
- WebSocket 连接用于实时生成进度
- 长时间搜索的暂停/恢复功能
- 生成的地址和私钥的复制到剪贴板功能

## 支持的地址类型

1. **传统地址 (P2PKH)** - 以 '1' 开头的传统地址
2. **嵌套隔离见证 (P2SH-P2WPKH)** - 包装在 P2SH 中的隔离见证，以 '3' 开头
3. **原生隔离见证 (P2WPKH)** - 以 'bc1q' 开头的原生隔离见证地址
4. **Taproot (P2TR)** - 以 'bc1p' 开头的最新地址类型

## API 端点

- `GET /` - API 状态
- `GET /address-types` - 获取支持的地址类型
- `POST /generate` - 生成单个地址
- `WebSocket /ws/generate` - 带模式匹配的实时地址生成

## 测试
```bash
cd backend
python3 test.py
```

## 安全说明

**⚠️ 重要提示：这仅用于教育目的！**

- 切勿将生成的私钥用于真实的比特币交易
- 简化版本使用的教育实现在密码学上不安全
- 真实的比特币应用程序需要适当的密码学库和安全实践
- 私钥在界面中显示仅用于学习目的

## 开发

### 添加新的地址类型
1. 在 `btc_generator.py` 中实现地址生成逻辑
2. 将新类型添加到 `main.py` 中的 `address_types` 端点
3. 更新 `App.vue` 中的前端下拉菜单

### 扩展模式匹配
`check_pattern_match()` 中的模式匹配逻辑可以扩展以支持：
- 正则表达式
- 多个模式
- 大小写敏感选项
- 自定义验证规则

## 故障排除

### 后端问题
- **导入错误**：如果密码学库不可用，应用程序会自动回退到简化版本
- **端口冲突**：后端默认运行在 8000 端口，如需要可在 `main.py` 中更改

### 前端问题
- **CORS 错误**：确保后端正在运行且 CORS 配置正确
- **WebSocket 连接**：检查后端 WebSocket 端点是否可访问
- **Node.js**：前端需要 Node.js 16+ 和 npm

## 许可证
仅用于教育目的。依赖项的许可证请参见各个库的许可证。