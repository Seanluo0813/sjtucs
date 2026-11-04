# CS2023 分类树：来源与统计口径

访问日期：2026-11-04。

## 官方知识体系

CS2023最终报告（2024年1月版），由ACM、IEEE-CS与AAAI联合制定。

- 报告：https://csed.acm.org/wp-content/uploads/2025/11/CS2023-Report.htm
- DOI：https://doi.org/10.1145/3664191
- 领域索引：https://csed.acm.org/knowledge-areas/

本项目提取报告目录中的17个Knowledge Area及162个Knowledge Unit，保留英文名称、标识、页码与具体章节锚点。SPD-SEP分平台的子节合并为一个KU，与报告汇总表的8个SPD知识单元一致。中文译名及四个导航分组由项目整理。

KA汇总表的CS Core学时合计270。数学与统计基础MSF为55、软件开发基础SDF为43，合计98，比例98/270=36.296...%，显示为36.3%。FPL为22个KU/21小时，MSF为5个KU/55小时。KU数不能替代学习难度或学时。

知识单元的CS Core和KA Core原表值按原字符串保留。括号内其他KA学时可能已在对应领域计算，不能再次跨行求和；未列出独立学时不表示内容不重要。筛选“本KA有CS Core学时”按字符串开头独立学时大于0判断，不把仅来自其他KA的复用学时计入本KA。

## 上海交通大学具体课程

2026级计算机科学与技术课程设置一览表：
https://mentor.sjtu.edu.cn/jwc/plans/view/4E34A4CBEA26FFC1E065F8163EE1DCCC/?render=1

提取50门与本项目领域相关的课程，保留课程代码、名称、学分、建议年级、学期与课程性质。该校内页面说明：培养方案和毕业要求以学院正式要求为准，当前页面仅供参考。本站不把此表作为选课资格或毕业认定依据。

具体课程存在性和字段来自校方页面；KU与课程的对应由项目基于名称/主题整理，属于建议学习入口，不是官方课程大纲覆盖认定。缺少可靠对应的KU留空；HCI中未凭课程名称确认的条目不填写，以免把VR或可视化自动当作人机交互完整覆盖。

## 复现

项目根目录运行：

```bash
python3 -m pip install lxml
python3 src/fetch_sources.py
python3 src/build_tree_data.py
python3 src/check_site.py
```

源HTML会保存至`data/raw/`，该目录不随Git上传。网页使用已整理的本地`data.js`，不依赖实时抓取或网络API。
