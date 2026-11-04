from pathlib import Path
from lxml import html
import json,re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT
RAW=ROOT/'data/raw'
REPORT='https://csed.acm.org/wp-content/uploads/2025/11/CS2023-Report.htm'
COURSES='https://mentor.sjtu.edu.cn/jwc/plans/view/4E34A4CBEA26FFC1E065F8163EE1DCCC/?render=1'
def text(n): return ' '.join(n.text_content().split())
s=html.fromstring((RAW/'cs2023.html').read_bytes())
tables=[t for t in s.xpath('//table') if text(t).startswith('Knowledge Unit') and 'CS Core' in text(t)]
summary=next(t for t in s.xpath('//table') if text(t).startswith('Knowledge Area # Knowledge'))
zh=['人工智能','算法基础','体系结构与组成','数据管理','程序设计语言基础','图形学与交互技术','人机交互','数学与统计基础','网络与通信','操作系统','并行与分布式计算','软件开发基础','软件工程','安全','社会、伦理与职业','系统基础','专用平台开发']
groups={'基础与理论':['AL','MSF','FPL','SDF'],'系统与计算':['AR','OS','SF','NC','PDC'],'数据与智能':['AI','DM','GIT'],'人与软件':['HCI','SE','SEC','SEP','SPD']}
desc=['研究如何让机器搜索、推理和学习，并理解智能技术的社会影响。','以数据结构、算法策略与复杂性分析，回答问题能否被高效求解。','理解数据在硬件中的表示，以及处理器、存储与输入输出的组织。','组织、存储、查询与保护数据，理解数据生命周期。','理解程序设计范式、类型系统以及程序如何被翻译与执行。','用计算生成、处理与呈现视觉内容，连接图像、建模和交互。','围绕人的目标、能力与差异，设计和评估可用、可访问的系统。','为计算建立离散结构、概率、统计、线性代数与微积分基础。','理解联网应用、可靠传输、路由、安全与移动通信。','理解资源管理、并发、进程、存储、文件系统与保护机制。','让计算任务在多个执行单元上沟通、协调，并衡量性能。','学习编程概念、数据结构、基本算法与可靠的软件开发实践。','在团队与工程约束下完成需求、设计、实现、验证和持续维护。','识别威胁，建立安全的编码、密码、工程与治理方法。','理解计算的社会背景、职业责任、隐私、公平和可持续性。','以整体视角分析计算机系统的资源、性能、可靠性与安全。','面向Web、移动、机器人、嵌入式、游戏等平台构建软件。']
areas=[]
for i,row in enumerate(summary.xpath('.//tr')[1:-1]):
 c=[text(x) for x in row.xpath('./td|./th')]
 areas.append(dict(id=c[0],name=zh[i],english=c[1],expectedUnits=int(c[2]),hours=int(c[3]),kaHours=int(c[4]) if c[4].isdigit() else None,group=next(g for g,ids in groups.items() if c[0] in ids),description=desc[i],units=[]))
lookup={a['id']:a for a in areas}
for a in s.xpath('//a'):
 t=text(a)
 m=re.match(r'^((?:AI|AL|AR|DM|FPL|GIT|HCI|MSF|NC|OS|PDC|SDF|SE|SEC|SEP|SF|SPD)-[^: .]+)(?::\s*(.*?))?\.*\s+(\d+)$',t)
 if not m:continue
 code,name,page=m.groups()
 if '/' in code:continue
 area=lookup[code.split('-')[0]]
 if any(u['id']==code for u in area['units']):continue
 name=(name or ('Calculus' if code=='MSF-Calculus' else code)).rstrip('. ')
 area['units'].append(dict(id=code,name=name,page=int(page),source=REPORT+a.get('href',''),coreHours='',kaHours=''))
lookup['SPD']['units'].append(dict(id='SPD-SEP',name='Society, Ethics, and the Profession',page=309,source=REPORT+'#_Toc166704059',coreHours='Included in SEP hours',kaHours=''))
# Deterministic aliases reconcile TOC headings with the literal hour-table labels.
# No fuzzy matching: every KU must have exactly one verified table row.
def normalized_label(value):
 return re.sub(r'[^a-z0-9]+',' ',value.lower().replace('&','and')).strip()
