import math
import utils

# number of splits
N = 10
#file to split
fin = 'fr_elites_handles.json'

twitters = utils.json_load(fin)
M = len(twitters)
k = math.ceil(M/N)
separated = [twitters[i:i+k] for i in range(0, M, k)]

fname, extension = fin.split('.')
for i, accnts in enumerate(separated):
    fout = "{}_{}.{}".format(fname, str(i+1), extension)
    utils.json_dump(accnts, fout)