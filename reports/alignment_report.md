# Alignment measurement

All 446 image/label pairs have matching dimensions and numerical GeoTIFF coordinate-system and raster-interpretation keys. Maximum displacement across the four chip corners: 5.1779135800964641e-11 source pixels. This is consistent with floating-point rounding, not a meaningful pixel-grid shift. No raster files were modified or resampled.

Example pixel spacing: image 0.000089831528411952148 degrees; label 0.000089831528411958572 degrees. Exact equality falsely rejected these almost identical values.

The revised audit uses a conservative absolute tolerance of 0.000001 pixels, requires matching dimensions and CRS, and checks raster pixel interpretation. The four corners bound affine displacement over the rectangular image. This measures grid metadata, not the accuracy of human labels or physical SAR/optical co-registration.

Measurements were executed with scripts/Measure-Alignment.ps1 because this chat cannot access the Python installation. The revised Python audit has not been rerun here. Previous successful band-count and label-value checks are retained; its 445 exact-transform failures were independently resolved using the measured headers. The original audit is preserved as dataset_audit_before_alignment_fix.json.

Per-pair measurements and transforms: alignment_measurements.csv and alignment_measurements.json. Download status was restored from a complete manifest matching all 21,405 inventory objects by name, size, GCS MD5 and generation; the full dataset was not rehashed in this step.