hour_aliases={
 'AL-Complexity':'Complexity Analysis',
 'DM-Data':'The Role of Data',
 'DM-Core':'Core Database Systems Concepts',
 'FPL-Run-Time':'Runtime Behavior and Systems',
 'GIT-Immersion':'Immersion (MR, AR, VR)',
 'HCI-User':'Understanding the User',
 'NC-Mobility':'Mobility Support',
 'SEP-History':'History',
 'SF-SEP':'Society, Ethics, and Profession',
 'SPD-Common':'Common Aspects',
 'SPD-SEP':'SPD-SEP',
}
hour_issues=[]
hour_audit=[]
assert len(areas)==len(tables)==17
for area,table in zip(areas,tables):
 rows=[]
 for row in table.xpath('.//tr')[1:]:
  cells=[text(c) for c in row.xpath('./td|./th')]
  if len(cells)>=2 and not cells[0].startswith('Total'):rows.append(cells)
 for u in area['units']:
  label=hour_aliases.get(u['id'],u['name'])
  matches=[r for r in rows if normalized_label(r[0])==normalized_label(label)]
  if len(matches)!=1:
   hour_issues.append(dict(unit=u['id'],lookupLabel=label,matches=len(matches)))
   continue
  row=matches[0]
  u['coreHours']=row[1]
  # AR has a blank layout column; the KA field is the final cell.
  # Two-cell SEP rows are merged and have no independent KA value.
  u['kaHours']=row[-1] if len(row)>=3 else ''
  u['hourTableLabel']=row[0]
  u['isCore']=bool(re.match(r'^(?:[1-9]|0\.[1-9])',u['coreHours']))
  hour_audit.append(dict(unit=u['id'],label=row[0],core=u['coreHours'],ka=u['kaHours']))
print(json.dumps({'hourMatchingIssues':hour_issues,'uniqueHourMatches':len(hour_audit)},ensure_ascii=False))
assert not hour_issues, 'Unmatched or ambiguous hour-table rows; inspect hourMatchingIssues before publication'
assert len(hour_audit)==162
translations={
'AI':'基本问题|搜索|知识表示与推理基础|机器学习|应用与社会影响|逻辑表示与推理|概率表示与推理|规划|智能体与认知系统|自然语言处理|机器人|感知与计算机视觉',
'AL':'基础数据结构与算法|算法策略|复杂性|计算模型与形式语言|社会、伦理与职业',
'AR':'数字逻辑与数字系统|机器级数据表示|汇编级机器组织|存储层次结构|接口与通信|功能组织|性能与能效|异构架构|安全处理器架构|量子架构|可持续性议题',
'DM':'数据作用与生命周期|数据库系统核心概念|数据建模|关系数据库|查询构建|查询处理|数据库内部机制|NoSQL系统|数据安全与隐私|数据分析|分布式数据库与云计算|半结构化与非结构化数据库|社会、伦理与职业',
'FPL':'面向对象编程|函数式编程|逻辑编程|Shell脚本|事件驱动与响应式编程|并行与分布式计算|面向切面编程|类型系统|系统执行与内存模型|语言翻译与执行|程序抽象与表示|语法分析|编译语义分析|程序分析与分析器|代码生成|运行时行为与系统|高级编程结构|语言实用性|形式语义|形式化开发方法|语言设计原则|社会、伦理与职业',
'GIT':'基本概念|可视化|应用渲染技术|几何建模|着色与高级渲染|计算机动画|仿真|沉浸技术|交互|图像处理|实体与物理计算|社会、伦理与职业',
'HCI':'理解用户|设计中的责任|可访问性与包容设计|设计评估|系统设计|社会、伦理与职业',
'MSF':'离散数学|概率|统计|线性代数|微积分',
'NC':'网络基础|联网应用|可靠性支持|路由与转发|单跳通信|网络安全|移动性|新兴主题',
'OS':'操作系统的作用|操作系统原理|并发|保护与安全|调度|进程模型|内存管理|设备管理|文件系统接口与实现|高级文件系统|虚拟化|实时与嵌入式系统|容错|社会、伦理与职业',
'PDC':'并行程序|通信|协调|评估|并行算法',
'SDF':'编程基本概念与实践|基本数据结构|算法|软件开发实践|社会、伦理与职业',
'SE':'团队协作|工具与环境|产品需求|软件设计|软件构建|软件验证与确认|重构与演化|软件可靠性|形式方法',
'SEC':'安全基础|社会、伦理与职业|安全编码|密码学|安全分析、设计与工程|数字取证|安全治理',
'SEP':'社会背景|伦理分析方法|职业伦理|知识产权|隐私与公民自由|沟通|可持续性|计算历史|计算经济|安全政策、法律与计算机犯罪|多样性、公平、包容与可访问性',
'SF':'计算机系统概览|基本概念|资源管理|系统性能|性能评估|系统可靠性|系统安全|系统设计|社会、伦理与职业',
'SPD':'共性与共同关注|Web平台|移动平台|机器人平台|嵌入式平台|游戏平台|交互计算平台|社会、伦理与职业'}
coursemap={
'AI':'CS3317 CS3308 CS3316 CS4314 CS3340 CS4313', 'AL':'CS0501 CS2308 CS3313 CS3341 CS4308', 'AR':'CS2307 CS2305 CS2306 CS3346', 'DM':'CS3321 CS3322 CS4303 CS3319', 'FPL':'CS1501 CS2301 CS3342', 'GIT':'CS3310 CS3320 CS3327','HCI':'CS3327 CS3320','MSF':'CS2501 CS2304 MATH1205 MATH1207 MATH1201 MATH1202','NC':'CS3311 ICE3307 CS3350','OS':'CS2310 CS2303 CS3347','PDC':'CS4302 CS3328 CS3301','SDF':'CS1501 CS0501 NIS1336','SE':'CS3331 CS4315','SEC':'CS3314 CS3312 CS3325','SEP':'CS3309','SF':'CS2307 CS2305 CS2310','SPD':'CS3349 CS3327 CS3351 CS4319'}
# Editorial KU-to-course suggestions based only on public course names.
# The explicit KU lists below are deliberate; no area-level fallback is permitted.
specific={}
mapping_reasons={}
def suggest(unit_ids, course_ids, reason):
 for unit_id in unit_ids.split():
  assert unit_id not in specific, 'Duplicate explicit mapping: '+unit_id
  specific[unit_id]=course_ids.split() if course_ids else []
  mapping_reasons[unit_id]=reason

