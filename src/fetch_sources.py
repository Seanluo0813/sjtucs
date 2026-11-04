"""Fetch public upstream HTML for CS2023 rebuilding; no credentials needed."""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib,json,time
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
SOURCES={
 'cs2023.html':'https://csed.acm.org/wp-content/uploads/2025/11/CS2023-Report.htm',
 'sjtu2026.html':'https://mentor.sjtu.edu.cn/jwc/plans/view/4E34A4CBEA26FFC1E065F8163EE1DCCC/?render=1'
}
RAW.mkdir(parents=True,exist_ok=True)
manifest=[]
for name,url in SOURCES.items():
 with urlopen(Request(url,headers={'User-Agent':'CourseResearchDashboard/1.0'}),timeout=180) as response:
  content=response.read()
 (RAW/name).write_bytes(content)
 manifest.append({'file':name,'url':url,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sha256':hashlib.sha256(content).hexdigest()})
 print(name,len(content),'bytes')
(RAW/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Run python3 src/build_tree_data.py to rebuild after reviewing upstream changes.')
