# Dataset licence evidence

Checked 2026-10-22.

Confirmed metadata declaration: proprietary.

Both official STAC collections explicitly contain `"license": "proprietary"`:

- Sentinel-1 source: https://storage.googleapis.com/sen1floods11/v1.1/catalog/sen1floods11_hand_labeled_source/collection.json
- Hand labels: https://storage.googleapis.com/sen1floods11/v1.1/catalog/sen1floods11_hand_labeled_label/collection.json

Exact downloaded collection snapshots are saved under metadata/upstream/ and hashed in metadata/licence_evidence_sha256.csv.

The publisher README provides public download instructions and asks users to cite Bonafilia, Tellman, Anderson and Issenberg (2020), Sen1Floods11: A Georeferenced Dataset to Train and Test Deep Learning Algorithms for Sentinel-1, CVPR Workshops.

The repository's missing-LICENSE issue remains open: https://github.com/cloudtostreet/Sen1Floods11/issues/18

No authoritative CC BY grant was verified. `proprietary` is a metadata declaration, not a full statement of training, redistribution, derivative-output or commercial-use permissions. Those permissions remain unresolved; obtain the publisher's actual terms before claiming an open-data licence or publishing dataset copies. Third-party mirrors do not establish upstream terms. No clarification message has been sent on your behalf.
