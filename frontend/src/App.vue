<template>
  <div class="app">
    <div class="container">
      <header class="header">
        <h1>🪙 比特币地址生成器</h1>
        <p class="subtitle">学习比特币密码学的教育工具</p>
        <div class="warning">
          ⚠️ 仅供教育目的使用，切勿将生成的私钥用于真实的比特币交易！
        </div>
        
        <div class="tabs">
          <button 
            @click="activeTab = 'backend'" 
            :class="['tab-btn', { active: activeTab === 'backend' }]"
          >
            🖥️ 后端生成器
          </button>
          <button 
            @click="activeTab = 'frontend'" 
            :class="['tab-btn', { active: activeTab === 'frontend' }]"
          >
            🌐 浏览器生成器
          </button>
          <button 
            @click="activeTab = 'history'" 
            :class="['tab-btn', { active: activeTab === 'history' }]"
          >
            📜 历史记录
          </button>
        </div>
      </header>

      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 后端生成器 -->
        <div v-if="activeTab === 'backend'" class="generator-form">
        <div class="form-group">
          <label>地址类型：</label>
          <select v-model="selectedAddressType" class="select-input">
            <option v-for="type in addressTypes" :key="type.value" :value="type.value">
              {{ type.label }} - {{ type.description }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>个性化模式 (可选)：</label>
          <input 
            v-model="pattern" 
            type="text" 
            placeholder="例如：abc, 123"
            class="text-input"
            :disabled="isGenerating"
            @input="updateEstimation"
          />
          <small>输入您希望在地址中出现的字符</small>
        </div>

        <div class="form-group" v-if="pattern">
          <label>模式位置：</label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" v-model="patternPosition" value="start" :disabled="isGenerating" @change="updateEstimation" />
              开头
            </label>
            <label class="radio-label">
              <input type="radio" v-model="patternPosition" value="middle" :disabled="isGenerating" @change="updateEstimation" />
              任意位置
            </label>
            <label class="radio-label">
              <input type="radio" v-model="patternPosition" value="end" :disabled="isGenerating" @change="updateEstimation" />
              末尾
            </label>
          </div>
        </div>

        <div v-if="pattern && estimation.attempts > 1" class="estimation-section">
          <h4>📊 预估信息</h4>
          <div class="estimation-info">
            <div class="estimation-item">
              <span class="estimation-label">预估尝试次数：</span>
              <span class="estimation-value">{{ formatNumber(estimation.attempts) }}</span>
            </div>
            <div class="estimation-item">
              <span class="estimation-label">预估时间：</span>
              <span class="estimation-value">{{ estimation.timeRange }}</span>
            </div>
            <div class="estimation-item">
              <span class="estimation-label">难度等级：</span>
              <span class="estimation-value" :class="'difficulty-' + estimation.difficulty">{{ estimation.difficultyText }}</span>
            </div>
          </div>
          <div class="estimation-note">
            <small>⚠️ 预估仅供参考，实际时间可能因硬件性能和运气而有很大差异</small>
          </div>
        </div>

        <div class="button-group">
          <button 
            @click="startGeneration" 
            :disabled="isGenerating" 
            class="btn btn-primary"
          >
            {{ isGenerating ? '生成中...' : '🚀 生成地址' }}
          </button>
          
          <button 
            v-if="isGenerating" 
            @click="pauseResume" 
            class="btn btn-secondary"
          >
            {{ isPaused ? '▶️ 继续' : '⏸️ 暂停' }}
          </button>
          
          <button 
            v-if="isGenerating" 
            @click="stopGeneration" 
            class="btn btn-danger"
          >
            🛑 停止
          </button>
        </div>
      </div>

      <div v-if="isGenerating || result" class="results-section">
        <div v-if="isGenerating" class="progress-section">
          <h3>🔄 生成进度</h3>
          <div class="progress-info">
            <p><strong>状态：</strong> {{ currentStatus }}</p>
            <p><strong>尝试次数：</strong> {{ attempts }}</p>
            <p v-if="currentAddress"><strong>当前地址：</strong> <code>{{ currentAddress }}</code></p>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
          </div>
        </div>

        <div v-if="result" class="result-section">
          <h3>✅ 生成的地址</h3>
          <div class="result-item">
            <label>地址：</label>
            <div class="result-value">
              <code>{{ result.address }}</code>
              <button @click="copyToClipboard(result.address)" class="copy-btn">📋</button>
            </div>
          </div>
          <div class="result-item">
            <label>私钥 (WIF格式)：</label>
            <div class="result-value">
              <code>{{ result.private_key }}</code>
              <button @click="copyToClipboard(result.private_key)" class="copy-btn">📋</button>
            </div>
          </div>
          <div class="result-item">
            <label>总尝试次数：</label>
            <span class="attempts-badge">{{ result.attempts }}</span>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'backend' && error" class="error-section">
        <h3>❌ 错误</h3>
        <p>{{ error }}</p>
      </div>
      
      <!-- 前端生成器 -->
      <div v-if="activeTab === 'frontend'">
        <FrontendGenerator @result-generated="handleFrontendResult" />
      </div>
      
      <!-- 历史记录 -->
      <div v-if="activeTab === 'history'" class="history-section">
        <div class="history-header">
          <h3>📜 生成历史记录</h3>
          <div class="history-controls">
            <button 
              v-if="historyRecords.length > 0" 
              @click="toggleSelectMode" 
              class="btn btn-secondary"
            >
              {{ isSelectMode ? '✅ 退出选择' : '☑️ 批量选择' }}
            </button>
            <button 
              v-if="isSelectMode && historyRecords.length > 0" 
              @click="selectAllRecords" 
              class="btn btn-secondary"
            >
              {{ selectedRecords.size === filteredHistoryRecords.length ? '❌ 取消全选' : '✅ 全选' }}
            </button>
            <button 
              v-if="isSelectMode && selectedRecords.size > 0" 
              @click="deleteSelectedRecords" 
              class="btn btn-danger"
            >
              🗑️ 删除选中 ({{ selectedRecords.size }})
            </button>
            <button 
              v-if="isSelectMode && selectedRecords.size > 0" 
              @click="exportSelectedRecords" 
              class="btn btn-secondary"
            >
              📤 导出选中
            </button>
            <button 
              v-if="!isSelectMode && historyRecords.length > 0" 
              @click="clearHistory" 
              class="btn btn-danger"
            >
              🗑️ 清空历史
            </button>
            <button 
              v-if="!isSelectMode && historyRecords.length > 0" 
              @click="exportHistory" 
              class="btn btn-secondary"
            >
              📤 导出历史
            </button>
            <input 
              ref="importFileInput"
              type="file" 
              accept=".json"
              @change="importHistory"
              style="display: none;"
            />
            <button 
              v-if="!isSelectMode"
              @click="triggerImport" 
              class="btn btn-secondary"
            >
              📥 导入历史
            </button>
          </div>
        </div>
        
        <div v-if="historyRecords.length === 0" class="empty-history">
          <div class="empty-icon">📭</div>
          <h4>暂无历史记录</h4>
          <p>开始生成地址后，历史记录将显示在这里</p>
        </div>
        
        <div v-else class="history-list">
          <div class="history-stats">
            <div class="stat-item">
              <span class="stat-label">总记录数：</span>
              <span class="stat-value">{{ historyRecords.length }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总尝试次数：</span>
              <span class="stat-value">{{ totalAttempts }}</span>
            </div>
          </div>
          
          <div class="history-filters">
            <select v-model="historyFilter" class="filter-select">
              <option value="all">所有类型</option>
              <option value="p2pkh">P2PKH (1开头)</option>
              <option value="p2sh">P2SH (3开头)</option>
              <option value="p2wpkh">P2WPKH (bc1开头)</option>
              <option value="p2tr">P2TR (bc1p开头)</option>
            </select>
            <input 
              v-model="historySearch" 
              type="text" 
              placeholder="搜索地址或私钥..."
              class="search-input"
            />
          </div>
          
          <div class="history-records">
            <div 
              v-for="(record, index) in filteredHistoryRecords" 
              :key="record.id" 
              class="history-record"
            >
              <div class="record-header">
                <div class="record-info">
                  <input 
                    v-if="isSelectMode"
                    type="checkbox"
                    :checked="selectedRecords.has(record.id)"
                    @change="toggleRecordSelection(record.id)"
                    class="record-checkbox"
                  />
                  <span class="record-index">#{{ historyRecords.length - historyRecords.indexOf(record) }}</span>
                  <span class="record-type">{{ getAddressTypeLabel(record.addressType) }}</span>
                  <span class="record-time">{{ formatTime(record.timestamp) }}</span>
                  <span v-if="record.attempts > 1" class="attempts-badge">{{ record.attempts }} 次尝试</span>
                  <span v-if="record.pattern" class="pattern-badge">模式: {{ record.pattern }}</span>
                </div>
                <button 
                  v-if="!isSelectMode"
                  @click="deleteHistoryRecord(record.id)" 
                  class="delete-btn"
                  title="删除此记录"
                >
                  🗑️
                </button>
              </div>
              
              <div class="record-content">
                <div class="record-field">
                  <label>地址：</label>
                  <div class="record-value">
                    <code>{{ record.address }}</code>
                    <button @click="copyToClipboard(record.address)" class="copy-btn">📋</button>
                  </div>
                </div>
                
                <div class="record-field">
                  <label>私钥 (WIF)：</label>
                  <div class="record-value">
                    <code class="private-key" :class="{ 'blurred': !record.showPrivateKey }">{{ record.privateKeyWIF }}</code>
                    <button @click="togglePrivateKeyVisibility(record.id)" class="toggle-btn">
                      {{ record.showPrivateKey ? '🙈' : '👁️' }}
                    </button>
                    <button @click="copyToClipboard(record.privateKeyWIF)" class="copy-btn">📋</button>
                  </div>
                </div>
                
                <div v-if="record.privateKeyHex" class="record-field">
                  <label>私钥 (Hex)：</label>
                  <div class="record-value">
                    <code class="private-key" :class="{ 'blurred': !record.showPrivateKey }">{{ record.privateKeyHex }}</code>
                    <button @click="copyToClipboard(record.privateKeyHex)" class="copy-btn">📋</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import axios from 'axios'
import CryptoJS from 'crypto-js'
import { ec as EC } from 'elliptic'
import bs58 from 'bs58'
import { bech32 } from 'bech32'
import FrontendGenerator from './FrontendGenerator.vue'

export default {
  name: 'App',
  components: {
    FrontendGenerator
  },
  setup() {
    const activeTab = ref('frontend') // 默认显示前端生成器
    const addressTypes = ref([])
    const selectedAddressType = ref('p2pkh')
    const pattern = ref('')
    const patternPosition = ref('start')
    const isGenerating = ref(false)
    const isPaused = ref(false)
    const currentStatus = ref('')
    const attempts = ref(0)
    const currentAddress = ref('')
    const result = ref(null)
    const error = ref('')
    const websocket = ref(null)
    const estimation = ref({
      attempts: 1,
      timeRange: '',
      difficulty: 'easy',
      difficultyText: '简单'
    })

    const API_BASE = 'http://localhost:8000'

    const progressPercentage = ref(0)

    // 处理前端生成器结果
    const handleFrontendResult = (results) => {
      // 将结果添加到历史记录
      if (Array.isArray(results)) {
        results.forEach(result => {
          addToHistory(result)
        })
      } else {
        addToHistory(results)
      }
    }

    // 历史记录相关变量
    const historyRecords = ref([])
    const historyFilter = ref('all')
    const historySearch = ref('')
    const selectedRecords = ref(new Set())
    const isSelectMode = ref(false)

    const ec = new EC('secp256k1')



    // 历史记录计算属性
    const totalAttempts = computed(() => {
      return historyRecords.value.reduce((total, record) => total + (record.attempts || 1), 0)
    })

    const filteredHistoryRecords = computed(() => {
      let filtered = historyRecords.value
      
      // 按类型过滤
      if (historyFilter.value !== 'all') {
        filtered = filtered.filter(record => record.addressType === historyFilter.value)
      }
      
      // 按搜索关键词过滤
      if (historySearch.value.trim()) {
        const searchTerm = historySearch.value.toLowerCase().trim()
        filtered = filtered.filter(record => 
          record.address.toLowerCase().includes(searchTerm) ||
          record.privateKeyWIF.toLowerCase().includes(searchTerm) ||
          (record.privateKeyHex && record.privateKeyHex.toLowerCase().includes(searchTerm))
        )
      }
      
      // 按时间倒序排列（最新的在前）
      return filtered.sort((a, b) => b.timestamp - a.timestamp)
    })

    const loadAddressTypes = async () => {
      try {
        const response = await axios.get(`${API_BASE}/address-types`)
        addressTypes.value = response.data.types
      } catch (err) {
        error.value = '加载地址类型失败'
      }
    }

    const startGeneration = () => {
      if (isGenerating.value) return

      // Reset state
      result.value = null
      error.value = ''
      attempts.value = 0
      currentAddress.value = ''
      isGenerating.value = true
      isPaused.value = false
      currentStatus.value = '连接中...'

      // Create WebSocket connection
      websocket.value = new WebSocket('ws://localhost:8000/ws/generate')

      websocket.value.onopen = () => {
        currentStatus.value = '开始生成...'
        const request = {
          action: 'start',
          address_type: selectedAddressType.value,
          pattern: pattern.value.trim(),
          position: patternPosition.value
        }
        websocket.value.send(JSON.stringify(request))
      }

      websocket.value.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'progress':
            attempts.value = data.attempts
            currentAddress.value = data.current_address
            currentStatus.value = `生成中... (${data.attempts} 次尝试)`
            
            // Update progress bar (logarithmic scale for better UX)
            if (pattern.value) {
              progressPercentage.value = Math.min(90, Math.log10(data.attempts + 1) * 20)
            } else {
              progressPercentage.value = 100
            }
            break
            
          case 'success':
            result.value = {
              address: data.address,
              private_key: data.private_key,
              attempts: data.attempts
            }
            // 保存到历史记录
            saveToHistory(result.value, 'backend')
            isGenerating.value = false
            currentStatus.value = '生成成功！'
            progressPercentage.value = 100
            break
            
          case 'error':
            error.value = data.message
            isGenerating.value = false
            currentStatus.value = '发生错误'
            break
            
          case 'timeout':
            error.value = data.message
            isGenerating.value = false
            currentStatus.value = '超时'
            break
            
          case 'status':
            currentStatus.value = data.message
            break
        }
      }

      websocket.value.onerror = (err) => {
        error.value = 'WebSocket连接错误，请确保后端服务正在运行。'
        isGenerating.value = false
      }

      websocket.value.onclose = () => {
        if (isGenerating.value) {
          isGenerating.value = false
          currentStatus.value = '连接已关闭'
        }
      }
    }

    const pauseResume = () => {
      if (!websocket.value) return

      const action = isPaused.value ? 'resume' : 'pause'
      websocket.value.send(JSON.stringify({ action }))
      isPaused.value = !isPaused.value
    }

    const stopGeneration = () => {
      if (websocket.value) {
        websocket.value.send(JSON.stringify({ action: 'stop' }))
        websocket.value.close()
      }
      isGenerating.value = false
      isPaused.value = false
      currentStatus.value = '用户停止'
    }

    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        // You could add a toast notification here
        console.log('已复制到剪贴板')
      } catch (err) {
        console.error('复制失败:', err)
      }
    }

    const calculateEstimation = (pattern, position, addressType) => {
      if (!pattern || pattern.length === 0) {
        return {
          attempts: 1,
          timeRange: '立即',
          difficulty: 'easy',
          difficultyText: '简单'
        }
      }

      // 计算有效字符集大小（根据地址类型）
      let validChars = 58 // Base58字符集大小
      if (addressType === 'p2wpkh' || addressType === 'p2tr') {
        validChars = 32 // Bech32字符集大小
      }

      // 计算理论尝试次数
      let attempts = Math.pow(validChars, pattern.length)
      
      // 根据位置调整概率
      if (position === 'middle') {
        // 任意位置匹配，概率更高
        const addressLength = addressType === 'p2pkh' ? 34 : 
                             addressType === 'p2sh-p2wpkh' ? 35 :
                             addressType === 'p2wpkh' ? 42 : 62
        const possiblePositions = Math.max(1, addressLength - pattern.length + 1)
        attempts = attempts / possiblePositions
      }

      // 平均需要尝试一半的次数
      attempts = Math.floor(attempts / 2)

      // 估算时间（假设每秒生成1000-5000个地址）
      const minSpeed = 1000 // 每秒最少生成数
      const maxSpeed = 5000 // 每秒最多生成数
      
      const minTime = attempts / maxSpeed
      const maxTime = attempts / minSpeed

      let timeRange = ''
      let difficulty = 'easy'
      let difficultyText = '简单'

      if (attempts < 1000) {
        timeRange = '几秒内'
        difficulty = 'easy'
        difficultyText = '简单'
      } else if (attempts < 100000) {
        const minSeconds = Math.max(1, Math.floor(minTime))
        const maxMinutes = Math.max(1, Math.ceil(maxTime/60))
        timeRange = `${minSeconds}秒 - ${maxMinutes}分钟`
        difficulty = 'medium'
        difficultyText = '中等'
      } else if (attempts < 10000000) {
        const minMinutes = Math.max(1, Math.floor(minTime/60))
        const maxHours = Math.max(1, Math.ceil(maxTime/3600))
        timeRange = `${minMinutes}分钟 - ${maxHours}小时`
        difficulty = 'hard'
        difficultyText = '困难'
      } else {
        const minHours = Math.max(1, Math.floor(minTime/3600))
        const maxDays = Math.max(1, Math.ceil(maxTime/86400))
        timeRange = `${minHours}小时 - ${maxDays}天`
        difficulty = 'extreme'
        difficultyText = '极难'
      }

      return {
        attempts,
        timeRange,
        difficulty,
        difficultyText
      }
    }

    const updateEstimation = () => {
      estimation.value = calculateEstimation(pattern.value, patternPosition.value, selectedAddressType.value)
    }



    const formatNumber = (num) => {
      if (num < 1000) return num.toString()
      if (num < 1000000) return (num / 1000).toFixed(1) + 'K'
      if (num < 1000000000) return (num / 1000000).toFixed(1) + 'M'
      return (num / 1000000000).toFixed(1) + 'B'
    }

    // 前端生成器方法
    const hexToUint8Array = (hex) => {
      const bytes = new Uint8Array(hex.length / 2)
      for (let i = 0; i < hex.length; i += 2) {
        bytes[i / 2] = parseInt(hex.substr(i, 2), 16)
      }
      return bytes
    }

    const generatePrivateKey = () => {
      const randomBytes = new Uint8Array(32)
      crypto.getRandomValues(randomBytes)
      return Array.from(randomBytes).map(b => b.toString(16).padStart(2, '0')).join('')
    }

    const privateKeyToPublicKey = (privateKeyHex) => {
      const keyPair = ec.keyFromPrivate(privateKeyHex, 'hex')
      return keyPair.getPublic('hex')
    }

    const compressPublicKey = (publicKeyHex) => {
      if (publicKeyHex.length === 130) {
        const x = publicKeyHex.slice(2, 66)
        const y = publicKeyHex.slice(66, 130)
        const yBigInt = BigInt('0x' + y)
        const prefix = yBigInt % 2n === 0n ? '02' : '03'
        return prefix + x
      }
      return publicKeyHex
    }

    const sha256 = (data) => {
      if (typeof data === 'string') {
        data = CryptoJS.enc.Hex.parse(data)
      }
      return CryptoJS.SHA256(data).toString()
    }

    const ripemd160 = (data) => {
      if (typeof data === 'string') {
        data = CryptoJS.enc.Hex.parse(data)
      }
      return CryptoJS.RIPEMD160(data).toString()
    }

    const hash160 = (data) => {
      const sha = sha256(data)
      return ripemd160(sha)
    }

    const hash256 = (data) => {
      const first = sha256(data)
      return sha256(first)
    }

    const createP2PKHAddress = (publicKeyHex) => {
      const compressedPubKey = compressPublicKey(publicKeyHex)
      const pubKeyHash = hash160(compressedPubKey)
      const versionedPayload = '00' + pubKeyHash
      const checksum = hash256(versionedPayload).slice(0, 8)
      const fullPayload = versionedPayload + checksum
      return bs58.encode(hexToUint8Array(fullPayload))
    }

    const createP2SHAddress = (publicKeyHex) => {
      const compressedPubKey = compressPublicKey(publicKeyHex)
      const pubKeyHash = hash160(compressedPubKey)
      const redeemScript = '0014' + pubKeyHash
      const scriptHash = hash160(redeemScript)
      const versionedPayload = '05' + scriptHash
      const checksum = hash256(versionedPayload).slice(0, 8)
      const fullPayload = versionedPayload + checksum
      return bs58.encode(hexToUint8Array(fullPayload))
    }

    const createP2WPKHAddress = (publicKeyHex) => {
      const compressedPubKey = compressPublicKey(publicKeyHex)
      const pubKeyHash = hash160(compressedPubKey)
      const words = bech32.toWords(hexToUint8Array(pubKeyHash))
      return bech32.encode('bc', [0, ...words])
    }

    const createP2TRAddress = (publicKeyHex) => {
      const compressedPubKey = compressPublicKey(publicKeyHex)
      const xCoord = compressedPubKey.slice(2)
      const words = bech32.toWords(hexToUint8Array(xCoord))
      return bech32.encode('bc', [1, ...words])
    }

    const privateKeyToWIF = (privateKeyHex) => {
      const versionedKey = '80' + privateKeyHex + '01'
      const checksum = hash256(versionedKey).slice(0, 8)
      const fullKey = versionedKey + checksum
      return bs58.encode(hexToUint8Array(fullKey))
    }

    const generateFrontendAddress = (addressType, privateKeyHex) => {
      const publicKeyHex = privateKeyToPublicKey(privateKeyHex)
      
      let address
      switch (addressType) {
        case 'p2pkh':
          address = createP2PKHAddress(publicKeyHex)
          break
        case 'p2sh':
          address = createP2SHAddress(publicKeyHex)
          break
        case 'p2wpkh':
          address = createP2WPKHAddress(publicKeyHex)
          break
        case 'p2tr':
          address = createP2TRAddress(publicKeyHex)
          break
        default:
          throw new Error('不支持的地址类型')
      }
      
      return {
        address,
        privateKeyHex,
        privateKeyWIF: privateKeyToWIF(privateKeyHex)
      }
    }

    const checkPatternMatch = (address, pattern, position) => {
      if (!pattern) return true
      
      const lowerAddress = address.toLowerCase()
      const lowerPattern = pattern.toLowerCase()
      
      switch (position) {
        case 'start':
          const addressWithoutPrefix = lowerAddress.startsWith('bc1') ? lowerAddress.slice(3) : lowerAddress.slice(1)
          return addressWithoutPrefix.startsWith(lowerPattern)
        case 'end':
          return lowerAddress.endsWith(lowerPattern)
        case 'anywhere':
        default:
          return lowerAddress.includes(lowerPattern)
      }
    }

    // 历史记录方法
    const addToHistory = (addressData) => {
      const record = {
        id: Date.now() + Math.random(), // 简单的唯一ID
        timestamp: Date.now(),
        source: 'frontend',
        addressType: addressData.addressType || 'p2pkh',
        address: addressData.address,
        privateKeyWIF: addressData.privateKeyWIF || addressData.private_key,
        privateKeyHex: addressData.privateKeyHex,
        attempts: addressData.attempts || 1,
        pattern: addressData.pattern || '',
        patternPosition: addressData.patternPosition || 'start',
        showPrivateKey: false // 默认隐藏私钥
      }
      
      historyRecords.value.unshift(record) // 添加到开头
      saveHistoryToLocalStorage()
    }
    
    const saveToHistory = (addressData, source = 'backend') => {
      const record = {
        id: Date.now() + Math.random(),
        timestamp: Date.now(),
        source: source,
        addressType: selectedAddressType.value,
        address: addressData.address,
        privateKeyWIF: addressData.privateKeyWIF || addressData.private_key,
        privateKeyHex: addressData.privateKeyHex,
        attempts: addressData.attempts || 1,
        pattern: pattern.value,
        patternPosition: patternPosition.value,
        showPrivateKey: false
      }
      
      historyRecords.value.unshift(record)
      saveHistoryToLocalStorage()
    }

    const saveHistoryToLocalStorage = () => {
      try {
        localStorage.setItem('btc_address_history', JSON.stringify(historyRecords.value))
      } catch (error) {
        console.error('保存历史记录失败:', error)
      }
    }

    const loadHistoryFromLocalStorage = () => {
      try {
        const saved = localStorage.getItem('btc_address_history')
        if (saved) {
          historyRecords.value = JSON.parse(saved)
        }
      } catch (error) {
        console.error('加载历史记录失败:', error)
        historyRecords.value = []
      }
    }

    const clearHistory = () => {
      console.log('clearHistory method called')
      console.log('Current historyRecords length:', historyRecords.value.length)
      if (confirm('确定要清空所有历史记录吗？此操作不可撤销。')) {
        console.log('User confirmed, clearing history')
        historyRecords.value = []
        saveHistoryToLocalStorage()
        console.log('History cleared, new length:', historyRecords.value.length)
      } else {
        console.log('User cancelled clearing history')
      }
    }

    const deleteHistoryRecord = (recordId) => {
      if (confirm('确定要删除这条记录吗？')) {
        const index = historyRecords.value.findIndex(record => record.id === recordId)
        if (index !== -1) {
          historyRecords.value.splice(index, 1)
          saveHistoryToLocalStorage()
        }
      }
    }

    const toggleSelectMode = () => {
      isSelectMode.value = !isSelectMode.value
      if (!isSelectMode.value) {
        selectedRecords.value.clear()
      }
    }

    const toggleRecordSelection = (recordId) => {
      if (selectedRecords.value.has(recordId)) {
        selectedRecords.value.delete(recordId)
      } else {
        selectedRecords.value.add(recordId)
      }
    }

    const selectAllRecords = () => {
      if (selectedRecords.value.size === filteredHistoryRecords.value.length) {
        // 如果已全选，则取消全选
        selectedRecords.value.clear()
      } else {
        // 选择所有可见记录
        selectedRecords.value.clear()
        filteredHistoryRecords.value.forEach(record => {
          selectedRecords.value.add(record.id)
        })
      }
    }

    const deleteSelectedRecords = () => {
      if (selectedRecords.value.size === 0) {
        alert('请先选择要删除的记录')
        return
      }

      if (confirm(`确定要删除选中的 ${selectedRecords.value.size} 条记录吗？此操作不可撤销。`)) {
        historyRecords.value = historyRecords.value.filter(record => 
          !selectedRecords.value.has(record.id)
        )
        selectedRecords.value.clear()
        saveHistoryToLocalStorage()
        isSelectMode.value = false
      }
    }

    const exportSelectedRecords = () => {
      if (selectedRecords.value.size === 0) {
        alert('请先选择要导出的记录')
        return
      }

      try {
        const selectedData = historyRecords.value.filter(record => 
          selectedRecords.value.has(record.id)
        )
        const dataStr = JSON.stringify(selectedData, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `btc_address_history_selected_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      } catch (error) {
        console.error('导出选中记录失败:', error)
        alert('导出失败，请重试')
      }
    }

    const togglePrivateKeyVisibility = (recordId) => {
      const record = historyRecords.value.find(r => r.id === recordId)
      if (record) {
        record.showPrivateKey = !record.showPrivateKey
      }
    }

    const exportHistory = () => {
      try {
        const dataStr = JSON.stringify(historyRecords.value, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `btc_address_history_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      } catch (error) {
        console.error('导出历史记录失败:', error)
        alert('导出失败，请重试')
      }
    }

    const importFileInput = ref(null)

    const triggerImport = () => {
      importFileInput.value?.click()
    }

    const importHistory = (event) => {
      const file = event.target.files[0]
      if (!file) return

      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const importedData = JSON.parse(e.target.result)
          
          // 验证数据格式
          if (!Array.isArray(importedData)) {
            throw new Error('无效的文件格式：数据应该是数组')
          }

          // 验证每条记录的基本字段
          const validRecords = importedData.filter(record => {
            return record && 
                   typeof record.address === 'string' && 
                   typeof record.privateKeyWIF === 'string' &&
                   typeof record.timestamp === 'number'
          })

          if (validRecords.length === 0) {
            throw new Error('文件中没有有效的历史记录')
          }

          // 询问用户是否要合并还是替换
          const shouldReplace = historyRecords.value.length > 0 ? 
            confirm(`检测到 ${validRecords.length} 条有效记录。\n\n点击"确定"替换当前历史记录\n点击"取消"合并到当前历史记录`) : 
            true

          if (shouldReplace) {
            // 替换当前历史记录
            historyRecords.value = validRecords.map(record => ({
              ...record,
              id: Date.now() + Math.random(), // 重新生成ID避免冲突
              showPrivateKey: false // 重置私钥显示状态
            }))
          } else {
            // 合并到当前历史记录
            const newRecords = validRecords.map(record => ({
              ...record,
              id: Date.now() + Math.random(), // 重新生成ID避免冲突
              showPrivateKey: false // 重置私钥显示状态
            }))
            historyRecords.value = [...newRecords, ...historyRecords.value]
          }

          saveHistoryToLocalStorage()
          alert(`成功导入 ${validRecords.length} 条历史记录！`)
          
        } catch (error) {
          console.error('导入历史记录失败:', error)
          alert(`导入失败：${error.message}`)
        }
      }

      reader.onerror = () => {
        alert('文件读取失败，请重试')
      }

      reader.readAsText(file)
      
      // 清空文件输入，允许重复选择同一文件
      event.target.value = ''
    }

    const getAddressTypeLabel = (type) => {
      const labels = {
        'p2pkh': 'P2PKH (1开头)',
        'p2sh': 'P2SH (3开头)', 
        'p2wpkh': 'P2WPKH (bc1开头)',
        'p2tr': 'P2TR (bc1p开头)',
        'p2sh-p2wpkh': 'P2SH-P2WPKH (3开头)'
      }
      return labels[type] || type
    }

    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      if (diff < 60000) { // 小于1分钟
        return '刚刚'
      } else if (diff < 3600000) { // 小于1小时
        return `${Math.floor(diff / 60000)}分钟前`
      } else if (diff < 86400000) { // 小于1天
        return `${Math.floor(diff / 3600000)}小时前`
      } else if (diff < 604800000) { // 小于1周
        return `${Math.floor(diff / 86400000)}天前`
      } else {
        return date.toLocaleDateString('zh-CN', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      }
    }

    onMounted(() => {
      loadAddressTypes()
      updateEstimation()
      loadHistoryFromLocalStorage()
    })

    onUnmounted(() => {
      if (websocket.value) {
        websocket.value.close()
      }
    })

    // 监听地址类型变化，更新预估信息
    watch(selectedAddressType, () => {
      updateEstimation()
    })



    // 监听标签页切换，清空对应的结果
    watch(activeTab, (newTab) => {
      if (newTab === 'frontend') {
        // 切换到前端生成器时，清空后端生成器的结果
        result.value = null
        error.value = ''
        currentAddress.value = ''
        attempts.value = 0
        currentStatus.value = ''
        progressPercentage.value = 0
        // 如果后端生成正在进行，停止它
        if (isGenerating.value) {
          stopGeneration()
        }
      }
    })

    return {
      activeTab,
      addressTypes,
      selectedAddressType,
      pattern,
      patternPosition,
      isGenerating,
      isPaused,
      currentStatus,
      attempts,
      currentAddress,
      result,
      error,
      progressPercentage,
      estimation,
      startGeneration,
      pauseResume,
      stopGeneration,
      copyToClipboard,
      updateEstimation,
      formatNumber,
      // 前端生成器
      handleFrontendResult,
      // 历史记录
      historyRecords,
      historyFilter,
      historySearch,
      selectedRecords,
      isSelectMode,
      totalAttempts,
      filteredHistoryRecords,
      clearHistory,
      deleteHistoryRecord,
      toggleSelectMode,
      toggleRecordSelection,
      selectAllRecords,
      deleteSelectedRecords,
      exportSelectedRecords,
      togglePrivateKeyVisibility,
      exportHistory,
      importFileInput,
      triggerImport,
      importHistory,
      getAddressTypeLabel,
      formatTime
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  box-shadow: 
    0 32px 64px rgba(0, 0, 0, 0.12),
    0 16px 32px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  padding: 48px;
  max-width: 900px;
  width: 100%;
  height: 900px;
  margin: 0 auto;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.container:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 40px 80px rgba(0, 0, 0, 0.15),
    0 20px 40px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.header {
  text-align: center;
  margin-bottom: 24px;
  position: relative;
  flex-shrink: 0;
}

.header::before {
  content: '';
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  border-radius: 2px;
  animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 0.6; transform: translateX(-50%) scaleX(1); }
  50% { opacity: 1; transform: translateX(-50%) scaleX(1.2); }
}

