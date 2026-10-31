"""Bounded diagnostic import for the pinned, isolated FLAIM checkout."""
import faulthandler
import sys
import time

sys.path.insert(0, '/home/ubuntu/research-director/btp-reference-src-20261025/flaim')
faulthandler.dump_traceback_later(30, repeat=True)
start = time.monotonic()
from synth_fl.generators.federated.flaim import FLAIM
from synth_fl.generators import FederatedGeneratorConfig
from synth_fl.utils.dataloaders import TabularDataset
print({'status': 'imported', 'seconds': time.monotonic()-start,
       'classes': [FLAIM.__name__, FederatedGeneratorConfig.__name__, TabularDataset.__name__]}, flush=True)
