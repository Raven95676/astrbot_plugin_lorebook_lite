# astrbot_plugin_lorebook_lite


AstrBot 的 lorebook 插件，支持自定义触发器、变量、逻辑、占位符等。

本插件依赖：
- python-dateutil：用于处理日期时间。
- kwmatcher：用于处理关键词匹配。

## 语法讲解

Version: 0.1.1

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

设定哪类用户可以触发哪些触发器。如果没有设定，默认该类用户可触发所有触发器。

name可以是占位符。

**世界状态：**

```yaml
world_state:
  var_name: "初始值"
  var_name: "初始值"
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

在单个会话中一类用户的状态。

name可以是占位符。

**触发器：**

```yaml
trigger:
  - name: "唯一标识符"
    type: "触发类型"
    match: "匹配规则"
    conditional: "触发条件"
    recursive_scan: true
    recursion_depth: 3
    priority: 10
    block: true
    probability: 0.3
    position: "sys_start"
    content: |
      多行文本
      什么都能塞
    actions:
      - "action_value"
      - "action_value"
```

name: 触发器的唯一标识符。

type: 触发类型，可选值：

- "regex": 正则表达式匹配。
- "keywords": 关键词组匹配，支持逻辑表达式。
  - 使用`&`表示要求多个关键词同时出现
  - 使用`~`表示排除包含特定关键词
  - 例如：`"魔法&咒语~黑魔法&禁术"`表示必须同时包含"魔法"和"咒语"，但不能同时包含"黑魔法"和"禁术"
  - 可以使用`use_logic: false`禁用逻辑表达式解析
- "listener": 每次对话检查条件。

match: 根据 type 指定的匹配规则。
- 对于"keywords"类型，可以使用逗号分隔多个逻辑表达式，如`"A&B~C,X&Y~Z"`

conditional: 触发条件，满足match与probability，但不满足conditional的触发器不会触发。

use_logic: 对于"keywords"类型，控制是否启用逻辑表达式解析，默认为true。其余类型设置无效。

recursive_scan: 是否启用递归扫描。

recursion_depth: 递归扫描的深度。

priority: 触发优先级，数值越高越先触发。

block: 是否阻断后续触发器。

probability: 触发概率（0.0 到 1.0）。

position: 插入位置，可选值，默认"sys_start"：

- "sys_start": 系统提示前。
- "user_start": 用户消息前。
- "sys_end": 系统提示后。
- "user_end": 用户消息后。
- "res_start": 响应开始。
- "res_end": 响应结束。

content: 插入到上下文的内容，支持多行文本。

actions: 执行的操作，列表形式，支持占位符或下一个触发器。actions不能触发自己。

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

作者注释始终在所有trigger结束之后触发。

### 占位符及控制符

**基础信息相关：**

```
{buildin::sender} - 返回发送者名称
{buildin::name} - 返回人设名称（可能存在问题）
```

**时间相关：**

```
{buildin::time}                  - 返回当前世界时间（YYYY-MM-DD HH:MM:SS）
{buildin::time(date)}            - 返回当前世界日期（YYYY-MM-DD）
{buildin::time(time)}            - 返回当前世界时间（HH:MM:SS）
{buildin::time(year)}            - 返回当前世界年份（YYYY）
{buildin::time(month)}           - 返回当前世界月份（MM）
{buildin::time(day)}             - 返回当前世界天（DD）
{buildin::time(hour)}            - 返回当前世界小时（HH）
{buildin::time(minute)}          - 返回当前世界分钟（MM）
{buildin::time(idle_duration)}   - 返回上次用户消息发送以来的时间范围（人性化字符串，如 "2 minutes"）
{buildin::time(advance,XY/XM/XD/Xh/Xm)} - 将时间向前推进 X 年/月/天/小时/分钟，返回设定的时间
{buildin::time(retreat,XY/XM/XD/Xh/Xm)} - 将时间向后推移 X 年/月/天/小时/分钟，返回设定的时间
{buildin::time(set,DATE_STRING)} - 将世界时间设置为指定日期时间，返回设定的时间
```

**随机相关：**

```
{buildin::random(min,max)}      - 返回一个随机整数，范围为 [min, max]
{buildin::random(XdY)}          - 标准骰子表示法（例如 2d6 表示掷两个六面骰并返回总和）
{buildin::random([a,b,c,…])}    - 返回列表 [a,b,c,…] 中的一个随机元素
```

**变量相关：**

```
{var::set(scope.var_name, value)} - 设置变量，scope 可为 "world" 或用户名，无返回值
{var::get(scope.var_name)}        - 获取变量，返回变量内容（若未定义则返回空字符串）
{var::del(scope.var_name)}        - 删除变量，无返回值
{var::add(X + Y)}                 - 加法，X 和 Y 可为变量或数值，返回结果
{var::sub(X - Y)}                 - 减法，X 和 Y 可为变量或数值，返回结果
{var::mul(X * Y)}                 - 乘法，X 和 Y 可为变量或数值，返回结果
{var::div(X / Y)}                 - 除法，X 和 Y 可为变量或数值，返回结果
```

**权限相关：**

```
{perm::add(user_name, trigger_name)}    - 为用户添加触发器权限，无返回值
{perm::remove(user_name, trigger_name)} - 移除用户的触发器权限，无返回值
{perm::check(user_name, trigger_name)}  - 检查用户是否具有触发器权限，返回 "true" 或 "false"
```

**逻辑相关：**

条件表达式支持 ==, !=, >, <, >=, <=, &&（与），||（或）。

```
{logic::if(condition, true, false)} - 逻辑判断，condition为表达式，true为条件为真时返回的值，false为条件为假时返回的值
{logic::and(condition1, condition2, …)} - 逻辑与，返回所有条件都为真时的值
{logic::or(condition1, condition2, …)} - 逻辑或，返回所有条件中至少一个为真时的值
```

> [!important]
> 出于安全考虑，逻辑表达式中只允许使用基本比较操作和变量引用，不支持调用Python内置库。

### 嵌套占位符

本插件支持嵌套占位符，允许在一个占位符内部使用其他占位符，最多支持5层嵌套。例如：

```
{logic::if({var::health} > 50, 健康, 不健康)}
```

首先会处理内部的 `{var::health}` 占位符获取健康值，然后再处理外部的 `logic::if` 逻辑判断。

下面是一个实际应用示例：

```
{logic::if({var::get(global.weather)} == "雨天", 
    今天是{buildin::time(date)}，外面正在下雨，记得带伞, 
    今天是{buildin::time(date)}，天气不错
)}
```

上述占位符会根据全局变量 `weather` 的值来决定返回什么内容，并在返回的内容中再次使用占位符显示当前日期。