.header h1 {
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
  animation: textGradient 3s ease-in-out infinite;
}

@keyframes textGradient {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.subtitle {
  color: #64748b;
  font-size: 1.2rem;
  font-weight: 500;
  margin-bottom: 20px;
  opacity: 0.8;
}

.tabs {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.tab-btn {
  padding: 14px 28px;
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 16px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 180px;
  position: relative;
  overflow: hidden;
}

.tab-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.6s;
}

.tab-btn:hover::before {
  left: 100%;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-2px);
  color: #475569;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  color: white;
  box-shadow: 
    0 8px 25px rgba(102, 126, 234, 0.4),
    0 4px 12px rgba(118, 75, 162, 0.3);
  transform: translateY(-1px);
}

.tab-btn.active::before {
  display: none;
}

.warning {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #f59e0b;
  color: #92400e;
  padding: 20px;
  border-radius: 16px;
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.5;
  margin-bottom: 8px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
}

.warning::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #f59e0b, #d97706, #f59e0b);
  background-size: 200% 100%;
  animation: warningShimmer 2s linear infinite;
}

@keyframes warningShimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.main-content::-webkit-scrollbar {
  width: 6px;
}

.main-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.main-content::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

.generator-form {
  margin-bottom: 48px;
}

.form-group {
  margin-bottom: 28px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 12px;
  color: #374151;
  font-size: 1rem;
  letter-spacing: -0.01em;
}

