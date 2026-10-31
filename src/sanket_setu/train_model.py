"""Group-aware training with measured metrics only. python -m sanket_setu.train_model"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from importlib import metadata

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from .config import DATA_CSV, FEATURE_COLS, META_PATH, MODEL_PATH, N_FEATURES, REPORT_DIR, load_signs, trainable
from .dataset import DatasetError, load_dataset


def split_indices(df: pd.DataFrame, seed: int, tries: int = 20):
    """Return train/val/test index arrays, strategy text, cross_person_validated flag, warnings.

    Group-aware: the split is by signer (preferred) or by signer/session, never by
    adjacent video frames. With few groups a split can leave a class out of the training
    partition, so several seeds are tried before giving up with an actionable error.
    """
    warns: list[str] = []
    groups, strategy, cross = None, "", False
    if df["signer_id"].nunique() >= 3:
        groups, strategy, cross = df["signer_id"], "group split by signer_id (held-out signers)", True
    else:
        combo = df["signer_id"] + "/" + df["session_id"]
        if combo.nunique() >= 3:
            groups, strategy = combo, "group split by signer/session (held-out sessions, same people)"
            warns.append("Fewer than 3 signers: cross-person generalization is UNVALIDATED.")
    if groups is not None:
        n_groups = groups.nunique()
        if n_groups == 3:
            warns.append("Only 3 signer groups: the training partition contains roughly one signer, "
                         "so the model sees a single person's hand. Treat metrics as indicative only.")
        last_err = ""
        for attempt in range(tries):
            s = seed + attempt
            tv, te = next(GroupShuffleSplit(1, test_size=0.3, random_state=s).split(df, groups=groups))
            sub = df.iloc[tv]
            if sub["label"].nunique() < df["label"].nunique():
                last_err = "a class was missing from the training partition"
                continue
            tr_r, va_r = next(GroupShuffleSplit(1, test_size=0.3, random_state=s).split(sub, groups=groups.iloc[tv]))
            tr, va = tv[tr_r], tv[va_r]
            if set(df.iloc[tr]["label"]) == set(df["label"].unique()) and set(df.iloc[va]["label"]) == set(df["label"].unique()):
                return np.array(tr), np.array(va), np.array(te), strategy, cross, warns
            last_err = "a class was missing from a partition"
        raise DatasetError(
            f"Could not build a group split where every class appears in every partition "
            f"({last_err}) after {tries} attempts. Collect from more signers or more sessions per signer."
        )
    else:
        strategy = "RANDOM stratified split (single signer/session): NOT a valid estimate of real-world accuracy"
        warns.append("!!! Only one signer/session: split is random, results are optimistic and cross-person generalization is UNVALIDATED. !!!")
        try:
            tv, te = train_test_split(np.arange(len(df)), test_size=0.25, stratify=df["label"], random_state=seed)
            tr, va = train_test_split(tv, test_size=0.25, stratify=df["label"].iloc[tv], random_state=seed)
        except ValueError as exc:
            raise DatasetError(f"Dataset too small to split ({exc}). Collect more samples per class.") from exc
    return np.array(tr), np.array(va), np.array(te), strategy, cross, warns


def tune_threshold(score, pred, truth) -> float:
    """Pick the reject threshold on VALIDATION data: reward correct accepts, penalise wrong accepts 2x."""
    best_u, best_t = -1e9, 0.5
    for t in np.arange(0.30, 0.96, 0.05):
        acc = score >= t
        ok = pred == truth
        u = int((ok & acc).sum()) - 2 * int((~ok & acc).sum())
        if u >= best_u:
            best_u, best_t = u, float(t)
    return round(best_t, 2)


def _version(pkg: str) -> str:
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return "not installed"


def train(df, config_version="unknown", seed=42, n_estimators=300, model_path=MODEL_PATH, meta_path=META_PATH,
          report_dir=REPORT_DIR, extra_meta: dict | None = None) -> dict:
    tr, va, te, strategy, cross, warns = split_indices(df, seed)
    for name, idx in (("train", tr), ("validation", va), ("test", te)):
        if len(idx) == 0:
            raise DatasetError(f"{name} split is empty. Collect data from more signers/sessions.")
    classes = sorted(df["label"].unique())
    if set(df.iloc[tr]["label"]) != set(classes):
        raise DatasetError("Some classes are absent from the training split. Collect more sessions/signers per class.")

    X, y = df[FEATURE_COLS].to_numpy(float), df["label"].to_numpy()  # metadata never enters X
    # Keep training deterministic and avoid spawning worker processes on locked-down
    # Windows/hackathon environments; landmark datasets are small enough for one core.
    model = RandomForestClassifier(n_estimators=n_estimators, class_weight="balanced", random_state=seed, n_jobs=1)
    model.fit(X[tr], y[tr])
    cls = np.array(model.classes_)

    pv = model.predict_proba(X[va])
    thr = tune_threshold(pv.max(1), cls[pv.argmax(1)], y[va])  # validation only

    pt = model.predict_proba(X[te])  # test set touched once
    pred, score = cls[pt.argmax(1)], pt.max(1)
    present = sorted(set(y[te]) | set(pred))
    p, r, f1, _ = precision_recall_fscore_support(y[te], pred, labels=present, average="macro", zero_division=0)
    accepted = score >= thr
    metrics = {
        "test_accuracy": float(accuracy_score(y[te], pred)),
        "macro_precision": float(p), "macro_recall": float(r), "macro_f1": float(f1),
        "reject_threshold": thr,
        "test_coverage_at_threshold": float(accepted.mean()),
        "test_accuracy_on_accepted": float((pred[accepted] == y[te][accepted]).mean()) if accepted.any() else None,
        "per_class": classification_report(y[te], pred, labels=present, output_dict=True, zero_division=0),
        "confusion_matrix": {"labels": present, "matrix": confusion_matrix(y[te], pred, labels=present).tolist()},
        "n_train": int(len(tr)), "n_val": int(len(va)), "n_test": int(len(te)),
        "class_counts": {k: int(v) for k, v in df["label"].value_counts().items()},
        "signers": int(df["signer_id"].nunique()), "sessions": int(df.groupby("signer_id")["session_id"].nunique().sum()),
    }

    # --- per-signer breakdown: the honest view of "does this work on a NEW person?" ---
    te_pos = np.asarray(te)
    te_df = df.iloc[te_pos].copy()
    te_df["_rel"] = np.arange(len(te_pos))          # position within the test prediction arrays
    per_signer = {}
    for signer, grp in te_df.groupby("signer_id"):
        rel = grp["_rel"].to_numpy()
        s_pred, s_true, s_score = pred[rel], y[te][rel], score[rel]
        keep = s_score >= thr
        per_signer[str(signer)] = {
            "n_test_samples": int(len(rel)),
            "accuracy": float((s_pred == s_true).mean()) if len(rel) else None,
            "accuracy_on_accepted": float((s_pred[keep] == s_true[keep]).mean()) if keep.any() else None,
            "labels_present": sorted(set(s_true)),
        }
    metrics["per_signer"] = per_signer
    metrics["held_out_signers"] = sorted(per_signer.keys())
    metrics["samples_per_signer_per_class"] = {
        str(s): {c: int(n) for c, n in grp["label"].value_counts().items()}
        for s, grp in df.groupby("signer_id")
    }

    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": f"RandomForestClassifier(n_estimators={n_estimators}, class_weight=balanced, seed={seed})",
        "class_order": [str(c) for c in cls],
        "feature_schema": {"n_features": N_FEATURES, "layout": "21 landmarks x (x,y,z), wrist-relative, scaled by wrist->middle MCP"},
        "config_version": config_version,
        "split_strategy": strategy,
        "cross_person_validated": cross,
        "warnings": warns,
        "reject_threshold": thr,
        "library_versions": {k: _version(k) for k in ("scikit-learn", "numpy", "mediapipe")},
        "data_hash": hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest(),
        "metrics": {k: metrics[k] for k in ("test_accuracy", "macro_f1", "test_coverage_at_threshold", "test_accuracy_on_accepted", "n_test")},
        "per_signer": per_signer,
        "held_out_signers": metrics["held_out_signers"],
        "score_semantics": (
            "Values from predict_proba are an UNCALIBRATED RandomForest score, not a real-world "
            "probability and not accuracy. The reject threshold was tuned on the validation "
            "partition only and applied unchanged to the test partition."
        ),
    }
    if extra_meta:
        meta.update(extra_meta)
    for path in (model_path, meta_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (report_dir / "metrics.json").write_text(json.dumps({**metrics, "split_strategy": strategy, "warnings": warns}, indent=2), encoding="utf-8")
    (report_dir / "classification_report.txt").write_text(
        f"Split: {strategy}\nCross-person validated: {cross}\n\n" + classification_report(y[te], pred, labels=present, zero_division=0),
        encoding="utf-8")
    return meta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    try:
        version, signs = load_signs()
        df, notes = load_dataset(DATA_CSV, [s.id for s in trainable(signs)])
        meta = train(df, version, args.seed)
    except DatasetError as exc:
        print(f"ERROR: {exc}")
        return 1
    for w in notes + meta["warnings"]:
        print("WARNING:", w)
    print(f"Split: {meta['split_strategy']}\nSaved {MODEL_PATH.name}; measured: {json.dumps(meta['metrics'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
