# %%
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Callable, Type, Dict, Any, TypeVar, ClassVar
import uuid
from collections import defaultdict
import inspect
import unittest
import io
from contextlib import redirect_stdout
from abc import ABC, abstractmethod
from copy import deepcopy  # 添加这个导入
from datetime import datetime
from mda.memory_kafka import MemoryKafka


# 在代码开始处设置全局配置
BaseModel.model_config = ConfigDict(arbitrary_types_allowed=True)

T = TypeVar('T')  # 定义一个泛型类型变量

def value_object(cls: Type[T]) -> Type[T]:
    """值对象装饰器"""
    cls._is_value_object = True
    return cls

def entity(cls: Type[T]) -> Type[T]:
    """
    装饰器用于标记一个类为领域驱动设计中的实体（Entity）。
    
    实体类都有id属性，类型是str，是主键。通常是uuid.uuid4()生成。
    
    Args:
        cls: 被装饰的类。
        
    Returns:
        cls: 添加了标记属性的类。
    """
    cls._is_entity = True
    return cls

def service(cls: Type[T]) -> Type[T]:
    """
    装饰器用于标记一个类为领域驱动设计中的服务（Service）。
    
    服务必须有__init__方法，且有db参数，类型是MemoryDatabase。
    
    Args:
        cls: 被装饰的类。
        
    Returns:
        cls: 添加了标记属性的类。
    """
    cls._is_service = True
    return cls

def domain_event(cls: Type[T]) -> Type[T]:
    """
    装饰器用于标记一个类为领域事件（Domain Event）。
    领域事件必须继承自BaseModel。
    
    Args:
        cls: 被装饰的类。
        
    Returns:
        cls: 添加了标记属性的类。
    """
    if not issubclass(cls, BaseModel):
        raise ValueError('领域事件必须继承自BaseModel')
    cls._is_domain_event = True
    return cls

class MemoryDatabase(BaseModel):
    """
    内存数据库，存储的对象都是BaseModel的子类且有id字段且有entity装饰器
    """
    name: str = 'MemoryDatabase'
    documentation: Optional[str] = None
    data: List[BaseModel] = Field(default_factory=list)
    transaction_data: Optional[List[BaseModel]] = Field(default=None)
    
    def begin_transaction(self):
        """开始事务，保存当前数据的深拷贝作为快照"""
        if self.transaction_data is not None:
            raise ValueError("已经在事务中")
        self.transaction_data = deepcopy(self.data)
    
    def commit(self):
        """提交事务，将事务数据复制到主数据"""
        if self.transaction_data is None:
            raise ValueError("不在事务中")
        self.data = deepcopy(self.transaction_data)
        self.transaction_data = None
    
    def rollback(self):
        """回滚事务，丢弃事务数据，保持原始数据不变"""
        if self.transaction_data is None:
            raise ValueError("不在事务中")
        self.transaction_data = None
    
    def save(self, object: BaseModel) -> None:
        """保存对象"""
        if not hasattr(object, 'id'):
            raise ValueError('保存的对象必须有id字段')
            
        if not hasattr(object.__class__, '_is_entity'):
            raise ValueError('保存的对象必须是被@entity装饰的类')
            
        # 确定要操作的目标列表
        target_list = self.transaction_data if self.transaction_data is not None else self.data
        
        # 检查ID是否重复
        existing = [x for x in target_list if isinstance(x, type(object)) and x.id == object.id]
        if existing:
            # 如果对象已存在，执行更新操作
            self.update(object)
        else:
            # 添加对象的深拷贝
            target_list.append(deepcopy(object))
    
    def update(self, object: BaseModel) -> None:
        """更新对象"""
        if not hasattr(object, 'id'):
            raise ValueError('更新的对象必须有id字段')
            
        if not hasattr(object.__class__, '_is_entity'):
            raise ValueError('更新的对象必须是被@entity装饰的类')
            
        target_list = self.transaction_data if self.transaction_data is not None else self.data
        for i, item in enumerate(target_list):
            if isinstance(item, type(object)) and item.id == object.id:
                target_list[i] = deepcopy(object)
                return
                
        raise ValueError(f'ID为{object.id}的对象不存在，无法更新')
    
    def delete(self, object: BaseModel) -> None:
        """删除指定对象"""
        if not hasattr(object, 'id'):
            raise ValueError('删除的对象必须有id字段')
            
        if not hasattr(object.__class__, '_is_entity'):
            raise ValueError('删除的对象必须是被@entity装饰的类')
            
        target_list = self.transaction_data if self.transaction_data is not None else self.data
        for i, item in enumerate(target_list):
            if isinstance(item, type(object)) and item.id == object.id:
                target_list.pop(i)
                return
                
        raise ValueError(f'ID为{object.id}的对象不存在，删除失败')
    
    def deleteById(self, type: Type, id: str) -> None:
        """根据ID删除指定类型的对象
        
        Args:
            type: 要删除的对象类型，必须是被@entity装饰的类
            id: 要删除的对象ID
            
        Raises:
            ValueError: 如果类型不是被@entity装饰的类，或者指定ID的对象不存在
        """
        if not hasattr(type, '_is_entity'):
            raise ValueError('删除的类型必须是被@entity装饰的类')
            
        target_list = self.transaction_data if self.transaction_data is not None else self.data
        for i, item in enumerate(target_list):
            if isinstance(item, type) and item.id == id:
                target_list.pop(i)
                return
                
        raise ValueError(f'ID为{id}的{type.__name__}对象不存在，删除失败')
    
    def query(self, type: Type, lambda_filter: Callable[[BaseModel], bool]) -> List[BaseModel]:
        """查询对象"""
        if not hasattr(type, '_is_entity'):
            raise ValueError('查询的类型必须是被@entity装饰的类')
            
        # 使用事务数据或原始数据
        target_list = self.transaction_data if self.transaction_data is not None else self.data
        return [deepcopy(item) for item in target_list 
                if isinstance(item, type) and lambda_filter(item)]

