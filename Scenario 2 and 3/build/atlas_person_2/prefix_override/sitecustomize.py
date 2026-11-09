import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/dhruv/A.T.L.A.S_EOD/install/atlas_person_2'
