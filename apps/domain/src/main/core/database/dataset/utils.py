from copy import deepcopy
from io import StringIO

import torch as th
import numpy as np
import pandas as pd
from syft.core.common.uid import UID
from syft.core.store.storeable_object import StorableObject

from ..bin_storage.json_obj import JsonObject
from ..store_disk import DiskObjectStore
from ..bin_storage.metadata import get_metadata
from .datasetgroup import DatasetGroup


def store_json(db, df_json: dict) -> dict:
    _json = deepcopy(df_json)
    storage = DiskObjectStore(db)
    mapping = []

    # Separate CSV from metadata
    for el in _json["tensors"].copy():
        _id = UID()
        _json["tensors"][el]["id"] = str(_id.value)
        mapping.append((el, _id, _json["tensors"][el].pop("content", None)))

    # Ensure we have same ID in metadata and dataset
    df_id = UID()
    _json["id"] = str(df_id.value)

    # Create storables from UID/CSV. Update metadata
    storables = []
    for idx, (name, _id, raw_file) in enumerate(mapping):
        _tensor = pd.read_csv(StringIO(raw_file))
        _tensor = th.tensor(_tensor.values.astype(np.float32))

        _json["tensors"][name]["shape"] = [int(x) for x in _tensor.size()]
        _json["tensors"][name]["dtype"] = "{}".format(_tensor.dtype)
        storage.__setitem__(_id, StorableObject(id=_id, data=_tensor))
        # Ensure we have same ID in metadata and dataset
        db.session.add(
            DatasetGroup(bin_object=str(_id.value), dataset=str(df_id.value))
        )

    json_obj = JsonObject(id=_json["id"], binary=_json)
    metadata = get_metadata(db)
    metadata.length += 1

    db.session.add(json_obj)
    db.session.commit()
    return _json
