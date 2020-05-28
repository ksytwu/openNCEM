"""
Tests for the basic functionality of the dm io module.
"""

import pytest

import time
import inspect
import ncempy.io.dm
import os

class test_dm3():
    """
    Test the DM3 io module
    """
    
    # Auxiliary attributes and method to facilitate the location of the test images
    _current_file = os.path.dirname(os.path.abspath(
                    inspect.getfile(inspect.currentframe())))
    _images_folder="{}/resources".format(_current_file)

    def _get_image_route(self, file_name):
        return os.path.join(self._images_folder, file_name)

    def _read_dm3_data(self, file_route, on_memory=False):
        """Creates a fileDM and reads its data metadata

        Parameters
        ----------
             file_route : str
                full route where the file is placed.

             on_memory : bool
                if True, the dm file will be opened in on memory mode.
        """
        
        with ncempy.io.dm.fileDM(file_route, on_memory=on_memory) as f:
            if on_memory:
                assert f._on_memory
            f.parseHeader()
            ds = f.getDataset(0)
            img = ds['data']

            if img.ndim == 3:
                img = img[:, :, img.shape[2]//2, ]
            elif img.ndim == 4:
                img = img[:, :, img.shape[2]//2, img.shape[3]//2]
            elif img.ndim > 4:
                raise ValueError("Images with more than four dimensions not supported.")
            metadata = dict(dimensions=img.ndim,
                            header=f.allTags,
                            metadata={x: ds[x] for x in ds.keys() if x != "data"})

        return metadata, img
    
    def test_read_dm3(self):
        
        metadata, img = self._read_dm3_data(self._get_image_route(
                            "dmTest_3D_float32_nonSquare_diffPixelSize.dm3"))

        assert metadata["dimensions"] == 3
        assert metadata["metadata"]["pixelOrigin"] == [0.0, 0.0, 0.0]
        assert img.ndim == 3

    def test_read_dm3_1d(self):
        
        metadata, img = self._read_dm3_data(self._get_image_route("08_Carbon.dm3"))

        assert metadata["dimensions"] == 2
        assert metadata["metadata"]["pixelOrigin"] == [0.0, 200.0]
        assert img.shape == 2048

    def test_read_dm3_on_memory(self):
        
        metadata, img = self._read_dm3_data(self._get_image_route("dmTest_3D_float32_nonSquare_diffPixelSize.dm3"),
                                            on_memory=True)
        assert metadata["dimensions"] == 3
        assert metadata["metadata"]["pixelOrigin"] == [0.0, 0.0, 0.0]

    def test_dm4_memory_vs_file_performance(self):
        """ Test speed improvement with on_memory option.
        Even with a local HDD, memory read should be x10 faster.

        """
        m0 = time.time()
        for i in range(10):
            _ = self._read_dm3_data(self._get_image_route("Si-SiGe-test-01-31x12x448x480.dm4"))
            delta0 = m0 - time.time()
            
            m1 = time.time()
            _ = self._read_dm3_data(self._get_image_route("Si-SiGe-test-01-31x12x448x480_copy.dm4"),
                                    on_memory=True)
            delta1 = m1 - time.time()

            assert delta0 > delta1

    def test_extract_on_memory(self):
        with ncempy.io.dm.fileDM(self._get_image_route("Si-SiGe-test-01-31x12x448x480.dm4"),
                                 on_memory=False) as f:
            ds = f.getDataset(0)
            img3D_no_on_mem = ds['data']

        with ncempy.io.dm.fileDM(self._get_image_route("Si-SiGe-test-01-31x12x448x480.dm4"),
                                 on_memory=True) as f:
            ds = f.getDataset(0)
            img3D_on_mem = ds['data']

        assert img3D_on_mem[0:25] == img3D_no_on_mem[0:25]