suggest('AI-Introduction AI-KRR','CS3317','人工智能课程名称与基础智能问题、知识表示主题相近。')
suggest('AI-Search','CS3317 CS2308','人工智能与算法课程可作为搜索策略的入门线索。')
suggest('AI-ML','CS3308','机器学习课程与该单元主题直接同名。')
suggest('AI-NLP','CS4314','自然语言处理课程与该单元主题直接同名。')
suggest('AI-Vision','CS3340','计算机视觉课程与视觉感知主题直接相关。')
suggest('AI-Probability','CS3317 MATH1207','概率统计提供数学先修，人工智能提供概率推理的后续学习入口。')
suggest('AI-SEP','CS3309','计算机伦理学提供社会影响讨论的学习入口，AI专属内容仍需核查。')
suggest('AI-Robotics','CS3349','无人系统实践是机器人相关实践线索，不能据此认定覆盖机器人单元。')
suggest('AL-Foundational','CS0501','数据结构课程与基础数据结构及算法主题直接相关。')
suggest('AL-Models','CS3313','计算理论课程与计算模型、形式语言主题相近。')
suggest('AL-Complexity','CS2308 CS4308','算法与复杂性、计算复杂性均在课程名称中明确涉及复杂性。')
suggest('AL-Strategies','CS2308 CS3341','算法与复杂性和高等算法可作为算法策略的学习入口。')
suggest('MSF-Discrete','CS2501','离散数学课程与该单元直接同名。')
suggest('MSF-Probability MSF-Statistics','MATH1207','概率统计课程在名称中同时明确列出概率与统计。')
suggest('MSF-Linear','MATH1205','线性代数课程与该单元直接同名。')
suggest('MSF-Calculus','MATH1201 MATH1202','高等数学I与II为微积分相关的基础学习入口。')
suggest('GIT-Visualization','CS3320','数据可视化与可视分析课程名称直接包含可视化。')
suggest('GIT-Fundamentals','CS3310','计算机图形学提供图形学基础的学习入口。')
suggest('GIT-Immersion','CS3327','虚拟现实与增强显示技术与沉浸技术主题直接相关。')
suggest('GIT-Rendering GIT-Modeling GIT-Shading','CS3310','计算机图形学可作为渲染与建模相关主题的入口，具体子主题需核课程大纲。')
suggest('FPL-OOP','CS1501','C++程序设计课程可作为面向对象编程入口，覆盖深度须查课程大纲。')
suggest('FPL-Translation','CS2301','编译原理课程与语言翻译主题直接相关。')
suggest('FPL-Types','CS3342','程序语言理论可作为类型系统的学习入口，具体覆盖待课程大纲核实。')
suggest('FPL-Syntax FPL-Semantics FPL-Code','CS2301','编译原理是语法分析、编译语义分析与代码生成的相关学习入口。')
suggest('SDF-Fundamentals','CS1501','程序设计思想与方法课程与基础编程主题直接相关。')
suggest('SDF-Data-Structures SDF-Algorithms','CS0501','数据结构课程提供基础数据结构与相关算法学习入口。')
suggest('SDF-Practices','NIS1336','计算机编程实践与软件开发实践的实践属性直接相关。')
suggest('AR-Logic AR-Representation AR-Assembly AR-IO','CS2307','计算机组成课程是硬件组织相关基础主题的学习入口；具体KU覆盖未核验。')
suggest('AR-Memory AR-Organization','CS2307 CS2305','计算机组成与系统结构课程是存储层次、功能组织的相关学习入口。')
suggest('AR-Performance-Energy','CS2305','系统结构课程提供性能相关学习入口，能效部分尚未核验。')
suggest('AR-Quantum','CS3346','量子计算课程与量子架构主题相关，架构细节覆盖仍需查大纲。')
suggest('DM-Data DM-Core DM-Modeling DM-Relational DM-Querying DM-Processing DM-Internals','CS3321 CS3322','数据库技术与数据库原理提供数据库基本机制的学习入口；细分KU覆盖未核验。')
suggest('DM-Analytics','CS3319 CS4303','数据科学基础与大数据处理是数据分析相关学习入口。')
suggest('DM-Distributed','CS3328 CS3322','云计算技术与数据库原理是组合学习线索，不代表存在分布式数据库专课。')
suggest('OS-Purpose OS-Principles OS-Concurrency OS-Protection OS-Scheduling OS-Process OS-Memory OS-Devices OS-Files OS-Advanced-Files OS-Virtualization OS-Faults','CS2310','现代操作系统课程提供操作系统领域学习入口；各细分机制需逐项查课程大纲。')
suggest('NC-Fundamentals NC-Applications NC-Reliability NC-Routing NC-SingleHop','CS3311','计算机网络课程与网络基本机制主题直接相关，具体KU覆盖待核实。')
suggest('NC-Security','CS3325','网络安全技术课程与网络安全单元直接同名相关。')
suggest('NC-Mobility','ICE3307','无线通信原理与移动网络课程名称明确涉及移动网络。')
suggest('PDC-Programs PDC-Communication PDC-Coordination PDC-Evaluation PDC-Algorithms','CS4302','并行与分布式程序设计是并行计算领域的直接学习入口，单元覆盖需查大纲。')
suggest('SE-Teamwork SE-Tools SE-Requirements SE-Design SE-Construction SE-Validation SE-Refactoring SE-Reliability','CS3331','软件工程课程是软件工程活动的领域学习入口；不据课程名称认定全部KU已覆盖。')
suggest('SEC-Crypto','CS3314','密码学与信息安全基础课程名称明确涉及密码学。')
suggest('SEC-Foundations','CS3314 CS3312','信息安全基础与计算机系统安全课程提供安全基础学习入口。')
suggest('SEC-Coding SEC-Engineering','CS3312','计算机系统安全提供安全工程相关入口；安全编码与工程方法具体覆盖待核实。')
suggest('SEP-Context SEP-Ethical-Analysis SEP-Professional-Ethics','CS3309','计算机伦理学与计算伦理、职业责任相关；并未核查完整学习目标。')
suggest('SF-Overview SF-Foundations','CS2307','计算机组成课程提供系统整体结构与基础概念学习入口。')
suggest('SF-Resource','CS2310','现代操作系统提供系统资源管理的相关学习入口。')
suggest('SF-Performance SF-Evaluation','CS2305','计算机系统结构提供系统性能相关学习入口，具体评估方法待核实。')
suggest('SF-Security','CS3312','计算机系统安全课程与系统安全单元主题直接相关。')
suggest('SPD-Robot','CS3349','智算无人系统实践是机器人平台相关学习线索。')
suggest('SPD-Interactive','CS3327','虚拟现实与增强显示技术是交互平台相关学习线索，不等于完整平台开发训练。')
suggest('SPD-Web','CS3351','智算云服务系统实践是Web后端相关学习线索，Web全栈覆盖尚未核验。')
suggest('SPD-Mobile SPD-Game SPD-Embedded','','公开课程名称不足以确认独立的移动、游戏或嵌入式平台开发课程。')
coursehtml=html.fromstring((RAW/'sjtu2026.html').read_bytes())
courses=[]
ids=set(' '.join(coursemap.values()).split())
for row in coursehtml.xpath('//tr'):
 c=[text(x) for x in row.xpath('./td|./th')]
 if len(c)>=6 and c[0] in ids:
  courses.append(dict(id=c[0],name=c[1],credits=float(c[2]),year=c[3],semester=c[4],type=c[5],source=COURSES))
