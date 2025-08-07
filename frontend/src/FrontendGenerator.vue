<template>
  <div class="generator-form">
    <div class="form-group">
          <label>地址类型：</label>
          <select v-model="selectedAddressType" class="select-input">
            <option value="p2pkh">P2PKH - 传统地址 (1开头)</option>
            <option value="p2sh">P2SH - 脚本地址 (3开头)</option>
            <option value="p2wpkh">P2WPKH - 原生隔离见证 (bc1开头)</option>
            <option value="p2tr">P2TR - Taproot地址 (bc1p开头)</option>
          </select>
    </div>

    <div class="form-group">
      <label>并发生成器数量：</label>
      <input 
        v-model.number="concurrentGenerators" 
        type="number" 
        min="1" 
        max="16"
        class="text-input"
        :disabled="isGenerating"
      />
      <small>推荐设置为CPU核心数的2倍，最多16个</small>
    </div>

    <div class="form-group">
      <label>性能模式：</label>
      <select v-model="performanceMode" class="select-input" :disabled="isGenerating">
        <option value="balanced">平衡模式 - 推荐</option>
        <option value="speed">极速模式 - 最大性能</option>
        <option value="memory">节能模式 - 低内存占用</option>
      </select>
      <small>{{ getPerformanceModeDescription() }}</small>
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
          <input type="radio" v-model="patternPosition" value="anywhere" :disabled="isGenerating" @change="updateEstimation" />
          任意位置
        </label>
        <label class="radio-label">
          <input type="radio" v-model="patternPosition" value="end" :disabled="isGenerating" @change="updateEstimation" />
          末尾
        </label>
      </div>
    </div>

    <div v-if="pattern && autoEstimation.attempts > 1" class="estimation-section">
      <h4>📊 预估信息</h4>
      <div class="estimation-info">
        <div class="estimation-item">
          <span class="estimation-label">预估尝试次数：</span>
          <span class="estimation-value">{{ formatNumber(autoEstimation.attempts) }}</span>
        </div>
        <div class="estimation-item">
          <span class="estimation-label">预估时间：</span>
          <span class="estimation-value">{{ autoEstimation.timeRange }}</span>
        </div>
        <div class="estimation-item">
          <span class="estimation-label">难度等级：</span>
          <span class="estimation-value" :class="'difficulty-' + autoEstimation.difficulty">{{ autoEstimation.difficultyText }}</span>
        </div>
      </div>
      <div class="estimation-note">
        <small>⚠️ 预估仅供参考，实际时间可能因硬件性能和运气而有很大差异</small>
      </div>
    </div>

    <div class="button-group">
      <button 
        @click="generateAddresses" 
        :disabled="isGenerating" 
        class="btn btn-primary"
      >
        {{ isGenerating ? '生成中...' : '🚀 生成地址' }}
      </button>
      
      <button 
        v-if="isGenerating" 
        @click="stopGeneration" 
        class="btn btn-danger"
      >
        🛑 停止
      </button>

      <button 
        v-if="results.length > 0" 
        @click="clearResults" 
        class="btn btn-secondary"
      >
        🗑️ 清空结果
      </button>
      

    </div>
  </div>

  <div v-if="isGenerating || generatorStates.length > 0" class="progress-section">
    <h3>🔄 并发生成进度</h3>
    <div class="overall-progress">
      <div class="progress-info">
        <p><strong>总体状态：</strong> {{ currentStatus }}</p>
        <p><strong>总计已生成：</strong> {{ totalGenerated }} / {{ totalTarget }}</p>
        <p v-if="pattern"><strong>总尝试次数：</strong> {{ totalAttempts }}</p>
        <p><strong>活跃生成器：</strong> {{ generatorStates.length }} 个</p>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: overallProgressPercentage + '%' }"></div>
      </div>
    </div>
    
    <div class="generators-grid" v-if="generatorStates.length > 0">
          <div 
            v-for="(generator, index) in generatorStates" 
            :key="'gen-' + index" 
            class="generator-box"
            :class="{ 'completed': generator.completed, 'active': generator.active }"
          >
            <div class="generator-header">
              <h4>生成器 #{{ index + 1 }}</h4>
              <span class="generator-status" :class="generator.status">{{ getStatusText(generator.status) }}</span>
            </div>
            
            <div class="generator-stats">
              <div class="stat-item">
                <span class="stat-label">已生成:</span>
                <span class="stat-value">{{ generator.generated }} / {{ generator.target }}</span>
              </div>
              <div class="stat-item" v-if="pattern">
                <span class="stat-label">尝试次数:</span>
                <span class="stat-value">{{ generator.attempts }}</span>
              </div>
              <div class="stat-item" v-if="generator.currentAddress">
                <span class="stat-label">当前地址:</span>
                <span class="stat-value address-preview">{{ generator.currentAddress.slice(0, 10) }}...</span>
              </div>
            </div>
            
            <div class="generator-progress">
              <div class="progress-bar small">
                <div class="progress-fill" :style="{ width: generator.progressPercentage + '%' }"></div>
              </div>
              <span class="progress-text">{{ generator.progressPercentage.toFixed(1) }}%</span>
            </div>
            
            <div v-if="generator.results.length > 0" class="generator-results">
              <div class="result-count">找到 {{ generator.results.length }} 个地址</div>
              <div class="latest-result" v-if="generator.results[generator.results.length - 1]">
                <small>最新: {{ generator.results[generator.results.length - 1].address.slice(0, 15) }}...</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="results.length > 0" class="results-section">
        <h3>✅ 生成的地址 ({{ results.length }})</h3>
        <div class="results-container">
          <div v-for="(result, index) in results" :key="index" class="result-item">
            <div class="result-header">
              <span class="result-index">#{{ index + 1 }}</span>
              <span v-if="result.attempts > 1" class="attempts-badge">{{ result.attempts }} 次尝试</span>
            </div>
            <div class="result-field">
              <label>地址：</label>
              <div class="result-value">
                <code>{{ result.address }}</code>
                <button @click="copyToClipboard(result.address)" class="copy-btn">📋</button>
              </div>
            </div>
            <div class="result-field">
              <label>私钥 (WIF)：</label>
              <div class="result-value">
                <code>{{ result.privateKeyWIF }}</code>
                <button @click="copyToClipboard(result.privateKeyWIF)" class="copy-btn">📋</button>
              </div>
            </div>
            <div class="result-field">
              <label>私钥 (Hex)：</label>
              <div class="result-value">
                <code>{{ result.privateKeyHex }}</code>
                <button @click="copyToClipboard(result.privateKeyHex)" class="copy-btn">📋</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-section">
        <h3>❌ 错误</h3>
        <p>{{ error }}</p>
      </div>
