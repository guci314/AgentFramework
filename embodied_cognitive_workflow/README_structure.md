# 目录结构说明

## 项目重组说明

为了更好地组织代码，我们已经将演示文件和测试文件分别移动到了独立的目录中。

### 目录结构

```
embodied_cognitive_workflow/
├── demo/                    # 演示文件目录（19个文件）
│   ├── calculator_demo.py
│   ├── debug_demo.py
│   ├── demo_cognitive_debugger.py
│   ├── multi_agent_demo.py
│   └── ... 其他演示文件
│
├── tests/                   # 测试文件目录（39个文件）
│   ├── test_cognitive_debugger.py
│   ├── test_ego_agent_fix.py
│   ├── test_decision_refactoring.py
│   └── ... 其他测试文件
│
├── ai_docs/                 # AI文档目录
│   └── ... 文档文件
│
├── predefined_agent/        # 预定义Agent目录
│   └── ... Agent文件
│
└── 核心模块文件
    ├── embodied_cognitive_workflow.py
    ├── ego_agent.py
    ├── id_agent.py
    ├── meta_cognitive_agent.py
    ├── cognitive_debugger.py
    └── decision_types.py
```

### 导入路径更新

由于文件位置发生了变化，在demo和tests目录中的文件需要正确设置Python路径：

#### 对于tests目录中的文件：
```python
import sys
import os
# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# 然后可以正常导入
from embodied_cognitive_workflow import CognitiveAgent
from ego_agent import EgoAgent
```

#### 对于demo目录中的文件：
```python
import sys
import os
# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# 然后可以正常导入
from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger
```

### 运行示例

#### 运行测试：
```bash
cd embodied_cognitive_workflow/tests
python test_cognitive_debugger.py
```

#### 运行演示：
```bash
cd embodied_cognitive_workflow/demo
python demo_cognitive_debugger.py
```

### 文件数量统计
- **Demo文件**: 19个
- **Test文件**: 39个

这种组织方式使项目结构更加清晰，便于维护和查找相关文件。