.select-input, .text-input {
  width: 100%;
  padding: 16px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
  min-height: 56px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.select-input {
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23667eea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6,9 12,15 18,9"></polyline></svg>');
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 20px;
  padding-right: 50px;
  cursor: pointer;
}

.select-input:focus, .text-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 
    0 0 0 3px rgba(102, 126, 234, 0.1),
    0 8px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.select-input:hover, .text-input:hover {
  border-color: #9ca3af;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

.text-input:disabled {
  background: rgba(248, 249, 250, 0.8);
  cursor: not-allowed;
  opacity: 0.6;
}

.form-group small {
  display: block;
  color: #666;
  font-size: 0.85rem;
  margin-top: 5px;
}

.radio-group {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: normal;
  cursor: pointer;
}

.radio-label input[type="radio"] {
  margin: 0;
}

.estimation-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 12px;
  padding: 20px;
  margin: 25px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.estimation-section h4 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 1.1rem;
}

.estimation-info {
  display: grid;
  gap: 12px;
  margin-bottom: 15px;
}

.estimation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.estimation-item:last-child {
  border-bottom: none;
}

.estimation-label {
  font-weight: 600;
  color: #495057;
}

.estimation-value {
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 6px;
  background: white;
  border: 1px solid #dee2e6;
}

.difficulty-easy {
  color: #28a745;
  border-color: #28a745;
  background: #d4edda;
}

.difficulty-medium {
  color: #ffc107;
  border-color: #ffc107;
  background: #fff3cd;
}

.difficulty-hard {
  color: #fd7e14;
  border-color: #fd7e14;
  background: #ffeaa7;
}

.difficulty-extreme {
  color: #dc3545;
  border-color: #dc3545;
  background: #f8d7da;
}

.estimation-note {
  padding: 12px;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 6px;
  text-align: center;
  margin-top: 10px;
}

.estimation-note small {
  color: #856404;
  font-style: italic;
}

.button-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 36px;
  padding-top: 24px;
  border-top: 1px solid rgba(229, 231, 235, 0.6);
}