class DomainDefinition(BaseModel):
    """类模型，用于描述领域模型、服务类和测试类"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = Field(description='类模型名称')
    domain_classes: List[Type[BaseModel]] = Field(
        default_factory=list, 
        description='List of domain model classes'
    )
    service_classes: List[Type[Any]] = Field(
        default_factory=list, 
        description='List of service classes'
    )
    test_classes: List[Type[unittest.TestCase]] = Field(
        default_factory=list, 
        description='List of test classes'
    )
    correct: bool = Field(default=False, description='类模型是否正确')
    validate_output: str = Field(default='', description='类模型验证输出')
    
    def validate_correct(self) -> bool:
        """验证类模型是否正确"""
        try:
            if not self._validate_classes():
                self.validate_output = "## 类模型验证失败\n\n类定义不符合要求"
                return False
            
            # 创建一个测试套件
            suite = unittest.TestSuite()
            
            # 为每个测试类添加测试用例
            for test_class in self.test_classes:
                test_methods = [m for m in dir(test_class) if m.startswith('test_')]
                for method in test_methods:
                    suite.addTest(test_class(method))
            
            # 捕获输出
            output = io.StringIO()
            with redirect_stdout(output):
                runner = unittest.TextTestRunner(verbosity=2)
                result = runner.run(suite)
            
            # 构建Markdown格式的输出
            markdown_output = ["## 测试结果报告\n"]
            
            # 添加测试输出
            markdown_output.append("### 详细测试输出\n")
            markdown_output.append("```\n")
            markdown_output.append(output.getvalue())
            markdown_output.append("```\n")
            
            # 添加错误信息
            if result.errors:
                markdown_output.append("\n### 错误信息\n")
                for test, error in result.errors:
                    markdown_output.append(f"\n#### {test}\n")
                    markdown_output.append("```\n")
                    markdown_output.append(error)
                    markdown_output.append("```\n")
            
            # 添加失败信息
            if result.failures:
                markdown_output.append("\n### 失败信息\n")
                for test, failure in result.failures:
                    markdown_output.append(f"\n#### {test}\n")
                    markdown_output.append("```\n")
                    markdown_output.append(failure)
                    markdown_output.append("```\n")
            
            # 添加最终结果
            markdown_output.append(f"\n### 最终结果\n\n")
            markdown_output.append(f"测试{'通过 ✅' if result.wasSuccessful() else '失败 ❌'}")
            
            # 合并所有输出
            self.validate_output = "".join(markdown_output)
            self.correct = result.wasSuccessful()
            
            print(self.validate_output)
            return result.wasSuccessful()
            
        except Exception as e:
            self.validate_output = f"## 验证过程出错\n\n```\n{str(e)}\n```"
            self.correct=False
            print(self.validate_output)
            return False
    
    def _validate_classes(self) -> bool:
        """验证所有类是否遵循正确的模式"""
        try:
            # 验证领域模型类
            for cls in self.domain_classes:
                if not issubclass(cls, BaseModel):
                    print(f"错误: 领域模型类 {cls.__name__} 必须继承自 BaseModel")
                    return False
                    
                # 检查实体类的id字段
                if hasattr(cls, '_is_entity'):
                    # 获取类的所有字段
                    fields = cls.model_fields
                    if 'id' not in fields:
                        print(f"错误: 实体类 {cls.__name__} 必须有 id 字段")
                        return False
                    # 检查id字段的类型和默认值
                    id_field = fields['id']
                    if id_field.annotation != str:
                        print(f"错误: 实体类 {cls.__name__} 的 id 字段必须是 str 类型")
                        return False
            
            # 验证服务类
            for cls in self.service_classes:
                if not hasattr(cls, '_is_service'):
                    print(f"错误: 服务类 {cls.__name__} 必须使用 @service 装饰器")
                    return False
                if not hasattr(cls, '__init__'):
                    print(f"错误: 服务类 {cls.__name__} 必须有 __init__ 方法")
                    return False
                init_params = inspect.signature(cls.__init__).parameters
                if 'db' not in init_params:
                    print(f"错误: 服务类 {cls.__name__} 必须在 __init__ 方法中有 db 参数")
                    return False
            
            # 验证测试类
            for cls in self.test_classes:
                if not issubclass(cls, unittest.TestCase):
                    print(f"错误: 测试类 {cls.__name__} 必须继承自 unittest.TestCase")
                    return False
                # 检查否有测试方法
                test_methods = [m for m in dir(cls) if m.startswith('test_')]
                if not test_methods:
                    print(f"警告: 测试类 {cls.__name__} 没有测试方法")
                    return False
            
            return True
            
        except Exception as e:
            print(f"验证类时出错: {str(e)}")
            return False

class ContextInitializer(ABC):
    @abstractmethod
    def initialize(self) -> BoundedContext:
        pass

class BoundedContext(BaseModel):
    """
    上下文类，管理领域模型的实例数据，包括领域实体的实例，服务类的实例
    """
    _root_context: ClassVar[Optional['BoundedContext']] = None  # 类属性
    _kafka: ClassVar[Optional['MemoryKafka']] = None  # kafka类属性
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    domain_definitions: List[DomainDefinition] = Field(default_factory=list,description='领域模型定义')
    name: str = Field(description='限界上下文名称')
    services: Dict[str, Any] = Field(default_factory=dict,description='服务实例')
    database: MemoryDatabase = Field(default_factory=MemoryDatabase,description='内存数据库')
    dependency_contexts: List['BoundedContext'] = Field(default_factory=list,description='依赖的上下文')
    is_root: bool = Field(default=False,description='是否是根上下文')
    initializer: Optional[ContextInitializer] = Field(default=None,description='上下文初始化器')
    
    @classmethod
    def set_root_context(cls, context: 'BoundedContext') -> None:
        cls._root_context = context
        
    @classmethod
    def get_root_context(cls) -> Optional['BoundedContext']:
        return cls._root_context
    
    @classmethod
    def set_kafka(cls, kafka: Optional['MemoryKafka']) -> None:
        """设置Kafka实例"""
        cls._kafka = kafka
    
    @classmethod
    def get_kafka(cls) -> Optional[MemoryKafka]:
        """获取Kafka实例"""
        return cls._kafka
        
    def publish_event(self, topic_name: str, event_data: Any):
        """
        发布领域事件到Kafka
        
        Args:
            topic_name: Kafka主题名称
            event_data: 事件数据，必须是被@domain_event装饰的类的实例
        """
        if not hasattr(event_data.__class__, '_is_domain_event'):
            raise ValueError('事件数据必须是被@domain_event装饰的类的实例')
            
        if self._kafka:
            self._kafka.produce(topic_name, event_data)
        else:
            raise ValueError('Kafka未初始化')
                
    def subscribe_event(self, topic_name: str, handler: Callable):
        """
        订阅领域事件
        
        Args:
            topic_name: Kafka主题名称
            handler: 事件处理函数
        """
        if self._kafka:
            def kafka_handler(message):
                handler(message.value)
            self._kafka.subscribe(topic_name, kafka_handler)
        else:
            raise ValueError('Kafka未初始化')
            
    def get_service_by_name(self, service_name: str) -> Any:
        """
        获取服务实例,如果当前上下文找不到,会到依赖的上下文中查找
        
        Args:
            service_name: 服务名称
            
        Returns:
            Any: 服务实例,如果找不到返回None
        """
        # 先在当前上下文查找
        service = self.services.get(service_name)
        if service:
            return service
            
        # 如果找不到,遍历依赖的上下文查找
        for context in self.dependency_contexts:
            service = context.get_service_by_name(service_name)
            if service:
                return service
                
        return None
        
    def validate_correct(self, visited: Optional[set[str]] = None) -> bool:
        """
        验证所有领域定义及子上下文是否正确（自动处理循环依赖）
        
        Args:
            visited: 已访问的上下文名称集合（内部递归使用）
        """
        # 初始化已访问集合
        visited = visited or set()
        
        # 检查循环依赖
        if self.name in visited:
            return True  # 已访问过的上下文视为验证通过，避免无限递归
            
        # 添加当前上下文到已访问集合
        visited = visited | {self.name}
        
        # 验证当前上下文的领域定义
        current_results = [dd.validate_correct() for dd in self.domain_definitions]
        
        # 递归验证依赖的子上下文（传递已访问集合）
        child_results = [context.validate_correct(visited) for context in self.dependency_contexts]
        
        # 合并所有验证结果
        return all(current_results + child_results)

    

    