import os
import sys

import ffmpeg
from bilibili import BiliSession
ses = BiliSession(os.getenv('BILISESSDATA'))
bvid = (sys.argv[1:2] or ['BV1x5411Y72N'])[0]

meta = ses.get_video_meta(bvid)
os.makedirs('output', exist_ok=True)
# os.chdir('output')
for p, part_meta in meta['parts'].items():
    # print(part_meta['qualities'][32]['stream'])
    ses.download(meta, p)
