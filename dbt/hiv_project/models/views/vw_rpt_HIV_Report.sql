{{
  config(
    materialized = 'view',
    schema = 'hiv'
  )
}}

-- Portal calls this view to generate the Tableau reports for a case for the HIV project
SELECT 
    ChampsId,  
    CONCAT(rpt.ReportUri, ChampsId) AS ReportUri,
    rpt.ReportSequence, 
    PackageType
FROM (
    SELECT 
        ChampsId,  
        CASE 
            WHEN FormName = 'diagnostic_testing' THEN 'Adult-HIV-CA-diagnostic_testing'
            WHEN FormName = 'hospital_course' THEN 'Adult-HIV-CA-hospital_course'
            WHEN FormName = 'medications_and_interventions' THEN 'Adult-HIV-CA-medication_and_inteventions'
            WHEN FormName = 'past_history' THEN 'Adult-HIV-CA-past_history'
            WHEN FormName = 'present_illness' THEN 'Adult-HIV-CA-present_illness'
            WHEN FormName = 'source_information' THEN 'Adult-HIV-CA-source_info'
        END AS ReportViewName
    FROM {{ ref('vw_HIVClinicalAbstr_rpt') }}
    -- WHERE ChampsId = 'DWHV00003'
    GROUP BY ChampsId, FormName 
    
    UNION ALL
    
    SELECT 
        ChampsId, 
        CASE 
            WHEN FormName = 'initial_death_notification' THEN 'Adult-HIV-Project1_1-initial_death_notification'
            WHEN FormName = 'death_notification_management' THEN 'Adult-HIV-Project1_1-death_notification_management'
            WHEN FormName = 'eligibility_screening_form' THEN 'Adult-HIV-Project1_1-eligibility_screening_form'
            WHEN FormName = 'consent_tracking' THEN 'Adult-HIV-Project1_1-consent_tracking'
        END AS ReportViewName
    FROM {{ ref('vw_HIVProject1_1') }}
    WHERE ChampsId <> ''
    GROUP BY ChampsId, FormName
    
    UNION ALL
    
    SELECT 
        ChampsId, 
        CONCAT('Adult-HIV-Project3_1-', FormName) AS ReportViewName
    FROM {{ ref('vw_HIVProject3_1_rpt') }}
    GROUP BY ChampsId, FormName 
) form_data
JOIN {{ ref('rpt_HIVReportName') }} rpt ON form_data.ReportViewName = rpt.ReportViewName