for a in areas:
 assert len(a['units'])==a['expectedUnits'],(a['id'],len(a['units']),a['expectedUnits'])
 a['courseIds']=coursemap[a['id']].split()
 assert len(a['units'])==len(translations[a['id']].split('|')), 'Translation count mismatch: '+a['id']
 for u,z in zip(a['units'],translations[a['id']].split('|')):
  u['zh']=z
  u['courseIds']=specific.get(u['id'],[])
  u['mappingStatus']='editorial-suggestion' if u['courseIds'] else 'unverified'
  if u['courseIds']:
   u['mappingNote']='人工学习入口建议：'+mapping_reasons[u['id']]+' 依据仅为公开课程名称及主题关联，未核验课程大纲，未经学院认定，不表示覆盖该KU全部学习目标。'
  else:
   u['mappingNote']='尚未核验“'+z+'”的具体交大课程对应。'+mapping_reasons.get(u['id'],'现有课程名称不足以建立可靠的KU级对应，故不自动继承本领域课程。')
  if a['id']=='HCI':
   u['courseIds']=[]
   u['mappingStatus']='unverified'
   u['mappingNote']='尚未核验“'+z+'”的具体课程对应。公开课表未找到独立命名的人机交互课程；VR与可视化仅保留在领域层作为相关入口，不能推定覆盖该HCI单元。'