.btn {
  padding: 16px 32px;
  border: none;
  border-radius: 16px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 56px;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s;
}

.btn:hover::before {
  left: 100%;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
  transform: none !important;
}

.btn:disabled::before {
  display: none;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 200% 200%;
  color: white;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  animation: buttonGradient 3s ease infinite;
}

@keyframes buttonGradient {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  box-shadow: 0 8px 25px rgba(107, 114, 128, 0.3);
}

.btn-secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(107, 114, 128, 0.4);
}

.btn-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3);
}

.btn-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(239, 68, 68, 0.4);
}

.results-section {
  background: linear-gradient(135deg, rgba(248, 249, 250, 0.8) 0%, rgba(241, 245, 249, 0.9) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 32px;
  margin: 36px 0 24px 0;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  position: relative;
  overflow: hidden;
}

.results-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #667eea);
  background-size: 300% 100%;
  animation: resultsBorder 4s linear infinite;
}

@keyframes resultsBorder {
  0% { background-position: 0% 0; }
  100% { background-position: 300% 0; }
}

.progress-section h3,
.result-section h3 {
  margin-bottom: 24px;
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-info {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.progress-info p {
  margin-bottom: 12px;
  font-weight: 500;
  color: #374151;
}

.progress-info code {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  padding: 8px 12px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  word-break: break-all;
  font-size: 0.9rem;
  display: inline-block;
  max-width: 100%;
  overflow-wrap: break-word;
  border: 1px solid #d1d5db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: rgba(229, 231, 235, 0.8);
  border-radius: 8px;
  overflow: hidden;
  margin-top: 20px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
}

.progress-bar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: progressShimmer 2s ease-in-out infinite;
}

@keyframes progressShimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 200% 100%;
  border-radius: 8px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  animation: progressGradient 3s ease infinite;
}

