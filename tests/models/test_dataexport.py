import unittest

from ..context import src
from ..testutils import gen_export_data
from src.models.dataexport import DataExport, DataExportException


class TestDataExport(unittest.TestCase):
    def test_validate_row(self):
        data = DataExport()
        rows = gen_export_data()
        for r in rows:
            data._validate_row(r)

        bad_row = rows[0]
        bad_row[3] = 'not float'
        with self.assertRaises(DataExportException):
            data._validate_row(bad_row)
