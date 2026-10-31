"""Exact Stage 2 authoring inputs and approved Stage 1 raster goldens.

No directory exemptions, original-input replacements or Native permission changes.
"""
import hashlib

INPUT_SHA256 = {'assets/experiments/native_terrain_47_96/baked_v2/baked_terrain.tres': 'e70237fe02222ccd3b9da8e96a27320d642a7244605e258012f44f4f666f3256',
 'assets/experiments/native_terrain_47_96/baked_v2/baseline_94.png': '5a3d448774fc2dc816f02827b75ecca1f1a57678e5023f383525cb811aff1977',
 'assets/experiments/native_terrain_47_96/baked_v2/interiors_bc.png': '01de466fcec2e7ed8e8cadf9813a57d3783eb57b50ec56408a9ba0346357efc8',
 'assets/experiments/native_terrain_47_96/baked_v2/mapping.json': '7702325b9d235ee7edc7f5ab0e6bdaa23db6f2ee8293f297a5d90449bb98d867',
 'scenes/experiments/native_terrain_47_96/illustrated_baked_v2.tscn': '24784615040640b05325ebb71b96b3bd038ce2f708ad769e2ec792c884269451',
 'tools/bake-illustrated-terrain.py': '2227fe4b280dd3538ed435ace64af5540b7061be3dbe396633df8cd931d6acdf'}

APPROVED_BASELINE_PIXELS = {(9, 2): '500b39a235c88b636076cb0b97b0d3edad9de17366659fe636891027c4717580',
 (8, 0): '9704015e7ab99b807a22e0dff48d78e7b138e7f516c19f5981bb6496c11eccd5',
 (5, 1): '01638b6a2946a6b73577ad39d24c2ea1b12838a3267a261b47fffaa044218492',
 (0, 0): 'c32b6153f6096a4f8405b99e38785708490df94d6f8cce66d2f612123157512e',
 (0, 1): '67359b6ea2344b45235e6eddd8641b93d6dc9867441727dd127787d78434bf30',
 (0, 3): '5bb8ee9ed9b05b4922b98df3127f75a2a9bfddf4475f786a9533539e65aa6fbb',
 (10, 0): 'e13bc9454ae4f8203b137082fc192cf16adc36586a91d354e534b2e698d3bf1f',
 (9, 3): '0edca149220c1b6e39d5d416540791247d20ebdab550e3836f6e2cb4616f0cdf',
 (8, 1): 'f7852faf50bc45e6cacecfd2b44e58d625817021f31be7df6e39b9d6ea2690a1',
 (11, 2): 'cf23348b8a106d3e6e93adcb60aae6d66ac23220d8270d39dc26bcc60d63efb4',
 (9, 6): '1c2f50719c586fcdcbbc9e2f58aa03a6dd2b27bb1c0710c35b7e4af31f14d028',
 (8, 4): 'ae11e784584075a590dbdda00c9dc56eb7b55fbfdb592e54f81ece52f7f78627',
 (5, 5): '122c9d80e7fd783e453958a1319b834496dd0c629ca64be0e9b7a9d07bc33107',
 (0, 4): '2fed8cd339fcc191a2b46479a535dbbbd38954a596031824b15eda29c5b98ec3',
 (0, 5): '0de13f7f8288d064600d902fb73f7db26b2f334812e1c5873f3039998462eed9',
 (0, 7): '51fe7a7f8563167d9872bc9f7a2f25778a2b7c1d231eecf072ecac04e2daab73',
 (10, 4): '6d0f42f044a314c7477c3f48f948387d043a4a686f82f4d3f57931c82ca1e9ea',
 (9, 7): 'd8729712827dbe1a4f0545cb3e8f3dba56f194886239b103d7ceb24068d7f4ef',
 (8, 5): 'c37ebe612773c7a258a8193472c61edbbe3e0095833e4f1a3902fb7f4cf72455',
 (11, 6): 'de43f8b450ae93b9b69a243ea9647e63954b89cb0b89949d398247326534f9e2'}

APPROVED_INTERIOR_PIXELS = {(0, 1): 'ed181155435a3050414d236cf565e223e7e12e7cf1fe9fb304f9961de66d3195',
 (0, 2): 'd4f08a5ba48f34fbb8216c38b9b9f6c2c8cfe47131268b3032857b5c81c09715',
 (1, 1): '2baad3a95a23ac2c1df80c598ab631e43188c7f18ef32dd40603e2c77e4beb5f',
 (1, 2): '10ca83cb502496c208ea7de596c23055dec2ff2a356de98fb1b24fbcdd0badb2'}

def verify_input(path, raw):
    if path not in INPUT_SHA256:
        raise AssertionError(f'Unapproved baked input: {path}')
    if not path.endswith('.png'):
        raw = raw.replace(b'\r\n', b'\n')
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA256[path]:
        raise AssertionError(f'Modified baked input: {path}')
