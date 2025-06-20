# CSV数据统计脚本使用说明


## 功能描述
- 读取标准CSV格式文件
- 自动识别数值列并计算统计指标：
  - 行数统计
  - 列数统计
  - 数值列的平均值计算
- 支持UTF-8编码的文件
- 包含基本的错误处理机制

## 系统要求
- Python 3.6+
- 仅依赖标准库(csv, sys等)

## 使用方法
1. 准备CSV文件(确保第一行是列名)
2. 执行脚本：
   ```bash
   python csv_stats.py 输入文件.csv
   ```
3. 查看控制台输出的统计结果

## 输出示例
```
成功读取文件: data.csv
列名: id, value, score
总行数: 100
总列数: 3

数值列统计:
列 'value':
  有效值数量: 100
  平均值: 42.35
列 'score':
  有效值数量: 100
  平均值: 85.60

任务完成 - CSV文件处理成功
```

## 注意事项
1. 确保输入文件是标准的CSV格式
2. 仅处理数值列(自动跳过非数值列)
3. 空值或非数值内容会被自动忽略
4. 文件编码应为UTF-8

## 错误处理
脚本会检测并报告以下错误：
- 文件不存在
- 文件不是CSV格式
- 文件读取错误
- 列数据处理错误

## 扩展建议
如需更多统计功能，可考虑添加：
- 最小值/最大值计算
- 数据总和
- 标准差计算
- 数据分布统计