-- Adult first ICU stays from public.
-- eICU has one row per ICU stay in patient.

DROP TABLE IF EXISTS saki_eicu.base_icu;
CREATE TABLE saki_eicu.base_icu AS
SELECT
    p.patientunitstayid AS stay_id,
    p.uniquepid AS subject_id,
    p.patienthealthsystemstayid AS hadm_id,
    p.gender,
    CASE
        WHEN p.age = '> 89' THEN 90
        WHEN p.age ~ '^[0-9]+$' THEN CAST(p.age AS INTEGER)
        ELSE NULL
    END AS age,
    p.ethnicity AS race,
    p.apacheadmissiondx,
    p.admissionheight,
    p.admissionweight,
    p.unitadmitsource,
    p.unittype,
    p.unitdischargeoffset,
    p.hospitaldischargeoffset,
    p.unitdischargestatus,
    p.hospitaldischargestatus
FROM public.patient p
WHERE (
        CASE
            WHEN p.age = '> 89' THEN 90
            WHEN p.age ~ '^[0-9]+$' THEN CAST(p.age AS INTEGER)
            ELSE NULL
        END
    ) >= 18
  AND p.unitdischargeoffset >= 1440;

-- Optional: keep first ICU stay per unique patient if desired.
-- eICU does not always provide clean cross-hospital chronology; patientunitstayid-level validation is common.

