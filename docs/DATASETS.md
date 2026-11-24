# Dataset inventory — 25 November 2026

Rights were read from the primary repository APIs, not inferred from DOI availability. Evidence snapshots record exact artifact sizes, publisher checksums and retrieval times. Files with participant rows are not included in this repository; manifest evidence is aggregated.

| ID | Version / rights | Source description and identity | Sampling / annotations | Decision |
| --- | --- | --- | --- | --- |
| D1 HRCA | 10.5281/zenodo.4539695, CC BY 4.0, open | 248 dysphagic participants; 3,144 swallows. Participant-to-file mapping not inspected. | 4 kHz microphone + AP/SI/ML acceleration, N×4; onset/offset from 60-fps VFSS; frame origin unknown. | Suitable M0 candidate after approved 1.406-GB signal download and schema check. No PAS labels verified. |
| D2 sEMG/swallow/cough/speech | 10.5522/04/24297766.v1, CC0, open | 11 participants, 4 sessions/participant in protocol; folders P1_S1 etc. | EMG 2 kHz; six CSV columns; labels 0 null, 1 preparation, 2 swallow reflex, 3 cough, 4 speech. Other channel time bases require inspection. | Strict documented-schema adapter with synthetic fixture. 1,123,928,984-byte archive not downloaded. Cancer status is not dysphagia label. |
| D3 EMG and Sound | 10.18742/28528115.v1, King's Internal Access Only | 11 participants described; identifiers and file schema not exposed. | EMG 2.2 kHz, microphone 44.1 kHz in description; task annotations, actual classes unverified. | Blocked: is_embargoed=true and no files exposed. Obtain explicit rights/access before use. |
| D4 Healthy multimodal | 10.18742/33952399.v2, CC BY 4.0, open | 38 participants, 41 sessions; HSDxxx links repeat visits. | Synchronous 20 kHz sound/upper/lower EMG; MAT `data`; processed clips documented/manifested as 40,001×3. | M0 paired acoustic/EMG candidate. Actual signal execution status is in report. Healthy only. |

Primary endpoints: https://zenodo.org/api/records/4539695 and https://api.figshare.com/v2/articles/{24297766,28528115,33952399}. Catalogue descriptions: [D2](https://kclpure.kcl.ac.uk/portal/en/datasets/semg-of-swallowing-coughing-and-speech/), [D3](https://kclpure.kcl.ac.uk/portal/en/datasets/electromyogram-and-sound-of-swallowing-events/), [D4](https://kclpure.kcl.ac.uk/portal/en/datasets/a-multimodal-healthy-swallowing-dataset-of-synchronous-swallowing/).

## D4 manifest audit

4,053 clips: Fluid 820; Saliva 843; Solid 821; Cough 793; ThroatClearing 776. These are publisher activity labels, not clinical labels. Full-length recordings are reported as 2,907; their archive was not approved/downloaded. Five small documentation/manifest files were retrieved and matched publisher size and MD5. The manifest has 4,053 rows with 40,001 samples and 3 columns each. Repeat visits must stay in one participant partition.

A processed event clip can support swallow-versus-cough/throat-clear classification. It cannot establish timing accuracy or false alarms per minute during continuous activities. Publisher PASS selection limits robustness conclusions. Raw QC must not be claimed as reproduced from processed PASS clips.

No source provides all actual SWALLOWGUARD modalities and adjudicated clinical outcomes together. No clinical labels are fabricated, and unrelated recordings are never fused. Clinical performance quoted by source authors is not SWALLOWGUARD performance.

## Entry gate

Before a dataset becomes training-eligible: verify authorized access/license and version; match file size/checksum; inspect actual schema/time base/units; map participant IDs; audit annotations and class counts; run integrity checks; persist subject partitions; document missingness, saturation and QC exclusions. Registry status must reflect actual progress, not planned availability.
