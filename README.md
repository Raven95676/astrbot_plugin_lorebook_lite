# astrbot_plugin_lorebook_lite

AstrBot 的 lorebook 插件，支持自定义触发器、变量、逻辑、占位符等。

本插件依赖：

- python-dateutil：用于处理日期时间
- kwmatcher：用于处理关键词匹配

灵感来源：[chatluna - 编写预设 - 世界书](https://chatluna.chat/guide/preset-system/write-preset.html)

本插件在复刻其部分特性的同时添加了大量拓充。

## 使用方法

编写你自己的Lorebook yaml文件，然后放到`data/lorebooks/`目录下。在插件配置中输入需要激活的yaml文件名（不含`.yaml`）。

## 语法讲解

### 块

**世界状态：**

```yaml
world_state:
  var_name: "初始值"
  var_name: "初始值"
```

键值对形式，存储单个会话中的全局状态变量。若键名重复，保留最后一个键。

如果存在`world_time`,则会尝试采用该值作为世界初始时间（YYYY-MM-DD hh:mm）。

var_name: 变量名，值为其初始值。

所有用户共用world_state。不同会话的world_state自动隔离。

**用户状态：**

```yaml
user_state:
  - name: "变量组名"
    variables:
      - var_name: "初始值"
      - var_name: "初始值"
  - name: "变量组名"
    variables:
      - var_name: "初始值"
      - var_name: "初始值"
```

在单个会话中存储用户的状态。若键名重复，保留最后一个键。

每个用户的状态自动隔离。不同会话的user_state自动隔离。

**触发器：**

> [!note]
> 一个触发器最多通过 actions 触发 25 个其他触发器
>
> 触发器内容暂时不能触发其他触发器

```yaml
trigger:
  - name: "唯一标识符"
    type: "触发类型"
    match: "匹配规则"
    conditional: "触发条件，应为逻辑占位符"
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

- "regex": 正则表达式匹配
- "keywords": 关键词组匹配，支持逻辑表达式
  - 使用`&`表示要求多个关键词同时出现
  - 使用`~`表示排除包含特定关键词
  - 例如：`"魔法&咒语~黑魔法&禁术"`表示必须同时包含"魔法"和"咒语"，但不能同时包含"黑魔法"和"禁术"
  - 可以使用`use_logic: false`禁用逻辑表达式解析
- "listener": 每次对话检查条件

match: 根据 type 指定的匹配规则。

- 对于"keywords"类型，可以使用逗号分隔多个逻辑表达式，如`"A&B~C,X&Y~Z"`，半角单引号`'`或半角双引号`"`内的逗号不会触发切分。

conditional: 触发条件，满足 match 与 probability，但不满足 conditional 的触发器不会触发。理论上支持多行（指的是把一个逻辑表达式拆成多行去写）。

use_logic: 对于"keywords"类型，控制是否启用逻辑表达式解析，默认为 true。其余类型设置无效。

priority: 触发优先级，数值越高越先触发。

block: 是否阻断后续触发器，设为 true 时会在此触发器处理后停止处理其他触发器。

probability: 触发概率（0.0 到 1.0），用于控制触发器随机触发的概率。

conditional: 条件表达式，用于设置更复杂的触发条件，支持逻辑表达式。

position: 插入位置，可选值，默认"sys_start"：

- "sys_start": 系统提示前
- "user_start": 用户消息前
- "sys_end": 系统提示后
- "user_end": 用户消息后

content: 插入到上下文的内容，支持多行文本和占位符。

actions: 执行的操作，列表形式，支持占位符或触发其他触发器。注意：

- actions 中不能触发自己
- actions 中的触发器将无视触发条件直接执行

## 作者注释

```yaml
authors_note:
  - content: "这是一条作者注释"
    probability: 0.3
    position: "sys_start"
```

content: 作者注释的内容，支持占位符。

probability: 插入概率（0.0 到 1.0）。

position: 插入位置，同触发器 position。

作者注释始终在所有 trigger 处理完成后触发，不受 block 属性影响。

## 占位符


占位符语法格式为`{namespace::function_name(arg1, arg2, …)}`，其中`namespace`为命名空间，`function_name`为函数名，`arg1, arg2, …`为参数列表。

占位符匹配使用的正则表达式为`\{([a-zA-Z0-9_]+)::([a-zA-Z0-9_]+)(?:\(([^(){}]*)\))?}`，所以参数列表内不得包含半角括号`()`。非嵌套占位符的情况下，参数列表内不得出现半角大括号`{}`。

半角单引号`'`或半角双引号`"`内的逗号不会触发切分。

编写占位符时建议提前使用验证工具测试是否能够一层一层地匹配（先匹配内层，移除内层后匹配外层）。

如：[在线正则表达式测试](https://tool.oschina.net/regex)。


**基础信息相关：**

```
{buildin::sender} - 返回发送者ID
{buildin::sender_name} - 返回发送者名称
```

**时间相关：**

```
{buildin::time}                  - 返回当前世界时间（YYYY-MM-DD hh:mm）
{buildin::time(date)}            - 返回当前世界日期（YYYY-MM-DD）
{buildin::time(time)}            - 返回当前世界时间（hh:mm）
{buildin::time(year)}            - 返回当前世界年份（YYYY）
{buildin::time(month)}           - 返回当前世界月份（MM）
{buildin::time(day)}             - 返回当前世界天（DD）
{buildin::time(hour)}            - 返回当前世界小时（hh）
{buildin::time(minute)}          - 返回当前世界分钟（mm）
{buildin::time(real_idle)}       - 返回上次用户消息发送以来的时间范围（人性化字符串，如 "5分钟前"）
{buildin::time(world_idle)}      - 返回上次用户消息发送以来的世界时间范围（人性化字符串，如 "5分钟前"）
{buildin::time(+XY/XM/XD/Xh/Xm)} - 将时间向前推进 X 年/月/天/小时/分钟，返回设定的时间
{buildin::time(-XY/XM/XD/Xh/Xm)} - 将时间向后推移 X 年/月/天/小时/分钟，返回设定的时间
{buildin::time(DATE_STRING)}     - 将世界时间设置为指定日期时间，返回设定的时间
```

**随机相关：**

> [!note]
> 支持的骰子表达式:
> - 标准格式: XdY (投X个Y面骰)
> - 带修正值: XdY+Z, XdY-Z
> - 保留高位: XdYkZ (投X个Y面骰并保留最高的Z个)
> - 保留低位: XdYlZ (投X个Y面骰并保留最低的Z个)
> - 上界: XdYuZ (当骰子结果大于Z时，按Z计算)
> - 下界: XdYbZ (当骰子结果小于Z时，按Z计算)
> - 重投累加: XdYrZ (当骰子结果大于等于Z时，重新投一个骰子并累加)
> - 重投: XdYtZ (当骰子结果小于等于Z时，重新投一个骰子)
> - 优势: XdYadv (投2X个Y面骰，每两个取较大值)
> - 劣势: XdYdis (投2X个Y面骰，每两个取较小值)
> - 组合表达式: 2d6+1d4+3, 3d20k2-1（不是按逗号组合）

```
{buildin::random(min,max)}      - 返回一个随机整数，范围为 [min, max]
{buildin::random(XdY)}          - 骰子表达式
{buildin::random(a,b,c,…)}      - 返回 a,b,c,… 中的一个随机元素
```

**变量相关：**

> [!important]
> 在使用set之前，变量不会保存。变量只能通过get取值
>
> 比如需要实现将某个变量取出来然后加1然后保存，你需要这样写：
>
> `{var::set(draw_stats.user_draws,{var::add({var::get(draw_stats.user_draws)},1)})}`
>
> 当然还可以这样写……
>
> ```
> {var::set(draw_stats.user_draws,
>   {var::add({var::get(draw_stats.user_draws)},1)}
> )}
> ```

```
{var::set(scope.var_name, value)} - 设置变量，scope 可为 "world" 或用户名，返回设置的值
{var::get(scope.var_name)}        - 获取变量，返回变量内容（若未定义则返回空字符串）
{var::del(scope.var_name)}        - 删除变量，无返回值
{var::add(X + Y)}                 - 加法，X 和 Y 可为变量或数值，返回结果
{var::sub(X - Y)}                 - 减法，X 和 Y 可为变量或数值，返回结果
{var::mul(X * Y)}                 - 乘法，X 和 Y 可为变量或数值，返回结果
{var::div(X / Y)}                 - 除法，X 和 Y 可为变量或数值，返回结果
```

**逻辑相关：**

条件表达式(condition)支持 ==, !=, >, <, >=, <=, &&（与），||（或）。

```
{logic::if(condition, true_value, false_value)} - 逻辑判断，condition为表达式，true_value为条件为真时返回的值，false_value为条件为假时返回的值
{logic::and(condition1, condition2, …)} - 逻辑与，返回所有条件都为真时的值
{logic::or(condition1, condition2, …)} - 逻辑或，返回所有条件中至少一个为真时的值
{logic::not(condition)} - 逻辑非，返回条件取反后的值
```

## 嵌套占位符

本插件支持简单情况的嵌套占位符，允许在一个占位符内部使用其他占位符，最多支持 25 层嵌套。例如：

```
{logic::if({var::get(world.health)} > 50, 健康, 不健康)}
```

首先会处理内部的 `{var::get(world.health)}` 占位符获取健康值，然后再处理外部的 `logic::if` 逻辑判断

下面是一个实际应用示例：

```
{logic::if({var::get(world.weather)} == 雨天,
    今天是{buildin::time(date)}，外面正在下雨，记得带伞,
    今天是{buildin::time(date)}，天气不错
)}
```

上述占位符会根据全局变量 `weather` 的值来决定返回什么内容，并在返回的内容中再次使用占位符显示当前日期。
