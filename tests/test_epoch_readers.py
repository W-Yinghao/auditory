import io
import struct
import tempfile
import unittest
from pathlib import Path
import numpy as np
from audit_egi_events import read_header
from audit_other_eeg import records

class ReaderChecks(unittest.TestCase):
    def header(self,version):
        return struct.pack('>i6hi5h',version,2020,1,2,3,4,5,0,1000,2,1,0,0)

    def test_continuous_precision_and_event_codes(self):
        for version,dtype in [(2,'>i2'),(4,'>f4'),(6,'>f8')]:
            b=self.header(version)+struct.pack('>ih',10,2)+b'staddev '
            h=read_header(io.BytesIO(b))
            self.assertEqual((h['n_samples'],h['n_segments'],h['offset']),(10,1,44))
            self.assertEqual(h['event_codes'],['stad','dev ']);self.assertEqual(h['dtype'],dtype)

    def test_segmented_header_does_not_read_category_as_sample_count(self):
        b=self.header(5)+struct.pack('>hB',1,8)+b'Standard'+struct.pack('>hih',3,701,1)+b'stad'
        h=read_header(io.BytesIO(b))
        self.assertEqual(h['categories'],['Standard']);self.assertEqual(h['n_segments'],3)
        self.assertEqual(h['n_samples'],701);self.assertEqual(h['offset'],len(b))

    def test_eeglab_flattened_event_latency_origin(self):
        sf=1000;pnts=701;xmin=-.2
        for epoch in (1,2,1000):
            zero_1based=(epoch-1)*pnts+201
            recovered=(zero_1based-1-(epoch-1)*pnts)/sf+xmin
            self.assertAlmostEqual(recovered,0)
            self.assertAlmostEqual((zero_1based+40-1-(epoch-1)*pnts)/sf+xmin,.04)

    def test_multi_event_epoch_metadata_stays_nested(self):
        d={'event':[np.array([1,2]),np.array([3])], 'eventtype':[['1','2'],['2']], 'eventlatency':[[0.,500.],[0.]]}
        out=records(d)
        self.assertEqual(len(out),2);self.assertEqual(out[0]['eventtype'],['1','2'])

if __name__=='__main__':unittest.main()
