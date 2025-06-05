import heapq
import os
import time
from collections import defaultdict
from decimal import Decimal, getcontext  # 用于高精度算术计算

# 霍夫曼树节点类
class HuffmanNode:
    def __init__(self, freq, byte=None, left=None, right=None):
        self.freq = freq    # 节点频率
        self.byte = byte    # 字节值（仅叶子节点有值）
        self.left = left    # 左子树
        self.right = right  # 右子树

    # 用于堆排序的比较方法
    def __lt__(self, other):
        return self.freq < other.freq

def huffman_compress(text_bytes):
    # 统计字节频率
    freq = defaultdict(int)
    for byte in text_bytes:
        freq[byte] += 1  # 统计每个字节出现的次数

    # 构建优先队列（最小堆）
    heap = []
    for byte, count in freq.items():
        # 将每个字节转换为叶子节点加入堆
        heapq.heappush(heap, HuffmanNode(count, byte=byte))

    # 构建霍夫曼树
    while len(heap) > 1:
        # 取出频率最小的两个节点
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        # 合并为新的内部节点（频率为两者之和）
        merged = HuffmanNode(left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    root = heapq.heappop(heap) if heap else None  # 根节点
    code_table = {}  # 编码表（字节->二进制字符串）

    # 递归构建编码表
    def build_code(node, current_code=""):
        if node is None:
            return
        if node.byte is not None:
            # 叶子节点：记录字节对应的编码
            code_table[node.byte] = current_code
            return
        # 左子树编码加0，右子树编码加1
        build_code(node.left, current_code + '0')
        build_code(node.right, current_code + '1')

    if root:
        build_code(root)

    # 生成编码位流
    encoded_bits = ''.join([code_table[byte] for byte in text_bytes])
    # 计算填充位数（使总位数为8的倍数）
    padding = 8 - (len(encoded_bits) % 8)
    if padding != 8:
        encoded_bits += '0' * padding  # 填充0

    # 转换为字节列表
    bytes_list = [int(encoded_bits[i:i+8], 2) for i in range(0, len(encoded_bits), 8)]

    # 保存压缩后的二进制文件
    with open('huffman_compressed.bin', 'wb') as f:
        f.write(bytes(bytes_list))

    # 保存中间信息（频率表和编码表）
    with open('huffman_info.txt', 'w', encoding='utf-8') as f:
        f.write("=== 字符频率表 ===\n")
        # 按频率从高到低排序
        for byte, count in sorted(freq.items(), key=lambda x: -x[1]):
            # 处理不可打印字符（用空格表示）
            char = chr(byte) if 32 <= byte <= 126 else ' '
            f.write(f"字节 {byte:3d}（字符: {char}）: 频率 = {count}\n")
        
        f.write("\n=== 霍夫曼编码表 ===\n")
        # 按编码长度排序
        for byte, code in sorted(code_table.items(), key=lambda x: len(x[1])):
            char = chr(byte) if 32 <= byte <= 126 else ' '
            f.write(f"字节 {byte:3d}（字符: {char}）: 编码 = {code}\n")

    return {
        'original_size': len(text_bytes),       # 原始大小
        'compressed_size': len(bytes_list),     # 压缩后大小
        'compression_ratio': len(bytes_list) / len(text_bytes) if text_bytes else 0,
        'time': 0                               # 预留时间字段
    }

def arithmetic_compress(text_bytes):
    getcontext().prec = 1000  # 设置高精度十进制精度

    # 统计字节频率
    freq = defaultdict(int)
    for byte in text_bytes:
        freq[byte] += 1

    total = sum(freq.values())  # 总字符数
    cum_prob = {}              # 累积概率表（字节->(下限, 上限)）
    current = Decimal(0)       # 当前累积概率

    # 生成累积概率区间
    for byte in sorted(freq.keys()):  # 按字节值排序
        prob = Decimal(freq[byte]) / Decimal(total)  # 计算概率
        cum_prob[byte] = (current, current + prob)   # 记录区间
        current += prob                              # 累加概率

    low = Decimal(0)       # 区间下限
    high = Decimal(1)      # 区间上限

    # 逐个字节更新区间
    for byte in text_bytes:
        char_low, char_high = cum_prob[byte]  # 获取当前字节的概率区间
        range_size = high - low               # 当前区间长度
        # 缩小区间范围
        high = low + range_size * char_high
        low = low + range_size * char_low

    # 将最终区间转换为二进制字符串
    binary_str = []
    value = low  # 取区间内任意值（通常取下限）
    for _ in range(1024):  # 最多生成1024位二进制
        value *= 2          # 左移一位（相当于乘以2）
        bit = int(value)    # 提取整数部分作为二进制位
        binary_str.append(str(bit))
        value -= bit        # 保留小数部分
        if value == 0:      # 提前结束条件
            break

    binary_str = ''.join(binary_str)
    # 填充到8的倍数
    padding = 8 - (len(binary_str) % 8)
    if padding != 8:
        binary_str += '0' * padding

    # 转换为字节列表
    bytes_list = [int(binary_str[i:i+8], 2) for i in range(0, len(binary_str), 8)]
    # 保存压缩后的二进制文件
    with open('arithmetic_compressed.bin', 'wb') as f:
        f.write(bytes(bytes_list))

    # 保存中间信息（概率区间和最终区间）
    with open('arithmetic_info.txt', 'w', encoding='utf-8') as f:
        f.write("=== 字符概率区间表 ===\n")
        for byte in sorted(cum_prob.keys()):
            low_range, high_range = cum_prob[byte]
            # 转换为浮点数便于显示（牺牲精度）
            char = chr(byte) if 32 <= byte <= 126 else ' '
            f.write(f"字节 {byte:3d}（字符: {char}）: 区间 = [{float(low_range):.10f}, {float(high_range):.10f})\n")
        
        f.write(f"\n最终压缩区间: [{float(low):.20f}, {float(high):.20f})\n")

    return {
        'original_size': len(text_bytes),
        'compressed_size': len(bytes_list),
        'compression_ratio': len(bytes_list) / len(text_bytes) if text_bytes else 0,
        'time': 0
    }

def lzw_compress(text_bytes):
    # 初始化字典：单字节到索引的映射（0-255）
    dictionary = {bytes([i]): i for i in range(256)}
    next_code = 256  # 下一个可用索引
    s = bytes()       # 当前匹配字符串
    encoded = []      # 编码结果列表

    for byte in text_bytes:
        sc = s + bytes([byte])  # 尝试扩展当前字符串
        if sc in dictionary:
            s = sc  # 存在则继续扩展
        else:
            # 输出当前字符串的索引
            encoded.append(dictionary[s])
            # 将新字符串加入字典
            dictionary[sc] = next_code
            next_code += 1
            s = bytes([byte])  # 重置当前字符串为当前字节
    # 处理最后一个字符串
    if s:
        encoded.append(dictionary[s])

    # 将编码转换为12位二进制字符串（假设索引最大4095）
    bits_str = ''.join([format(code, '012b') for code in encoded])
    # 填充到8的倍数
    padding = 8 - (len(bits_str) % 8)
    if padding != 8:
        bits_str += '0' * padding

    # 转换为字节列表
    bytes_list = [int(bits_str[i:i+8], 2) for i in range(0, len(bits_str), 8)]
    # 保存压缩后的二进制文件
    with open('lzw_compressed.bin', 'wb') as f:
        f.write(bytes(bytes_list))

    # 保存中间信息（字典大小和编码序列）
    with open('lzw_info.txt', 'w', encoding='utf-8') as f:
        f.write(f"字典最大索引: {next_code - 1}\n")
        f.write("\n=== 编码序列 ===\n")
        for i, code in enumerate(encoded):
            if i % 20 == 0 and i != 0:
                f.write("\n")  # 每20个编码换行
            f.write(f"{code:4d} ")  # 固定宽度输出

    return {
        'original_size': len(text_bytes),
        'compressed_size': len(bytes_list),
        'compression_ratio': len(bytes_list) / len(text_bytes) if text_bytes else 0,
        'time': 0
    }

def main():
    # 读取原始文件（自动处理UTF-8编码）
    with open('pki_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    text_bytes = text.encode('utf-8')  # 转换为字节流

    # 霍夫曼编码
    start = time.time()
    huffman_result = huffman_compress(text_bytes)
    huffman_time = (time.time() - start)*1000

    # 算术编码
    start = time.time()
    arithmetic_result = arithmetic_compress(text_bytes)
    arithmetic_time = (time.time() - start)*1000

    # LZW编码
    start = time.time()
    lzw_result = lzw_compress(text_bytes)
    lzw_time = (time.time() - start)*1000

    # 输出霍夫曼编码结果
    print("霍夫曼编码:")
    print(f"原始文件大小: {huffman_result['original_size']} 字节")
    print(f"压缩后大小: {huffman_result['compressed_size']} 字节")
    print(f"压缩比: {huffman_result['compression_ratio']:.2%}")
    print(f"耗时: {huffman_time:.2f}ms\n")

    # 输出算术编码结果
    print("算术编码:")
    print(f"原始文件大小: {arithmetic_result['original_size']} 字节")
    print(f"压缩后大小: {arithmetic_result['compressed_size']} 字节")
    print(f"压缩比: {arithmetic_result['compression_ratio']:.2%}")
    print(f"耗时: {arithmetic_time:.2f}ms\n")

    # 输出LZW编码结果
    print("LZW编码:")
    print(f"原始文件大小: {lzw_result['original_size']} 字节")
    print(f"压缩后大小: {lzw_result['compressed_size']} 字节")
    print(f"压缩比: {lzw_result['compression_ratio']:.2%}")
    print(f"耗时: {lzw_time:.2f}ms\n")

if __name__ == "__main__":
    main()