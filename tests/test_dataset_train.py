import json

import joblib
import pytest

from conftest import CLASSES, make_df
from sanket_setu.dataset import DatasetError, validate
from sanket_setu.train_model import train


def run(df, tmp_path):
    return train(df, "test", n_estimators=20, model_path=tmp_path / "m.joblib", meta_path=tmp_path / "meta.json",
                 report_dir=tmp_path / "rep")


def test_validate_ok(synth):
    df, _ = validate(synth[0], CLASSES)
    assert len(df) == len(synth[0])


def test_missing_class_and_nan_and_columns(synth):
    df = synth[0]
    with pytest.raises(DatasetError, match="No samples"):
        validate(df[df.label != "num_2"], CLASSES)
    bad = df.copy()
    bad.loc[0, "f0"] = float("nan")
    with pytest.raises(DatasetError, match="NaN"):
        validate(bad, CLASSES)
    with pytest.raises(DatasetError, match="missing columns"):
        validate(df.drop(columns=["signer_id"]), CLASSES)
    with pytest.raises(DatasetError, match="Too few"):
        validate(df.groupby("label").head(3), CLASSES)


def test_group_split_and_artifacts(synth, tmp_path):
    meta = run(synth[0], tmp_path)
    assert "signer_id" in meta["split_strategy"] and meta["cross_person_validated"]
    model = joblib.load(tmp_path / "m.joblib")
    assert list(model.classes_) == meta["class_order"] == json.loads((tmp_path / "meta.json").read_text())["class_order"]
    assert (tmp_path / "rep" / "metrics.json").exists() and (tmp_path / "rep" / "classification_report.txt").exists()


def test_single_signer_is_flagged_unvalidated(tmp_path):
    df, _ = make_df(signers=1, per=20)
    meta = run(df, tmp_path)
    assert meta["cross_person_validated"] is False and any("UNVALIDATED" in w for w in meta["warnings"])


def test_metadata_never_in_features(synth, tmp_path):
    run(synth[0], tmp_path)
    assert joblib.load(tmp_path / "m.joblib").n_features_in_ == 63
