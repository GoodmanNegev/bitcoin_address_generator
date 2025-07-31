// 独立的加密Worker，使用ES模块导入
import { ec as EC } from 'elliptic';
import CryptoJS from 'crypto-js';
import bs58 from 'bs58';
import { bech32 } from 'bech32';

// 初始化椭圆曲线
const ec = new EC('secp256k1');

// 性能优化：缓存哈希对象
const sha256Cache = [];
const ripemd160Cache = [];
const MAX_CACHE_SIZE = 5;

// 优化的哈希函数 - 使用对象池
function getCachedSHA256() {
  if (sha256Cache.length > 0) {
    return sha256Cache.pop();
  }
  return CryptoJS.algo.SHA256.create();
}

function returnSHA256ToCache(hasher) {
  if (sha256Cache.length < MAX_CACHE_SIZE) {
    hasher.reset();
    sha256Cache.push(hasher);
  }
}

function getCachedRIPEMD160() {
  if (ripemd160Cache.length > 0) {
    return ripemd160Cache.pop();
  }
  return CryptoJS.algo.RIPEMD160.create();
}

function returnRIPEMD160ToCache(hasher) {
  if (ripemd160Cache.length < MAX_CACHE_SIZE) {
    hasher.reset();
    ripemd160Cache.push(hasher);
  }
}

// 优化的SHA256哈希 - 使用对象池
function sha256(data) {
  const hasher = getCachedSHA256();
  if (typeof data === 'string') {
    data = CryptoJS.enc.Hex.parse(data);
  }
  const result = hasher.update(data).finalize().toString();
  returnSHA256ToCache(hasher);
  return result;
}

// 优化的RIPEMD160哈希 - 使用对象池
function ripemd160(data) {
  const hasher = getCachedRIPEMD160();
  if (typeof data === 'string') {
    data = CryptoJS.enc.Hex.parse(data);
  }
  const result = hasher.update(data).finalize().toString();
  returnRIPEMD160ToCache(hasher);
  return result;
}

// 优化的随机私钥生成 - 预分配缓冲区
const privateKeyBuffer = new Uint8Array(32);
const hexLookup = ['00','01','02','03','04','05','06','07','08','09','0a','0b','0c','0d','0e','0f',
                   '10','11','12','13','14','15','16','17','18','19','1a','1b','1c','1d','1e','1f',
                   '20','21','22','23','24','25','26','27','28','29','2a','2b','2c','2d','2e','2f',
                   '30','31','32','33','34','35','36','37','38','39','3a','3b','3c','3d','3e','3f',
                   '40','41','42','43','44','45','46','47','48','49','4a','4b','4c','4d','4e','4f',
                   '50','51','52','53','54','55','56','57','58','59','5a','5b','5c','5d','5e','5f',
                   '60','61','62','63','64','65','66','67','68','69','6a','6b','6c','6d','6e','6f',
                   '70','71','72','73','74','75','76','77','78','79','7a','7b','7c','7d','7e','7f',
                   '80','81','82','83','84','85','86','87','88','89','8a','8b','8c','8d','8e','8f',
                   '90','91','92','93','94','95','96','97','98','99','9a','9b','9c','9d','9e','9f',
                   'a0','a1','a2','a3','a4','a5','a6','a7','a8','a9','aa','ab','ac','ad','ae','af',
                   'b0','b1','b2','b3','b4','b5','b6','b7','b8','b9','ba','bb','bc','bd','be','bf',
                   'c0','c1','c2','c3','c4','c5','c6','c7','c8','c9','ca','cb','cc','cd','ce','cf',
                   'd0','d1','d2','d3','d4','d5','d6','d7','d8','d9','da','db','dc','dd','de','df',
                   'e0','e1','e2','e3','e4','e5','e6','e7','e8','e9','ea','eb','ec','ed','ee','ef',
                   'f0','f1','f2','f3','f4','f5','f6','f7','f8','f9','fa','fb','fc','fd','fe','ff'];

function generatePrivateKey() {
  crypto.getRandomValues(privateKeyBuffer);
  let result = '';
  for (let i = 0; i < 32; i++) {
    result += hexLookup[privateKeyBuffer[i]];
  }
  return result;
}

// 私钥转公钥 - 使用elliptic库保持一致性
function privateKeyToPublicKey(privateKeyHex) {
  const keyPair = ec.keyFromPrivate(privateKeyHex, 'hex');
  return keyPair.getPublic('hex');
}

