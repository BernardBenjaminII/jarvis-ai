import re,zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET
def _clean(s):
 s=re.sub(r"(?is)<(script|style).*?>.*?</\1>"," ",s); s=re.sub(r"(?i)</(p|div|h[1-6]|li|br)>","\n",s); s=re.sub(r"<[^>]+>"," ",s); s=unescape(s)
 return "\n".join(" ".join(x.split()) for x in s.splitlines() if x.strip())
def extract_epub(path):
 with zipfile.ZipFile(path) as z:
  names=[]
  try:
   root=ET.fromstring(z.read('META-INF/container.xml')); opf=next((n.attrib.get('full-path') for n in root.iter() if n.tag.rsplit('}',1)[-1]=='rootfile'),None)
   if opf:
    r=ET.fromstring(z.read(opf)); base=str(Path(opf).parent); base='' if base=='.' else base; man={}; spine=[]
    for n in r.iter():
     tag=n.tag.rsplit('}',1)[-1]
     if tag=='item' and n.attrib.get('media-type') in ('application/xhtml+xml','text/html'): man[n.attrib.get('id')]=n.attrib.get('href')
     elif tag=='itemref': spine.append(n.attrib.get('idref'))
    names=[((base+'/'+man[i]) if base else man[i]).replace('\\','/') for i in spine if i in man]
  except Exception: pass
  if not names:names=sorted(n for n in z.namelist() if n.lower().endswith(('.xhtml','.html','.htm')))
  parts=[]
  for n in names:
   try:t=_clean(z.read(n).decode('utf-8','ignore'))
   except Exception:continue
   if t.strip():parts.append(t)
  return '\n\n'.join(parts),len(parts)
