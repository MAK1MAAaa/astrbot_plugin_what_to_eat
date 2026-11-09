# 上游来源与适配记录

- 仓库：[Sisyphbaous-DT-Project/astrbot_plugin_what_to_eat](https://github.com/Sisyphbaous-DT-Project/astrbot_plugin_what_to_eat)
- 上游作者：C₂₂H₂₅NO₆
- 上游元信息版本：`1.3.0_beta1`
- 固定提交：[11fc4c62af961717a2365cfbb3a681037f7f6f49](https://github.com/Sisyphbaous-DT-Project/astrbot_plugin_what_to_eat/commit/11fc4c62af961717a2365cfbb3a681037f7f6f49)
- 调查日期：2026-10-13；适配日期：2026-10-14
- 适配作者：makima；本目录版本：`v1.0.1`
- 适配仓库：[MAK1MAAaa/astrbot_plugin_what_to_eat](https://github.com/MAK1MAAaa/astrbot_plugin_what_to_eat)
- 许可证：保留该提交的原始 [MIT LICENSE](LICENSE)，包括上游版权声明。

## 同类项目调查

已通过 GitHub 公共仓库搜索 `astrbot 吃什么`、`astrbot eat`，并核对以下项目说明。现有实现中，指定仓库直接包含本次确认的“随机推荐或复读”玩法，因此采用它的固定提交进行适配。

| 项目 | 核对到的功能 | 本次用途 |
| --- | --- | --- |
| [指定上游](https://github.com/Sisyphbaous-DT-Project/astrbot_plugin_what_to_eat) | 关键词包含匹配、推荐／复读概率、食物库、配图、次数保护与复读冷却。 | 本目录代码来源。 |
| [Newbie-L/astrbot_plugin_eatdrink](https://github.com/Newbie-L/astrbot_plugin_eatdrink) | 吃、喝及组合推荐，支持按类别选择。 | README 对比。 |
| [Venti-XingLanCiJiang-BiLiBiLi/astrbot_plugin_what_to_eat](https://github.com/Venti-XingLanCiJiang-BiLiBiLi/astrbot_plugin_what_to_eat) | 菜品管理、单道／多道推荐、导入导出、WebUI 页面和程序化菜单接口。 | README 对比。 |

## 复用与修改

从固定提交引入入口、食物管理、回复器、次数保护、图片管理、配置、元信息和许可证。保留上游默认食物清单、六种推荐模板、固定复读／空库提示、关键词包含匹配及图片命名规则。

- 入口采用标准 AstrBot 事件，保留附加 handler 参数兼容；加入自身消息和已停止事件过滤，以默认优先级 0 运行，让本合集优先级 10 的 1d 入口先处理。命中后停止事件、禁止默认 LLM，并直接发送一次结果；发送失败只记录日志。
- 重构次数与冷却记录，两个开关独立生效。计数键包含平台实例和群聊／私聊类型；使用单调时间、滑动窗口、限定长度的时间戳队列、过期清理及最多 2048 个会话。复读记录在第一次等待前完成，卸载时清空。
- 配图从官方插件数据目录解析上传路径，兼容上游插件目录中的旧文件和手工 `images/`。合并时复制列表并按路径去重，跳过缺失、不可读及格式扩展名不受支持的文件；配置扩展名使用不带点的形式。
- 关键词去除首尾空白并去重；缺省配置仍提供 50 项默认食物，显式空库保留；概率非法时回退默认值，保护参数按有效范围处理。
- 默认概率调整为 70% 推荐、30% 复读；配置缺省与非法概率回退均使用 `0.7`。
- `v1.0.1` 随仓库提供 20 张美食配图，启动日志记录已加载的配图数量。
- 包入口延迟加载插件类并保留 `WhatToEatPlugin` 导出；新增中文说明、离线测试和空依赖清单，更新根目录菜单。

插件标识保持 `astrbot_plugin_what_to_eat`，安装目录及既有配置标识继续沿用。元信息 `repo` 指向上述独立适配仓库，上游链接与固定版本记录保存在本文件中。

## AstrBot 接口核对

- [4.5.7 的数据目录接口](https://github.com/AstrBotDevs/AstrBot/blob/v4.5.7/astrbot/core/star/star_tools.py)：确认 `StarTools.get_data_dir(plugin_name)` 可获取插件数据目录。
- [标准消息事件接口](https://github.com/AstrBotDevs/AstrBot/blob/fb49dfa54bb248e263f1db14cfc553b2cb0655c3/astrbot/core/platform/astr_message_event.py)：核对平台实例 ID、停止事件、直接发送消息及 `should_call_llm(True)` 禁止默认 LLM 请求的语义。
- [官方配置上传服务](https://github.com/AstrBotDevs/AstrBot/blob/fb49dfa54bb248e263f1db14cfc553b2cb0655c3/astrbot/dashboard/services/config_service.py)：核对上传结果为相对的 `files/...` 路径，文件根目录位于插件数据目录。
- [官方文件配置组件](https://github.com/AstrBotDevs/AstrBot/blob/fb49dfa54bb248e263f1db14cfc553b2cb0655c3/dashboard/src/components/shared/FileConfigItem.vue)：核对图片扩展名、上传与配置保存接口。

离线测试以这些接口合同构建模拟事件，不代表 AstrBot WebUI、平台适配器或真实收发已联调。
