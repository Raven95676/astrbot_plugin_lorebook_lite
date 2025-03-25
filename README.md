# astrbot_plugin_lorebook_lite

> [!caution]
> run_code块允许执行任意代码，请勿随意导入带有run_code块的lorebook。

AstrBot 的 lorebook 插件。

## 语法讲解

### 基础数据类型

```yaml
"字符串"   # 字符串类型
12345     # 数字类型
true      # 布尔类型
[]        # 列表类型
```

### 块

**全局设置：**

```yaml
lores_base:
    scan_depth: 2
    recursive_scan: true
    recursion_depth: 3
```

这规定了默认行为。

scan_depth: 扫描深度，表示扫描多少条聊天记录。

recursive_scan: 是否启用递归扫描，允许世界书条目触发其他条目。

recursion_depth: 递归扫描的深度，控制递归层数。

**权限相关：**

```yaml
permissions:
  - name: "用户名"
    triggers:
      - "trigger_name1"
      - "trigger_name2"
  - name: "用户名"
    triggers:
      - "trigger_name3"
      - "trigger_name4"
```

设定哪些用户可以触发哪些触发器。如果没有设定，默认该用户可触发所有触发器。

注：不止用户名，塞占位符也行。

**世界状态：**

```yaml
world_state:
  - var_name: "初始值"
  - var_name: "初始值"
```

键值对形式，存储单个会话中的全局状态变量。

var_name: 变量名，值为其初始值。

**用户状态：**

```yaml
user_state:
  - name: "用户名"
    variables:
      - var_name: "初始值"
      - var_name: "初始值"
  - name: "用户名"
    variables:
      - var_name: "初始值"
      - var_name: "初始值"
```

在单个会话中的用户状态。

**触发器：**

```yaml
trigger:
  - name: "唯一标识符"
    type: "触发类型"
    match: "匹配规则"
    recursive_scan: true
    recursion_depth: 3
    priority: 10
    block: true
    probability: 0.3
    position: "sys_start"
    content: |
      多行文本
      什么都能塞
```

name: 触发器的唯一标识符。

type: 触发类型，可选值：

- "regex": 正则表达式匹配。
- "keywords": 关键词组匹配。
- "listener": 每次对话检查条件。

match: 根据 type 指定的匹配规则。

recursive_scan: 是否启用递归扫描。

recursion_depth: 递归扫描的深度。

priority: 触发优先级，数值越高越先触发。

block: 是否阻断后续触发器。

probability: 触发概率（0.0 到 1.0）。

position: 插入位置，可选值：

- "sys_start": 系统提示前。
- "user_start": 用户消息前。
- "sys_end": 系统提示后。
- "user_end": 用户消息后。

content: 插入到上下文的内容，支持多行文本。

**代码执行器：**

```yaml
code_run:
  - name: "唯一标识符"
    type: "触发类型"
    match: "匹配规则"
    priority: 10
    block: true
    probability: 0.3
    code: |
      多行Python代码
      什么都能塞
```

name: 代码执行器的唯一标识符。

type: 触发类型，同 trigger。

match: 匹配规则，同 trigger。

priority: 触发优先级，同 trigger。

block: 是否阻断后续触发器。

probability: 触发概率（0.0 到 1.0）。

code: 执行的 Python 代码，支持多行。

特殊说明: 
- code_run 的`return`会存储为变量，变量名为 code_run 的 name 值。
- code_run 总是优先于 trigger 执行。



**作者注释：**

```yaml
authors_note:
  - content: "这是一条作者注释"
    probability: 0.3
    position: "sys_start"
```

content: 作者注释的内容。

probability: 插入概率（0.0 到 1.0）。

position: 插入位置，同 trigger。

### 占位符及控制符

**基础信息相关：**

```
{buildin::sender} - 返回发送者名称
{buildin::name} - 返回人设名称（可能存在问题）
```

**时间相关：**

```
{buildin::time} - 返回当前世界时间（YYYY-MM-DD HH:MM）
{buildin::time(date)} - 返回当前世界日期（YYYY-MM-DD）
{buildin::time(time)} - 返回当前世界时间（HH:MM）
{buildin::time(year)} - 返回当前世界年份（YYYY）
{buildin::time(month)} - 返回当前世界月份（MM）
{buildin::time(day)} - 返回当前世界天（DD）
{buildin::time(hour)} - 返回当前世界小时（hh）
{buildin::time(minute)} - 返回当前世界分钟（mm）
{buildin::time(idle_duration)} - 返回表示上次用户消息发送以来的时间范围的人性化字符串
{buildin::time(advance,XY/XM/XD/Xh/Xm)} - 将时间向前推（也就是加）X年/月/天/小时/分钟
{buildin::time(retreat,XY/XM/XD/Xh/Xm)} - 将时间向后推（也就是减）X年/月/天/小时/分钟
```

**随机相关：**

```
{buildin::random(min,max)} - 返回一个随机整数，范围为(min, max)
{buildin::random(XdY)} - 标准骰支持
{buildin::random([a,b,c,…])} - 返回列表[a,b,c,…]中一个随机元素
```

**变量相关：**

```
{var::set(var_name, value)} - 设置变量，返回值为value
{var::get(var_name)} - 获取变量，返回变量内容
{var::clear(var_name)} - 清空变量，没有返回值
{var::add(var_name+X)} - 变量加法，X为整数或字符串，返回结果
{var::sub(var_name-X)} - 变量减法，X为整数或字符串，返回结果
{var::mul(var_name*X)} - 变量乘法，参与运算的必须是整数，字符串会报错，返回结果
{var::div(var_name/X)} - 变量除法，参与运算的必须是整数，字符串会报错，返回结果
```

**逻辑相关：**

条件表达式支持 ==, >, < ，>=, <=, !=运算符。

条件表达式示例：{var::get(var_name)} == {var::get(var_name)}

```
{logic::if(condition, true, false)} - 逻辑判断，condition为表达式，true为条件为真时返回的值，false为条件为假时返回的值
{logic::and(condition1, condition2, …)} - 逻辑与，返回所有条件都为真时的值
{logic::or(condition1, condition2, …)} - 逻辑或，返回所有条件中至少一个为真时的值
```

逻辑占位符示例：{logic::if({var::get(var_name)} == 5, "是的", "不是")}