</template>


<script>
import { ref, computed, watch, onMounted } from 'vue'
import CryptoJS from 'crypto-js'
import { ec as EC } from 'elliptic'
import bs58 from 'bs58'
import { bech32 } from 'bech32'

export default {
  name: 'FrontendGenerator',
  emits: ['result-generated'],
  setup(props, { emit }) {
    const selectedAddressType = ref('p2pkh')
    const concurrentGenerators = ref(navigator.hardwareConcurrency || 4)
    const performanceMode = ref('balanced')
    const addressesPerGenerator = 1  // 固定值，不可配置
    const pattern = ref('')
    const patternPosition = ref('start')
    const isGenerating = ref(false)
    const currentStatus = ref('')
    const attempts = ref(0)
    const currentAddress = ref('')
    const results = ref([])
    const error = ref('')
    const targetCount = ref(0)
    const stopRequested = ref(false)
    const isEstimating = ref(false)
    const estimationResult = ref(null)
    const autoEstimation = ref({
      attempts: 1,
      timeRange: '',
      difficulty: 'easy',
      difficultyText: '简单'
    })
    
    // 新增：并发生成器状态管理
    const generatorStates = ref([])
    const activeWorkers = ref([])
    
    // 性能模式配置
    const getPerformanceConfig = () => {
      switch (performanceMode.value) {
        case 'speed':
          return {
            batchSize: 200,
            progressInterval: 5000,
            maxAttempts: 5000000,
            workerDelay: 0
          }
        case 'memory':
          return {
            batchSize: 50,
            progressInterval: 1000,
            maxAttempts: 1000000,
            workerDelay: 10
          }
        default: // balanced
          return {
            batchSize: 100,
            progressInterval: 2000,
            maxAttempts: 2000000,
            workerDelay: 0
          }
      }
    }
    
    // 获取性能模式描述
    const getPerformanceModeDescription = () => {
      switch (performanceMode.value) {
        case 'speed':
          return '最大化生成速度，占用更多CPU和内存'
        case 'memory':
          return '降低资源占用，适合低配置设备'
        default:
          return '平衡性能和资源占用，适合大多数情况'
      }
    }


    const ec = new EC('secp256k1')

    const progressPercentage = computed(() => {
      if (targetCount.value === 0) return 0
      return Math.min(100, (results.value.length / targetCount.value) * 100)
    })
    
    // 新增：计算总体进度
    const totalGenerated = computed(() => {
      return generatorStates.value.reduce((sum, gen) => sum + gen.generated, 0)
    })
    
    const totalTarget = computed(() => {
      return concurrentGenerators.value * addressesPerGenerator
    })
    
    const totalAttempts = computed(() => {
      return generatorStates.value.reduce((sum, gen) => sum + gen.attempts, 0)
    })
    
    const overallProgressPercentage = computed(() => {
      if (totalTarget.value === 0) return 0
      return Math.min(100, (totalGenerated.value / totalTarget.value) * 100)
    })
    
    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'waiting': '等待中',
        'running': '生成中',
        'completed': '已完成',
        'error': '错误',
        'stopped': '已停止'
      }
      return statusMap[status] || '未知'
    }
    
    // 初始化生成器状态
    const initializeGenerators = () => {
      generatorStates.value = []
      for (let i = 0; i < concurrentGenerators.value; i++) {
        generatorStates.value.push({
          id: i,
          status: 'waiting',
          generated: 0,
          target: addressesPerGenerator,
          attempts: 0,
          currentAddress: '',
          results: [],
          progressPercentage: 0,
          active: false,
          completed: false,
          worker: null
        })
      }
    }

    // 辅助函数：将十六进制字符串转换为Uint8Array（替代Buffer.from）
    const hexToUint8Array = (hex) => {
      const bytes = new Uint8Array(hex.length / 2)
      for (let i = 0; i < hex.length; i += 2) {
        bytes[i / 2] = parseInt(hex.substr(i, 2), 16)
      }
      return bytes
    }

    // 生成随机私钥
    const generatePrivateKey = () => {
      const randomBytes = new Uint8Array(32)
      crypto.getRandomValues(randomBytes)
      return Array.from(randomBytes).map(b => b.toString(16).padStart(2, '0')).join('')
    }

    // 私钥转公钥
    const privateKeyToPublicKey = (privateKeyHex) => {
      const keyPair = ec.keyFromPrivate(privateKeyHex, 'hex')
      return keyPair.getPublic('hex')
    }

    // 压缩公钥
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

    // SHA256哈希
    const sha256 = (data) => {
      if (typeof data === 'string') {
        data = CryptoJS.enc.Hex.parse(data)
      }
      return CryptoJS.SHA256(data).toString()
    }

    // RIPEMD160哈希
    const ripemd160 = (data) => {
      if (typeof data === 'string') {
        data = CryptoJS.enc.Hex.parse(data)
      }
      return CryptoJS.RIPEMD160(data).toString()
    }

    // Hash160 (SHA256 + RIPEMD160)
    const hash160 = (data) => {
      const sha = sha256(data)
      return ripemd160(sha)
    }

    // 双重SHA256
    const hash256 = (data) => {
      const first = sha256(data)
      return sha256(first)
    }

    // 创建P2PKH地址
    const createP2PKHAddress = (publicKeyHex) => {
      const compressedPubKey = compressPublicKey(publicKeyHex)
      const pubKeyHash = hash160(compressedPubKey)
      const versionedPayload = '00' + pubKeyHash
      const checksum = hash256(versionedPayload).slice(0, 8)
      const fullPayload = versionedPayload + checksum
      return bs58.encode(hexToUint8Array(fullPayload))
    }

    // 创建P2SH地址
    const createP2SHAddress = (publicKeyHex) => {
      const compressedPubKey = compressPublicKey(publicKeyHex)
      const pubKeyHash = hash160(compressedPubKey)
      // P2WPKH脚本: OP_0 + 20字节pubKeyHash
      const redeemScript = '0014' + pubKeyHash
      const scriptHash = hash160(redeemScript)
      const versionedPayload = '05' + scriptHash
      const checksum = hash256(versionedPayload).slice(0, 8)
      const fullPayload = versionedPayload + checksum
      return bs58.encode(hexToUint8Array(fullPayload))
    }

    // 创建P2WPKH地址
    const createP2WPKHAddress = (publicKeyHex) => {
      const compressedPubKey = compressPublicKey(publicKeyHex)
      const pubKeyHash = hash160(compressedPubKey)
      const words = bech32.toWords(hexToUint8Array(pubKeyHash))
      return bech32.encode('bc', [0, ...words])
    }

    // 创建P2TR地址 (Taproot)
    const createP2TRAddress = (publicKeyHex) => {
      const compressedPubKey = compressPublicKey(publicKeyHex)
      // 提取x坐标（去掉前缀字节）
      const xCoord = compressedPubKey.slice(2)
      const words = bech32.toWords(hexToUint8Array(xCoord))
      return bech32.encode('bc', [1, ...words])
    }

    // 私钥转WIF格式
    const privateKeyToWIF = (privateKeyHex) => {
      const versionedKey = '80' + privateKeyHex + '01' // 0x80前缀 + 私钥 + 0x01后缀(压缩)
      const checksum = hash256(versionedKey).slice(0, 8)
      const fullKey = versionedKey + checksum
      return bs58.encode(hexToUint8Array(fullKey))
    }

    // 生成地址
    const generateAddress = (addressType, privateKeyHex) => {
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

    // 检查模式匹配
    const checkPatternMatch = (address, pattern, position) => {
      if (!pattern) return true
      
      const lowerAddress = address.toLowerCase()
      const lowerPattern = pattern.toLowerCase()
      
      switch (position) {
        case 'start':
          // 跳过地址前缀检查
          const addressWithoutPrefix = lowerAddress.startsWith('bc1') ? lowerAddress.slice(3) : lowerAddress.slice(1)
          return addressWithoutPrefix.startsWith(lowerPattern)
        case 'end':
          return lowerAddress.endsWith(lowerPattern)
        case 'anywhere':
        default:
          return lowerAddress.includes(lowerPattern)
      }
    }

    // 并行生成地址
    const generateAddresses = async () => {
      if (isGenerating.value) return
      
      error.value = ''
      results.value = []
      attempts.value = 0
      isGenerating.value = true
      stopRequested.value = false
      targetCount.value = totalTarget.value
      currentStatus.value = '初始化并发生成器...'
      
      // 初始化生成器状态
      initializeGenerators()
      
      try {
        currentStatus.value = `启动 ${concurrentGenerators.value} 个并发生成器...`
        
        if (pattern.value) {
          // 有模式匹配时使用并行搜索
          await generateWithPatternConcurrent()
        } else {
          // 无模式时直接并行生成
          await generateBatchConcurrent()
        }
        
        if (!stopRequested.value) {
          currentStatus.value = '所有生成器完成！'
        } else {
          currentStatus.value = '用户停止'
        }
      } catch (err) {
        error.value = err.message
        currentStatus.value = '发生错误'
      } finally {
        isGenerating.value = false
        // 清理所有workers
        cleanupAllWorkers()
      }
    }

    // 并发批量生成（无模式匹配）
    const generateBatchConcurrent = async () => {
      const promises = []
      
      for (let i = 0; i < concurrentGenerators.value; i++) {
        promises.push(startGenerator(i, false))
      }
      
      await Promise.all(promises)
    }
    
    // 启动单个生成器
    const startGenerator = async (generatorId, hasPattern) => {
      const generator = generatorStates.value[generatorId]
      generator.status = 'running'
      generator.active = true
      
      return new Promise((resolve, reject) => {
        let worker;
        
        // 使用本地独立Worker
        worker = new Worker('/src/CryptoWorker.js', { type: 'module' });
        
        generator.worker = worker
        activeWorkers.value.push(worker)
        
        const cleanup = () => {
          try {
            worker.terminate()
            const index = activeWorkers.value.indexOf(worker)
            if (index > -1) activeWorkers.value.splice(index, 1)
          } catch (e) {
            console.warn('清理worker时出错:', e)
          }
        }
        
        worker.onmessage = (e) => {
          const { type, data } = e.data
          
          if (type === 'batch_result') {
            // 批量生成完成
            const enrichedData = data.map(result => ({
              ...result,
              addressType: selectedAddressType.value,
              pattern: pattern.value || '',
              patternPosition: patternPosition.value,
              attempts: 1 // 批量生成时每个地址尝试次数为1
            }))
            
            generator.results.push(...enrichedData)
            generator.generated = generator.results.length
            generator.attempts = generator.generated  // 批量生成时，尝试次数等于生成数量
            generator.progressPercentage = (generator.generated / generator.target) * 100
            generator.status = 'completed'
            generator.completed = true
            generator.active = false
            
            // 添加到总结果
            results.value.push(...enrichedData)
            
            // 保存到后端数据库
            enrichedData.forEach(result => {
              saveToBackend(result)
            })
            
            // 发射结果给父组件（历史记录）
            enrichedData.forEach(result => {
              emit('result-generated', result)
            })
            
            cleanup()
            resolve()
          } else if (type === 'result') {
            // 模式匹配找到结果
            const resultData = {
              ...data,
              addressType: selectedAddressType.value,
              pattern: pattern.value,
              patternPosition: patternPosition.value
            }
            
            generator.results.push(resultData)
            generator.generated = generator.results.length
            generator.attempts = data.attempts  // data.attempts是累计值，直接赋值
            generator.currentAddress = data.address
            generator.progressPercentage = (generator.generated / generator.target) * 100
            
            // 添加到总结果
            results.value.push(resultData)
            
            // 保存到后端数据库
            saveToBackend(resultData)
            
            // 发射结果给父组件（历史记录）
            emit('result-generated', resultData)
            
            if (generator.generated >= generator.target) {
              generator.status = 'completed'
              generator.completed = true
              generator.active = false
              cleanup()
              resolve()
            }
          } else if (type === 'progress') {
            // 进度更新 - data.attempts是累计值，直接赋值而不是累加
            generator.attempts = data.attempts
            generator.currentAddress = data.currentAddress
          } else if (type === 'error') {
            generator.status = 'error'
            generator.active = false
            cleanup()
            reject(new Error(data.message))
          }
        }
        
        worker.onerror = (error) => {
          generator.status = 'error'
          generator.active = false
          cleanup()
          reject(error)
        }
        
        // 启动worker - 使用性能配置
        const perfConfig = getPerformanceConfig()
        
        if (hasPattern) {
          worker.postMessage({
            addressType: selectedAddressType.value,
            pattern: pattern.value,
            patternPosition: patternPosition.value,
            workerId: generatorId,
            targetCount: generator.target,
            performanceConfig: perfConfig
          })
        } else {
          worker.postMessage({
            type: 'batch',
            addressType: selectedAddressType.value,
            count: generator.target,
            workerId: generatorId,
            performanceConfig: perfConfig
          })
        }
        
        // 根据性能模式添加延迟
        if (perfConfig.workerDelay > 0) {
          setTimeout(() => {}, perfConfig.workerDelay)
        }
      })
    }

    // 并发模式匹配生成
    const generateWithPatternConcurrent = async () => {
      const promises = []
      
      for (let i = 0; i < concurrentGenerators.value; i++) {
        promises.push(startGenerator(i, true))
      }
      
      await Promise.all(promises)
    }
    
    // 清理所有workers
    const cleanupAllWorkers = () => {
      activeWorkers.value.forEach(worker => {
        try {
          worker.terminate()
        } catch (e) {
          console.warn('清理worker时出错:', e)
        }
      })
      activeWorkers.value = []
      
      // 重置生成器状态
      generatorStates.value.forEach(generator => {
        if (generator.status === 'running') {
          generator.status = 'stopped'
          generator.active = false
        }
      })
    }





    const stopGeneration = () => {
      stopRequested.value = true
      
      // 清理所有workers
      cleanupAllWorkers()
      
      isGenerating.value = false
      currentStatus.value = '已停止'
    }

    const clearResults = () => {
      results.value = []
      attempts.value = 0
      currentAddress.value = ''
      error.value = ''
      generatorStates.value = []
    }
    


    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        console.log('已复制到剪贴板')
      } catch (err) {
        console.error('复制失败:', err)
      }
    }

    // 预估生成时间
    const estimateTime = async () => {
      if (!pattern.value || isEstimating.value) return
      
      isEstimating.value = true
      estimationResult.value = null
      
      try {
        // 计算模式难度
        const patternLength = pattern.value.length
        let baseChars = 58 // Base58字符集大小
        
        // 根据地址类型调整字符集
        if (selectedAddressType.value === 'p2wpkh' || selectedAddressType.value === 'p2tr') {
          baseChars = 32 // Bech32字符集大小
        }
        
        // 计算理论概率
        let probability
        switch (patternPosition.value) {
          case 'start':
            probability = 1 / Math.pow(baseChars, patternLength)
            break
          case 'end':
            probability = 1 / Math.pow(baseChars, patternLength)
            break
          case 'anywhere':
          default:
            // 对于"任意位置"，概率会更高，因为有多个位置可以匹配
            const addressLength = selectedAddressType.value.startsWith('p2') ? 34 : 42
            const possiblePositions = Math.max(1, addressLength - patternLength + 1)
            probability = possiblePositions / Math.pow(baseChars, patternLength)
            break
        }
        
        // 预计尝试次数
        const expectedAttempts = Math.ceil(1 / probability)
        
        // 预估设备性能（每秒生成地址数）
        const performanceTest = await measurePerformance()
        const addressesPerSecond = performanceTest.rate
        
        // 计算预估时间
        const estimatedSeconds = expectedAttempts / addressesPerSecond
        const estimatedTime = formatTime(estimatedSeconds)
        
        // 计算难度等级
        const difficultyLevel = getDifficultyLevel(expectedAttempts)
        const difficultyPercentage = Math.min(100, Math.log10(expectedAttempts) * 10)
        
        // 计算成功概率（在合理时间内）
        const successProbability = getSuccessProbability(probability)
        
        estimationResult.value = {
          difficulty: difficultyLevel,
          expectedAttempts,
          estimatedTime,
          successProbability,
          difficultyPercentage
        }
      } catch (err) {
        error.value = '预估计算失败: ' + err.message
      } finally {
        isEstimating.value = false
      }
    }
    
    // 测量设备性能
    const measurePerformance = async () => {
      const startTime = performance.now()
      const testCount = 100
      
      for (let i = 0; i < testCount; i++) {
        const privateKeyHex = generatePrivateKey()
        generateAddress(selectedAddressType.value, privateKeyHex)
      }
      
      const endTime = performance.now()
      const duration = (endTime - startTime) / 1000 // 转换为秒
      const rate = testCount / duration
      
      return { rate, duration }
    }
    
    // 格式化时间显示
    const formatTime = (seconds) => {
      if (seconds < 1) {
        return '< 1秒'
      } else if (seconds < 60) {
        return `${Math.ceil(seconds)}秒`
      } else if (seconds < 3600) {
        const minutes = Math.ceil(seconds / 60)
        return `${minutes}分钟`
      } else if (seconds < 86400) {
        const hours = Math.ceil(seconds / 3600)
        return `${hours}小时`
      } else if (seconds < 2592000) {
        const days = Math.ceil(seconds / 86400)
        return `${days}天`
      } else if (seconds < 31536000) {
        const months = Math.ceil(seconds / 2592000)
        return `${months}个月`
      } else {
        const years = Math.ceil(seconds / 31536000)
        return `${years}年`
      }
    }
    
    // 获取难度等级
    const getDifficultyLevel = (attempts) => {
      if (attempts < 1000) {
        return '简单'
      } else if (attempts < 100000) {
        return '中等'
      } else if (attempts < 10000000) {
        return '困难'
      } else if (attempts < 1000000000) {
        return '极难'
      } else {
        return '几乎不可能'
      }
    }
    
    // 获取成功概率描述
    const getSuccessProbability = (probability) => {
      if (probability > 0.1) {
        return '很高 (>10%)'
      } else if (probability > 0.01) {
        return '高 (1-10%)'
      } else if (probability > 0.001) {
        return '中等 (0.1-1%)'
      } else if (probability > 0.0001) {
        return '低 (0.01-0.1%)'
      } else {
        return '极低 (<0.01%)'
      }
    }

    // 自动预估计算（类似后端生成器）
    const calculateAutoEstimation = (pattern, position, addressType) => {
      if (!pattern) {
        return {
          attempts: 1,
          timeRange: '',
          difficulty: 'easy',
          difficultyText: '简单'
        }
      }

      // 计算有效字符集大小
      let validChars = 58 // Base58字符集
      if (addressType === 'p2wpkh' || addressType === 'p2tr') {
        validChars = 32 // Bech32字符集
      }

      // 获取地址长度（去除前缀后的有效部分）
      let effectiveLength
      switch (addressType) {
        case 'p2pkh':
          effectiveLength = 33 // 去除'1'前缀
          break
        case 'p2sh':
          effectiveLength = 34 // 去除'3'前缀
          break
        case 'p2wpkh':
          effectiveLength = 39 // 去除'bc1'前缀
          break
        case 'p2tr':
          effectiveLength = 59 // 去除'bc1p'前缀
          break
        default:
          effectiveLength = 34
      }

      // 计算理论尝试次数
      let attempts
      
      switch (position) {
        case 'start':
          // 开头匹配：只考虑去除前缀后的开头位置
          attempts = Math.pow(validChars, pattern.length)
          break
        case 'end':
          // 末尾匹配：考虑地址末尾位置
          attempts = Math.pow(validChars, pattern.length)
          break
        case 'anywhere':
        default:
          // 任意位置匹配：考虑所有可能的位置
          const possiblePositions = Math.max(1, effectiveLength - pattern.length + 1)
          attempts = Math.pow(validChars, pattern.length) / possiblePositions
          break
      }

      // 平均需要尝试一半的次数
      attempts = Math.floor(attempts / 2)

      // 确保最小值为1
      attempts = Math.max(1, attempts)

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

    // 更新自动预估
    const updateEstimation = () => {
      autoEstimation.value = calculateAutoEstimation(pattern.value, patternPosition.value, selectedAddressType.value)
    }

    // 格式化数字显示
     const formatNumber = (num) => {
       if (num < 1000) return num.toString()
       if (num < 1000000) return (num / 1000).toFixed(1) + 'K'
       if (num < 1000000000) return (num / 1000000).toFixed(1) + 'M'
       return (num / 1000000000).toFixed(1) + 'B'
     }

     // 初始化时更新预估
     onMounted(() => {
       updateEstimation()
     })

     // 监听地址类型变化，更新预估信息
     watch(selectedAddressType, () => {
       updateEstimation()
     })

     // 保存地址到后端数据库
     const saveToBackend = async (result) => {
       try {
         const response = await fetch('http://localhost:8000/save-address', {
           method: 'POST',
           headers: {
             'Content-Type': 'application/json',
           },
           body: JSON.stringify({
             address: result.address,
             private_key: result.privateKeyWIF,
             address_type: result.addressType,
             pattern: result.pattern || '',
             position: result.patternPosition || 'anywhere',
             attempts: result.attempts || 1,
             generation_source: 'frontend'
           })
         })
         
         if (!response.ok) {
           console.warn('保存到后端失败:', response.statusText)
         }
       } catch (error) {
         console.warn('保存到后端时发生错误:', error.message)
       }
     }

     return {
      selectedAddressType,
      concurrentGenerators,
      performanceMode,
      pattern,
      patternPosition,
      isGenerating,
      currentStatus,
      attempts,
      currentAddress,
      results,
      error,
      targetCount,
      progressPercentage,
      isEstimating,
      estimationResult,
      autoEstimation,
      generatorStates,
      totalGenerated,
      totalTarget,
      totalAttempts,
      overallProgressPercentage,

      generateAddresses,
      stopGeneration,
      clearResults,
      copyToClipboard,
      estimateTime,
      updateEstimation,
      formatNumber,
      getStatusText,
      getPerformanceModeDescription,
      getPerformanceConfig,

    }
  }
}
</script>