@keyframes progressGradient {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.result-item {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  padding: 24px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.result-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.12);
  border-color: rgba(102, 126, 234, 0.3);
}

.result-item label {
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  display: block;
  font-size: 0.95rem;
  letter-spacing: -0.01em;
}

.result-value {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(248, 249, 250, 0.8);
  border-radius: 12px;
  padding: 4px;
  border: 1px solid rgba(229, 231, 235, 0.6);
}

.result-value code {
  background: transparent;
  padding: 12px 16px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  word-break: break-all;
  flex: 1;
  font-size: 0.9rem;
  color: #1f2937;
  font-weight: 500;
}

.copy-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 60px;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.copy-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.copy-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.attempts-badge {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(229, 231, 235, 0.6);
}

.result-index {
  font-weight: 700;
  color: #667eea;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-field {
  margin-bottom: 16px;
}

.result-field:last-child {
  margin-bottom: 0;
}

.results-container {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.results-container::-webkit-scrollbar {
  width: 8px;
}

.results-container::-webkit-scrollbar-track {
  background: rgba(229, 231, 235, 0.3);
  border-radius: 4px;
}

.results-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

.results-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
}

.error-section {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 20px;
  border-radius: 8px;
}

.error-section h3 {
  margin-bottom: 10px;
}

@media (max-width: 1024px) {
  .container {
    max-width: 95%;
    padding: 30px;
  }
  
  .estimation-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .result-value {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 20px;
    margin: 10px;
  }
  
  .header {
    margin-bottom: 30px;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .generator-form {
    margin-bottom: 30px;
  }
  
  .form-group {
    margin-bottom: 18px;
  }
  
  .radio-group {
    flex-direction: column;
    gap: 12px;
  }
  
  .estimation-section {
    margin: 20px 0;
    padding: 15px;
  }
  
  .estimation-info {
    gap: 8px;
  }
  
  .estimation-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .button-group {
    flex-direction: column;
    margin-top: 25px;
    padding-top: 15px;
  }
  
  .btn {
    justify-content: center;
    width: 100%;
  }
  
  .results-section {
    margin: 25px 0 15px 0;
    padding: 20px;
  }
  
  .result-value {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .copy-btn {
    align-self: flex-end;
    width: auto;
  }
}

/* 历史记录样式 */
.history-section {
  margin-top: 32px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.history-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
}

.history-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.empty-history {
  text-align: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-history h4 {
  margin: 0 0 8px 0;
  color: #374151;
  font-size: 1.25rem;
}

.empty-history p {
  margin: 0;
  color: #6b7280;
  font-size: 0.95rem;
}

.history-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-item {
  background: rgba(255, 255, 255, 0.8);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.stat-label {
  font-weight: 500;
  color: #6b7280;
  margin-right: 8px;
}

.stat-value {
  font-weight: 700;
  color: #1f2937;
  font-size: 1.1rem;
}

.history-filters {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-select {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
  font-weight: 500;
  color: #374151;
  transition: all 0.3s ease;
  min-width: 160px;
}

.filter-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.history-records {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-record {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.history-record:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.record-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.record-index {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.record-type {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.record-time {
  color: #6b7280;
  font-size: 0.85rem;
  font-weight: 500;
}

.pattern-badge {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.delete-btn {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  border: none;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  transform: scale(1.05);
}

.record-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-field label {
  font-weight: 600;
  color: #374151;
  font-size: 0.9rem;
}

.record-value {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.record-value code {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  padding: 8px 12px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  word-break: break-all;
  font-size: 0.85rem;
  border: 1px solid #d1d5db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex: 1;
  min-width: 0;
}

.private-key.blurred {
  filter: blur(4px);
  transition: filter 0.3s ease;
}

.toggle-btn {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  background: rgba(102, 126, 234, 0.2);
  transform: scale(1.05);
}

.record-checkbox {
  width: 18px;
  height: 18px;
  margin-right: 12px;
  cursor: pointer;
  accent-color: #667eea;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.record-checkbox:hover {
  transform: scale(1.1);
}

.record-checkbox:checked {
  background: #667eea;
  border-color: #667eea;
}

@media (max-width: 768px) {
  .history-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .history-controls {
    justify-content: center;
  }
  
  .history-filters {
    flex-direction: column;
  }
  
  .history-stats {
    flex-direction: column;
  }
  
  .record-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .record-info {
    justify-content: center;
  }
  
  .record-value {
    flex-direction: column;
    align-items: stretch;
  }
  
  .record-value code {
    margin-bottom: 8px;
  }
}
</style>