import urllib.request
import json
import uuid

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/workspaces/f74c5258-472d-44ca-9626-277174d3914f/projects/59be1d65-c1ed-4813-a925-cf52a397509c/workflow')
req.add_header('Authorization', 'Bearer dummy')
try:
    resp = urllib.request.urlopen(req)
    print('OK:', resp.getcode(), resp.read())
except Exception as e:
    print('ERR:', getattr(e, 'code', str(e)), getattr(e, 'read', lambda: b'')())