<style scoped>
/* 移除重复的样式，使用App.vue中的样式 */

.form-group {
  margin-bottom: 28px;
}

.form-group label {
  display: block;
  margin-bottom: 12px;
  font-weight: 600;
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
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  min-height: 56px;
  box-sizing: border-box;
}

.select-input {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23667eea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6,9 12,15 18,9"></polyline></svg>');
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 20px;
  padding-right: 50px;
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

.select-input option {
  padding: 12px 16px;
  background: white;
  color: #374151;
  font-size: 1rem;
  font-weight: 500;
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
  cursor: pointer;
  font-weight: normal;
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
  min-width: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 56px;
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

.btn-estimate {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  box-shadow: 0 8px 25px rgba(245, 158, 11, 0.3);
  width: 100%;
  margin-bottom: 20px;
}

.btn-estimate:hover:not(:disabled) {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(245, 158, 11, 0.4);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.btn:disabled::before {
  display: none;
}

.progress-section {
  padding: 32px 48px;
  background: linear-gradient(135deg, rgba(248, 249, 250, 0.8) 0%, rgba(241, 245, 249, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(229, 231, 235, 0.6);
  position: relative;
}

.progress-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #667eea);
  background-size: 300% 100%;
  animation: progressBorder 4s linear infinite;
}

@keyframes progressBorder {
  0% { background-position: 0% 0; }
  100% { background-position: 300% 0; }
}

.progress-section h3 {
  margin: 0 0 24px 0;
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
  margin: 12px 0;
  color: #374151;
  font-weight: 500;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: rgba(229, 231, 235, 0.8);
  border-radius: 8px;
  overflow: hidden;
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
  animation: progressGradient 3s ease infinite;
}

@keyframes progressGradient {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.results-section {
  padding: 30px 40px;
  border-top: 1px solid #e9ecef;
}

.results-section h3 {
  margin: 0 0 25px 0;
  color: #333;
}

.results-container {
  max-height: 600px;
  overflow-y: auto;
}

.result-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.result-index {
  font-weight: 600;
  color: #667eea;
  font-size: 1.1em;
}

.attempts-badge {
  background: #28a745;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: 500;
}

.result-field {
  margin-bottom: 15px;
}

.result-field:last-child {
  margin-bottom: 0;
}

.result-field label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #333;
  font-size: 0.9em;
}

.result-value {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-value code {
  flex: 1;
  background: white;
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  word-break: break-all;
}

.copy-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9em;
  transition: background 0.3s;
}

.copy-btn:hover {
  background: #5a6fd8;
}

.error-section {
  padding: 30px 40px;
  background: #f8d7da;
  border-top: 1px solid #f5c6cb;
  color: #721c24;
}

.error-section h3 {
  margin: 0 0 15px 0;
}

small {
  color: #6c757d;
  font-size: 0.9em;
  margin-top: 5px;
  display: block;
}

.estimation-section {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%);
  border: 2px solid rgba(245, 158, 11, 0.2);
  border-radius: 16px;
  padding: 24px;
  margin-top: 20px;
  backdrop-filter: blur(10px);
}

.estimation-section h4 {
  margin: 0 0 16px 0;
  color: #d97706;
  font-size: 1.3rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.estimation-info {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.estimation-info p {
  margin: 12px 0;
  color: #374151;
  font-weight: 500;
  font-size: 1rem;
}

.difficulty-bar {
  width: 100%;
  height: 8px;
  background: rgba(229, 231, 235, 0.8);
  border-radius: 6px;
  overflow: hidden;
  margin: 16px 0;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.difficulty-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981 0%, #f59e0b 50%, #ef4444 100%);
  border-radius: 6px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.estimation-info small {
  color: #9ca3af;
  font-size: 0.85rem;
  font-style: italic;
  margin-top: 12px;
}

.estimate-hint {
  color: #6b7280;
  font-size: 0.9rem;
  margin-top: 8px;
  display: block;
  text-align: center;
  font-weight: 500;
}

.estimation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.estimation-label {
  font-weight: 600;
  color: #374151;
}

.estimation-value {
  font-weight: 500;
  color: #1f2937;
}

.difficulty-easy {
  color: #10b981;
}

.difficulty-medium {
  color: #f59e0b;
}

.difficulty-hard {
  color: #ef4444;
}

.difficulty-extreme {
  color: #dc2626;
  font-weight: 700;
}

.estimation-note {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(229, 231, 235, 0.6);
}

.estimation-note small {
  color: #9ca3af;
  font-size: 0.85rem;
  font-style: italic;
}

/* 并发生成器样式 */
.overall-progress {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.generators-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.generator-box {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(229, 231, 235, 0.6);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.generator-box.active {
  border-color: #4CAF50;
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.2);
  transform: translateY(-2px);
}

.generator-box.completed {
  border-color: #2196F3;
  background: rgba(33, 150, 243, 0.1);
  box-shadow: 0 8px 25px rgba(33, 150, 243, 0.2);
}

.generator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.generator-header h4 {
  margin: 0;
  font-size: 1.1rem;
  color: #1f2937;
  font-weight: 600;
}

.generator-status {
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.generator-status.waiting {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #000;
}

.generator-status.running {
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
  animation: statusPulse 2s infinite;
}

.generator-status.completed {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
}

.generator-status.error {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
}

.generator-status.stopped {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: #fff;
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

.generator-stats {
  margin-bottom: 1rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.stat-label {
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  color: #1f2937;
  font-weight: 600;
}

.address-preview {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  background: rgba(102, 126, 234, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
}

.generator-progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.progress-bar.small {
  height: 8px;
  flex: 1;
  background: rgba(229, 231, 235, 0.8);
}

.progress-text {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.generator-results {
  border-top: 1px solid rgba(229, 231, 235, 0.6);
  padding-top: 0.75rem;
}

.result-count {
  font-size: 0.9rem;
  color: #059669;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.latest-result {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  color: #6b7280;
  background: rgba(248, 249, 250, 0.8);
  padding: 0.3rem 0.5rem;
  border-radius: 6px;
  border: 1px solid rgba(229, 231, 235, 0.6);
}

@media (max-width: 768px) {
  .container {
    margin: 10px;
    border-radius: 15px;
  }
  
  .header {
    padding: 30px 20px;
  }
  
  .generator-form, .progress-section, .results-section {
    padding: 20px;
  }
  
  .button-group {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
  
  .radio-group {
    flex-direction: column;
    gap: 10px;
  }
  
  .generators-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .generator-box {
    padding: 1rem;
  }
}
</style>