"""Synthetic fixtures: test pipeline MECHANICS only. Never used for reported metrics."""
import numpy as np
import pandas as pd
import pytest

from sanket_setu.config import ALL_COLS, FEATURE_COLS, N_FEATURES

CLASSES = ["none", "num_1", "num_2"]


def make_df(signers=3, per=12, seed=0):
    rng = np.random.default_rng(seed)
    protos = {c: rng.normal(size=N_FEATURES) * 3 for c in CLASSES}
    rows, n = [], 0
    for s in range(signers):
        for c in CLASSES:
            for _ in range(per):
                n += 1
                row = dict(sample_id=f"id{n}", label=c, signer_id=f"S{s}", session_id="a", timestamp="t",
                           capture_condition="x", hand_side="Right")
                row.update(dict(zip(FEATURE_COLS, protos[c] + rng.normal(scale=0.2, size=N_FEATURES))))
                rows.append(row)
    return pd.DataFrame(rows, columns=ALL_COLS), protos


@pytest.fixture
def synth():
    return make_df()