// 压缩公钥
function compressPublicKey(publicKeyHex) {
  if (publicKeyHex.length === 66) {
    return publicKeyHex; // 已经是压缩格式
  }
  
  if (publicKeyHex.length === 130 && publicKeyHex.startsWith('04')) {
    const x = publicKeyHex.slice(2, 66);
    const y = publicKeyHex.slice(66, 130);
    
    // 检查y坐标的奇偶性
    const yBigInt = BigInt('0x' + y);
    const prefix = yBigInt % 2n === 0n ? '02' : '03';
    return prefix + x;
  }
  
  return publicKeyHex;
}

// 十六进制转Uint8Array
function hexToUint8Array(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
  }
  return bytes;
}

// Uint8Array转十六进制
function uint8ArrayToHex(bytes) {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

// Hash160 (SHA256 + RIPEMD160)
function hash160(data) {
  const sha = sha256(data);
  return ripemd160(sha);
}

// 双重SHA256
function hash256(data) {
  const first = sha256(data);
  return sha256(first);
}

// Base58编码 - 使用bs58库
function base58Encode(bytes) {
  return bs58.encode(bytes);
}

// Bech32编码 - 使用bech32库
function bech32Encode(hrp, data) {
  return bech32.encode(hrp, data);
}

// 异步SHA256哈希
// 创建P2PKH地址
function createP2PKHAddress(publicKeyHex) {
  const compressedPubKey = compressPublicKey(publicKeyHex);
  const pubKeyHash = hash160(compressedPubKey);
  const versionedPayload = '00' + pubKeyHash;
  const checksum = hash256(versionedPayload).slice(0, 8);
  const fullPayload = versionedPayload + checksum;
  return base58Encode(hexToUint8Array(fullPayload));
}

// 创建P2SH地址
function createP2SHAddress(publicKeyHex) {
  const compressedPubKey = compressPublicKey(publicKeyHex);
  const pubKeyHash = hash160(compressedPubKey);
  // P2WPKH脚本: OP_0 + 20字节pubKeyHash
  const redeemScript = '0014' + pubKeyHash;
  const scriptHash = hash160(redeemScript);
  const versionedPayload = '05' + scriptHash;
  const checksum = hash256(versionedPayload).slice(0, 8);
  const fullPayload = versionedPayload + checksum;
  return base58Encode(hexToUint8Array(fullPayload));
}

// 将字节数组转换为5位组
function convertBits(data, fromBits, toBits, pad = true) {
  let acc = 0;
  let bits = 0;
  const ret = [];
  const maxv = (1 << toBits) - 1;
  const maxAcc = (1 << (fromBits + toBits - 1)) - 1;
  
  for (let value of data) {
    if (value < 0 || (value >> fromBits)) {
      throw new Error('Invalid data for base conversion');
    }
    acc = ((acc << fromBits) | value) & maxAcc;
    bits += fromBits;
    while (bits >= toBits) {
      bits -= toBits;
      ret.push((acc >> bits) & maxv);
    }
  }
  
  if (pad) {
    if (bits) {
      ret.push((acc << (toBits - bits)) & maxv);
    }
  } else if (bits >= fromBits || ((acc << (toBits - bits)) & maxv)) {
    throw new Error('Invalid padding in base conversion');
  }
  
  return ret;
}

// 创建P2WPKH地址
function createP2WPKHAddress(publicKeyHex) {
  const compressedPubKey = compressPublicKey(publicKeyHex);
  const pubKeyHash = hash160(compressedPubKey);
  const data = hexToUint8Array(pubKeyHash);
  
  // 转换为5位组：版本(0) + 转换后的数据
  const converted = convertBits(Array.from(data), 8, 5);
  return bech32Encode('bc', [0].concat(converted));
}

// 创建P2TR地址 (Taproot)
function createP2TRAddress(publicKeyHex) {
  const compressedPubKey = compressPublicKey(publicKeyHex);
  // 提取x坐标（去掉前缀字节）
  const xCoord = compressedPubKey.slice(2);
  const data = hexToUint8Array(xCoord);
  
  // 转换为5位组：版本(1) + 转换后的数据
  const converted = convertBits(Array.from(data), 8, 5);
  return bech32Encode('bc', [1].concat(converted));
}

// 私钥转WIF格式
function privateKeyToWIF(privateKeyHex) {
  const versionedKey = '80' + privateKeyHex + '01'; // 0x80前缀 + 私钥 + 0x01后缀(压缩)
  const checksum = hash256(versionedKey).slice(0, 8);
  const fullKey = versionedKey + checksum;
  return base58Encode(hexToUint8Array(fullKey));
}

// 生成地址
function generateAddress(addressType, privateKeyHex) {
  const publicKeyHex = privateKeyToPublicKey(privateKeyHex);
  
  let address;
  switch (addressType) {
    case 'p2pkh':
      address = createP2PKHAddress(publicKeyHex);
      break;
    case 'p2sh':
      address = createP2SHAddress(publicKeyHex);
      break;
    case 'p2wpkh':
      address = createP2WPKHAddress(publicKeyHex);
      break;
    case 'p2tr':
      address = createP2TRAddress(publicKeyHex);
      break;
    default:
      address = createP2PKHAddress(publicKeyHex);
  }
  
  return {
    address,
    privateKeyHex,
    privateKeyWIF: privateKeyToWIF(privateKeyHex)
  };
}

// 检查模式匹配
function checkPatternMatch(address, pattern, position) {
  if (!pattern) return true;
  
  const lowerAddress = address.toLowerCase();
  const lowerPattern = pattern.toLowerCase();
  
  switch (position) {
    case 'start':
      const addressWithoutPrefix = lowerAddress.startsWith('bc1') ? lowerAddress.slice(3) : lowerAddress.slice(1);
      return addressWithoutPrefix.startsWith(lowerPattern);
    case 'end':
      return lowerAddress.endsWith(lowerPattern);
    case 'anywhere':
    default:
      return lowerAddress.includes(lowerPattern);
  }
}

// 优化的Worker消息处理
self.onmessage = async function(e) {
  const { type, addressType, pattern, patternPosition, count, workerId, targetCount, testPrivateKey, performanceConfig } = e.data;
  
  // 使用性能配置，如果没有提供则使用默认值
  const config = performanceConfig || {
    batchSize: 100,
    progressInterval: 2000,
    maxAttempts: 2000000,
    workerDelay: 0
  };
  
  try {
    if (type === 'batch') {
      // 优化的批量生成（无模式匹配）- 使用性能配置
      const results = [];
      const batchSize = Math.min(count, config.batchSize);
      let processed = 0;
      
      while (processed < count) {
        const currentBatch = Math.min(batchSize, count - processed);
        
        for (let i = 0; i < currentBatch; i++) {
          const privateKeyHex = testPrivateKey || generatePrivateKey();
          const result = generateAddress(addressType, privateKeyHex);
          results.push(result);
        }
        
        processed += currentBatch;
        
        // 根据性能配置决定是否让出控制权
        if (processed < count && config.workerDelay >= 0) {
          await new Promise(resolve => setTimeout(resolve, config.workerDelay));
        }
      }
      
      self.postMessage({ type: 'batch_result', data: results, workerId: workerId });
    } else {
      // 优化的模式匹配生成 - 使用性能配置
      let attempts = 0;
      let foundCount = 0;
      const target = targetCount || 1;
      const maxAttempts = config.maxAttempts;
      let lastProgressReport = 0;
      const progressInterval = config.progressInterval;
      
      while (attempts < maxAttempts && foundCount < target) {
        attempts++;
        
        const privateKeyHex = generatePrivateKey();
        const result = generateAddress(addressType, privateKeyHex);
        
        if (checkPatternMatch(result.address, pattern, patternPosition)) {
          foundCount++;
          self.postMessage({
            type: 'result',
            data: {
              ...result,
              attempts: attempts,
              workerId: workerId
            }
          });
          
          if (foundCount >= target) {
            break;
          }
        }
        
        // 优化的进度报告 - 使用性能配置
          if (attempts - lastProgressReport >= progressInterval) {
            self.postMessage({
              type: 'progress',
              data: {
                attempts: attempts,
                currentAddress: result.address,
                workerId: workerId
              }
            });
            lastProgressReport = attempts;
            
            // 根据性能配置决定延迟时间
            if (config.workerDelay >= 0) {
              await new Promise(resolve => setTimeout(resolve, config.workerDelay));
            }
          }
      }
      
      // 如果达到最大尝试次数仍未找到足够的地址
      if (foundCount < target) {
        self.postMessage({
          type: 'progress',
          data: {
            attempts: attempts,
            currentAddress: '',
            workerId: workerId
          }
        });
      }
    }
  } catch (error) {
    self.postMessage({
      type: 'error',
      data: { message: '加密操作失败: ' + error.message }
    });
  }
};