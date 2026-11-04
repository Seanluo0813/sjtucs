#!/usr/bin/env python3
"""知径 CS2023 独立网站的离线完整性检查。

在网站根目录运行：python3 src/check_site.py
或指定目录：python3 check_cs_tree.py --root /path/to/site
仅使用 Python 标准库；有 Node.js 时检查 JavaScript 语法。不联网、不写文件。
"""
from __future__ import annotations
import argparse
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

EXPECTED_AREAS = {'AI','AL','AR','DM','FPL','GIT','HCI','MSF','NC','OS','PDC','SDF','SE','SEC','SEP','SF','SPD'}
SKIP = {'.git','node_modules','raw','__pycache__','_site','.venv','venv'}

class References(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]; self.scripts=[]; self.styles=[]
    def handle_starttag(self, tag, attributes):
        attrs=dict(attributes)
        for key in ('src','href','poster','data-src'):
            if attrs.get(key):
                runtime=tag in ('script','img','source','video','audio','iframe') or (tag=='link' and attrs.get('rel') in ('stylesheet','icon','preload'))
                self.refs.append((attrs[key],runtime))
        if tag=='script' and attrs.get('src'):self.scripts.append(attrs['src'])
        if attrs.get('style'):self.styles.append(attrs['style'])
        if attrs.get('srcset') and not attrs['srcset'].startswith('data:'):
            self.refs.extend((part.strip().split()[0],True) for part in attrs['srcset'].split(',') if part.strip())
        if tag=='base':self.refs.append(('__BASE_TAG__',True))
    def handle_startendtag(self,tag,attributes):self.handle_starttag(tag,attributes)

