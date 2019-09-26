import numpy as np
import nixio as nix
import unittest
from nixworks.table import table


class TestTable(unittest.TestCase):

    def setUp(self):
        self.testfilename = "t.nix"
        self.file = nix.File.open(self.testfilename, nix.FileMode.Overwrite)
        self.block = self.file.create_block("test_block", "abc")
        di = {'name': np.int64, 'id': str, 'time': float, 'sig1':
              np.float64, 'sig2': np.int64}
        arr = [[1, "a8sdfn32", 20.04, 3.5, 7],
               [400, "sda98f23rb", 6.5, 2.3, 5]]
        self.df1 = self.block.create_data_frame("test df", "signal1",
                                                data=arr, col_dict=di)
        darr = [[1, 2, 3], [4, 5, 6]]
        self.da1 = self.block.create_data_array("test_da", "da1", data=darr)

    def tearDown(self):
        self.file.close()

    def test_panda_df(self):
        pd_df = table.write_to_pandas(self.file.blocks[0].data_frames[0])
        df_new = table.create_from_pandas(self.block, pd_df, "new_df")
        assert list(df_new[:]) == list(self.df1[:])