all_units=[u for a in areas for u in a['units']]
all_unit_ids={u['id'] for u in all_units}
course_ids={c['id'] for c in courses}
assert len(areas)==17 and len(all_units)==162 and sum(a['hours'] for a in areas)==270
assert len(courses)==len(course_ids)==50
assert not (set(specific)-all_unit_ids), 'Explicit mapping points to an unknown KU'
assert all(set(u['courseIds'])<=course_ids for u in all_units), 'Mapped course is absent from official course extraction'
assert next(u for u in all_units if u['id']=='GIT-Immersion')['kaHours']=='6'
assert next(u for u in all_units if u['id']=='AR-Logic')['kaHours']=='2 + 1 (SF)'
assert all(not u['courseIds'] for u in lookup['HCI']['units'])
assert all(s.xpath('//*[@id=$frag or @name=$frag]',frag=u['source'].split('#',1)[1]) for u in all_units if '#' in u['source'])

data=dict(version='2026-11-04',sourceReport=REPORT,sourceCourses=COURSES,courseCohort='2026',areas=areas,courses=courses,notes=['CS2023报告2024年1月版；知识域17、知识单元162、CS Core合计270小时。','学时是课程指南的建议教学时间，不是交大学分；跨KA复用学时不重复求和。','四个导航分组和中文译名由项目整理，不是CS2023官方分组。','交大修业导师页面注明仅供参考，培养方案与毕业要求以学院正式要求为准。','KU课程关系为显式人工学习建议，仅据课程名称及主题关系，未核验课程大纲；未建立对应的KU为空，不从领域课程自动推断。'])
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(OUT/'data.js').write_text('window.CS_DATA = '+json.dumps(data,ensure_ascii=False)+';\n')
print(json.dumps({'areas':len(areas),'units':sum(len(a['units']) for a in areas),'hours':sum(a['hours'] for a in areas),'courses':len(courses),'coreUnits':sum(u['isCore'] for a in areas for u in a['units']),'uniqueHourMatches':len(hour_audit),'unmatchedHours':hour_issues,'explicitSuggestedUnits':sum(bool(u['courseIds']) for u in all_units),'unverifiedUnits':sum(not u['courseIds'] for u in all_units)}))