class Audit:
    def __init__(self, root):
        self.root=root.resolve();self.errors=[];self.warnings=[];self.checks=0
        self.references=0;self.dynamic=0;self.facts={};self.seen=set()
    def check(self,condition,message):
        self.checks+=1
        if not condition:self.errors.append(message)
        return bool(condition)
    def label(self,path):return str(path.relative_to(self.root))
    def reference(self,origin,value,runtime=False):
        value=unescape(value).strip()
        if value=='__BASE_TAG__':self.check(False,f'{self.label(origin)}: 不支持改变根路径的 base 标签');return
        if not value:return
        if '${' in value:self.dynamic+=1;return
        if value.startswith(('data:','blob:','mailto:','tel:','javascript:')):return
        try:parsed=urlsplit(value)
        except ValueError:self.check(False,f'{self.label(origin)}: URL 格式错误 {value}');return
        if parsed.scheme or parsed.netloc:
            if runtime:self.check(False,f'{self.label(origin)}: 存在联网运行资源 {value}')
            return
        if not parsed.path:return
        path=unquote(parsed.path).replace('\\','/')
        key=(str(origin),path)
        if key in self.seen:return
        self.seen.add(key);self.references+=1
        if not self.check(not path.startswith('/'),f'{self.label(origin)}: 绝对路径不能适配独立仓库 {value}'):return
        target=(origin.parent/path).resolve()
        if not self.check(target.is_relative_to(self.root),f'{self.label(origin)}: 引用越过网站根目录 {value}'):return
        self.check(target.exists(),f'{self.label(origin)}: 本地资源不存在 {value}')
        if target.is_dir():self.check((target/'index.html').is_file(),f'{self.label(origin)}: 目录入口缺少 index.html {value}')
    def paths(self,suffix):
        return sorted(p for p in self.root.rglob('*'+suffix) if not any(part in SKIP for part in p.relative_to(self.root).parts))
    def css(self,path,text):
        for match in re.finditer(r'url\(\s*([\x22\x27]?)(.*?)\1\s*\)',text,re.S):self.reference(path,match.group(2),True)
        for match in re.finditer(r'@import\s+[\x22\x27]([^\x22\x27]+)',text):self.reference(path,match.group(1),True)
    def resources(self):
        self.check((self.root/'index.html').is_file(),'缺少网站根目录 index.html')
        for path in self.paths('.html'):
            text=path.read_text(encoding='utf-8-sig');parser=References();parser.feed(text)
            for value,runtime in parser.refs:self.reference(path,value,runtime)
            for style in parser.styles:self.css(path,style)
            for style in re.findall(r'<style\b[^>]*>(.*?)</style\s*>',text,re.S|re.I):self.css(path,style)
        for path in self.paths('.css'):self.css(path,path.read_text(encoding='utf-8-sig'))
        node=shutil.which('node');checked=0
        for path in self.paths('.js'):
            text=path.read_text(encoding='utf-8-sig')
            # fetch 与动态 HTML 属性中的相对 URL 以根页面为基准。
            patterns=[r'\b(?:fetch|import)\s*\(\s*[\x22\x27`]([^\x22\x27`]+)',r'(?:href|src)\s*=\s*[\x22\x27`]([^\x22\x27`<>]+)']
            for pattern in patterns:
                for value in re.findall(pattern,text):self.reference(self.root/'index.html',value)
            if node:
                result=subprocess.run([node,'--check',str(path)],capture_output=True,text=True,check=False)
                checked+=1;self.check(result.returncode==0,f'{self.label(path)}: JavaScript 语法错误 {result.stderr.strip()}')
        if not node:self.warnings.append('未找到 Node.js，跳过 JavaScript 语法检查。')
        self.facts['javascript_files_checked']=checked
    def dataset(self):
        required=['data.json','data.js','app.js','style.css']
        if not all([self.check((self.root/name).is_file(),f'缺少 {name}') for name in required]):return
        try:data=json.loads((self.root/'data.json').read_text(encoding='utf-8-sig'))
        except ValueError as error:self.check(False,f'data.json 无法解析：{error}');return
        self.check(all(key in data for key in ('areas','courses','sourceReport','sourceCourses','version')),'JSON 缺少必要顶层字段')
        areas=data.get('areas',[]);courses=data.get('courses',[])
        units=[unit for area in areas for unit in area.get('units',[])]
        hours=sum(area.get('hours',0) for area in areas)
        self.check(len(areas)==17 and {a.get('id') for a in areas}==EXPECTED_AREAS,'应保留官方 17 个知识领域')
        self.check(len(units)==162 and len({u.get('id') for u in units})==162,'应保留 162 个唯一知识单元')
        self.check(hours==270,'CS Core 领域学时应合计 270')
        course_ids={course.get('id') for course in courses}
        self.check(len(courses)==50 and len(course_ids)==50,'应保留 50 门唯一交大课程')
        for area in areas:
            self.check(area.get('expectedUnits')==len(area.get('units',[])),f"{area.get('id')}: KU 数量与官方汇总不符")
            self.check(set(area.get('courseIds',[]))<=course_ids,f"{area.get('id')}: 课程引用不存在")
        for unit in units:
            self.check(set(unit.get('courseIds',[]))<=course_ids,f"{unit.get('id')}: 课程引用不存在")
            self.check(bool(unit.get('mappingNote')),f"{unit.get('id')}: 缺少课程映射口径")
        wrapper=(self.root/'data.js').read_text(encoding='utf-8-sig')
        match=re.fullmatch(r'\s*window\.CS_DATA\s*=\s*(\{.*\})\s*;?\s*',wrapper,re.S)
        if self.check(match is not None,'data.js 必须封装为 window.CS_DATA'):
            try:self.check(json.loads(match.group(1))==data,'data.js 与 data.json 内容不一致')
            except ValueError as error:self.check(False,f'data.js 封装 JSON 无法解析：{error}')
        parser=References();parser.feed((self.root/'index.html').read_text(encoding='utf-8-sig'))
        scripts=[urlsplit(s).path.removeprefix('./') for s in parser.scripts]
        self.check('data.js' in scripts and 'app.js' in scripts and scripts.index('data.js')<scripts.index('app.js'),'index.html 必须在 app.js 前载入 data.js')
        self.check('window.CS_DATA' in (self.root/'app.js').read_text(encoding='utf-8-sig'),'app.js 必须优先使用离线数据 window.CS_DATA')
        self.facts.update(knowledge_areas=len(areas),knowledge_units=len(units),cs_core_hours=hours,sjtu_courses=len(courses))
    def run(self):
        self.resources();self.dataset()
        return {'status':'FAIL' if self.errors else 'PASS','root':str(self.root),'checks':self.checks,'local_references_checked':self.references,'facts':self.facts,'dynamic_url_expressions':self.dynamic,'warnings':self.warnings,'errors':self.errors,'scope':'静态检查不联网；动态数据来源链接与交互行为仍需浏览器验收。'}

def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1],help='知径网站根目录')
    args=parser.parse_args();audit=Audit(args.root)
    try:report=audit.run()
    except (OSError,ValueError,TypeError,KeyError) as error:
        audit.check(False,f'检查未完成：{error}')
        report={'status':'FAIL','root':str(audit.root),'checks':audit.checks,'warnings':audit.warnings,'errors':audit.errors}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 1 if audit.errors else 0
if __name__=='__main__':sys.exit(main())
