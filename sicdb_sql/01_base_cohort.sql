-- Adult ICU cases from SICdb.
-- Adjust column names if your local import lowercases identifiers.

DROP TABLE IF EXISTS saki_sicdb.base_icu;
CREATE TABLE saki_sicdb.base_icu AS
SELECT
    c.CaseID AS stay_id,
    c.PatientID AS subject_id,
    c.CaseID AS hadm_id,
    c.Sex AS gender,
    c.Age AS age,
    c.Weight AS admissionweight,
    c.AdmissionOffset AS icu_intime,
    c.DischargeOffset AS icu_outtime,
    c.DischargeOffset / 86400.0 AS los_icu,
    c.DischargeStatus AS unitdischargestatus,
    c.HospitalDischargeStatus AS hospitaldischargestatus
FROM sicdb.cases c
WHERE c.Age >= 18
  AND c.DischargeOffset >= 86400;

