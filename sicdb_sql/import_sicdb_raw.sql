CREATE SCHEMA IF NOT EXISTS sicdb;

DROP TABLE IF EXISTS sicdb.cases;
CREATE TABLE sicdb.cases (
    CaseID integer,
    PatientID integer,
    AdmissionYear integer,
    TimeOfStay integer,
    ICUOffset integer,
    saps3 numeric,
    HospitalDischargeType integer,
    HospitalDischargeDay integer,
    HospitalStayDays integer,
    DischargeState integer,
    DischargeUnit integer,
    OffsetOfDeath integer,
    EstimatedSurvivalObservationTime integer,
    Sex integer,
    WeightOnAdmission numeric,
    HeightOnAdmission numeric,
    AgeOnAdmission numeric,
    HospitalUnit integer,
    ReferringUnit integer,
    ICD10Main text,
    ICD10MainText text,
    DiagnosisT2 integer,
    SurgicalSite integer,
    HoursOfCRRT numeric,
    AdmissionUrgency integer,
    AdmissionFormHasSepsis integer,
    SurgicalAdmissionType integer,
    OrbisDataAvailable integer,
    HeartSurgeryAdditionalData integer,
    HeartSurgeryCPBTime numeric,
    HeartSurgeryCrossClampTime numeric,
    HeartSurgeryBeginOffset integer,
    HeartSurgeryEndOffset integer,
    OffsetAfterFirstAdmission integer
);

DROP TABLE IF EXISTS sicdb.d_references;
CREATE TABLE sicdb.d_references (
    ReferenceGlobalID integer,
    ReferenceValue text,
    ReferenceName text,
    ReferenceDescription text,
    ReferenceUnit text,
    ReferenceOrder integer,
    ReferenceType integer,
    Data text,
    LOINC_code text,
    LOINC_short text,
    LOINC_long text
);

DROP TABLE IF EXISTS sicdb.laboratory;
CREATE TABLE sicdb.laboratory (
    id bigint,
    CaseID integer,
    LaboratoryID integer,
    Offset integer,
    LaboratoryValue numeric,
    LaboratoryType integer
);

DROP TABLE IF EXISTS sicdb.medication;
CREATE TABLE sicdb.medication (
    id bigint,
    CaseID integer,
    PatientID integer,
    DrugID integer,
    Offset integer,
    OffsetDrugEnd integer,
    IsSingleDose integer,
    Amount numeric,
    AmountPerMinute numeric,
    GivenState integer
);

DROP TABLE IF EXISTS sicdb.data_float_h;
CREATE TABLE sicdb.data_float_h (
    id bigint,
    CaseID integer,
    DataID integer,
    Offset integer,
    Val numeric,
    cnt integer,
    rawdata text
);

DROP TABLE IF EXISTS sicdb.data_ref;
CREATE TABLE sicdb.data_ref (
    id bigint,
    CaseID integer,
    FieldID integer,
    RefID integer
);

DROP TABLE IF EXISTS sicdb.data_range;
CREATE TABLE sicdb.data_range (
    id bigint,
    CaseID integer,
    DataID integer,
    Offset integer,
    OffsetEnd integer,
    Data text
);

DROP TABLE IF EXISTS sicdb.unitlog;
CREATE TABLE sicdb.unitlog (
    id bigint,
    CaseID integer,
    PatientID integer,
    LogState integer,
    Offset integer,
    HospitalUnit integer
);

\copy sicdb.cases FROM PROGRAM 'gzip -dc F:/SICDB/cases.csv.gz' WITH CSV HEADER
\copy sicdb.d_references FROM PROGRAM 'gzip -dc F:/SICDB/d_references.csv.gz' WITH CSV HEADER
\copy sicdb.laboratory FROM PROGRAM 'gzip -dc F:/SICDB/laboratory.csv.gz' WITH CSV HEADER
\copy sicdb.medication FROM PROGRAM 'gzip -dc F:/SICDB/medication.csv.gz' WITH CSV HEADER
\copy sicdb.data_float_h FROM PROGRAM 'gzip -dc F:/SICDB/data_float_h.csv.gz' WITH CSV HEADER
\copy sicdb.data_ref FROM PROGRAM 'gzip -dc F:/SICDB/data_ref.csv.gz' WITH CSV HEADER
\copy sicdb.data_range FROM PROGRAM 'gzip -dc F:/SICDB/data_range.csv.gz' WITH CSV HEADER
\copy sicdb.unitlog FROM PROGRAM 'gzip -dc F:/SICDB/unitlog.csv.gz' WITH CSV HEADER

CREATE INDEX IF NOT EXISTS idx_sicdb_cases_caseid ON sicdb.cases (CaseID);
CREATE INDEX IF NOT EXISTS idx_sicdb_lab_case_offset ON sicdb.laboratory (CaseID, Offset);
CREATE INDEX IF NOT EXISTS idx_sicdb_lab_id ON sicdb.laboratory (LaboratoryID);
CREATE INDEX IF NOT EXISTS idx_sicdb_med_case_offset ON sicdb.medication (CaseID, Offset);
CREATE INDEX IF NOT EXISTS idx_sicdb_med_drug ON sicdb.medication (DrugID);
CREATE INDEX IF NOT EXISTS idx_sicdb_float_case_data_offset ON sicdb.data_float_h (CaseID, DataID, Offset);
CREATE INDEX IF NOT EXISTS idx_sicdb_ref_id ON sicdb.d_references (ReferenceGlobalID);
CREATE INDEX IF NOT EXISTS idx_sicdb_data_ref_case_field ON sicdb.data_ref (CaseID, FieldID);
CREATE INDEX IF NOT EXISTS idx_sicdb_data_range_case_data ON sicdb.data_range (CaseID, DataID, Offset);
