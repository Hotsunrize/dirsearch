import xml.etree.ElementTree as ET
import base64
import re
tree = ET.parse('1.xml')
f = open('num.txt','a+')
root = tree.getroot()

for i in root:
    data_encode = i.findall("request")[0].text
    data=base64.b64decode(data_encode).decode('utf-8')
    num = re.findall('userName=(\d+)',data)
    f.write(num[0]+'\n')




