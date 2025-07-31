<template>
  <div class="app">
    <div class="container">
      <header class="header">
        <h1>🪙 比特币地址生成器</h1>
        <p class="subtitle">学习比特币密码学的教育工具</p>
        <div class="warning">
          ⚠️ 仅供教育目的使用，切勿将生成的私钥用于真实的比特币交易！
        </div>
      </header>

      <div class="generator-form">
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

      <div v-if="error" class="error-section">
        <h3>❌ 错误</h3>
        <p>{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
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
        timeRange = `${Math.floor(minTime)}秒 - ${Math.floor(maxTime/60)}分钟`
        difficulty = 'medium'
        difficultyText = '中等'
      } else if (attempts < 10000000) {
        timeRange = `${Math.floor(minTime/60)}分钟 - ${Math.floor(maxTime/3600)}小时`
        difficulty = 'hard'
        difficultyText = '困难'
      } else {
        timeRange = `${Math.floor(minTime/3600)}小时 - ${Math.floor(maxTime/86400)}天`
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

    onMounted(() => {
      loadAddressTypes()
      updateEstimation()
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

    return {
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
      formatNumber
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

.container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  padding: 40px;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.header h1 {
  font-size: 2.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 10px;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
  margin-bottom: 15px;
}

.warning {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  color: #856404;
  padding: 15px;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.4;
  margin-bottom: 5px;
}

.generator-form {
  margin-bottom: 40px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.select-input, .text-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
  min-height: 44px;
}

.select-input:focus, .text-input:focus {
  outline: none;
  border-color: #667eea;
}

.text-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
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
  gap: 15px;
  flex-wrap: wrap;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  white-space: nowrap;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.results-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 25px;
  margin: 30px 0 20px 0;
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.progress-section h3,
.result-section h3 {
  margin-bottom: 20px;
  color: #333;
}

.progress-info p {
  margin-bottom: 10px;
}

.progress-info code {
  background: #e9ecef;
  padding: 6px 10px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  word-break: break-all;
  font-size: 0.9rem;
  display: inline-block;
  max-width: 100%;
  overflow-wrap: break-word;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 15px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s ease;
}

.result-item {
  margin-bottom: 20px;
}

.result-item label {
  font-weight: 600;
  color: #333;
  margin-bottom: 5px;
  display: block;
}

.result-value {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-value code {
  background: #e9ecef;
  padding: 12px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  word-break: break-all;
  flex: 1;
  font-size: 0.9rem;
}

.copy-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.copy-btn:hover {
  background: #218838;
}

.attempts-badge {
  background: #007bff;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
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
</style>