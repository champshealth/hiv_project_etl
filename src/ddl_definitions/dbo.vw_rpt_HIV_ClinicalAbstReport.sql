-- VIEW
-- Schema: dbo
-- Name: vw_rpt_HIV_ClinicalAbstReport
-- Generated: 2025-02-26 22:17:56.964602

CREATE view /*CHAMPS_QA*/ [dbo].[vw_rpt_HIV_ClinicalAbstReport] as 
select ChampsId,  concat(rpt.ReportUri,ChampsId) ReportUri,rpt.ReportSequence, PackageType
 from  (select ChampsId ,  
        case when FormName = 'diagnostic_testing' then 'Adult-HIV-CA-diagnostic_testing'
        when FormName = 'hospital_course' then 'Adult-HIV-CA-hospital_course'
        when FormName = 'medications_and_interventions' then 'Adult-HIV-CA-medication_and_inteventions'
        when FormName = 'past_history' then 'Adult-HIV-CA-past_history'
        when FormName = 'present_illness' then 'Adult-HIV-CA-present_illness'
        when FormName = 'source_information' then 'Adult-HIV-CA-source_info'
        end as ReportViewName
        from stg.vw_HIVClinicalAbstr_rpt
        -- where ChampsId = 'DWHV00003'
        group by ChampsId,FormName 
        UNION ALL
        select ChampsId, case when FormName = 'initial_death_notification' then 'Adult-HIV-Project1_1-initial_death_notification'
        when FormName = 'death_notification_management' then 'Adult-HIV-Project1_1-death_notification_management'
        when FormName = 'eligibility_screening_form' then 'Adult-HIV-Project1_1-eligibility_screening_form'
        when FormName = 'consent_tracking' then 'Adult-HIV-Project1_1-consent_tracking'
        end as ReportViewName
        from stg.vw_HIVProject1_1
        where ChampsId <> ''
        group by ChampsId, FormName
        UNION ALL
        select ChampsId, concat('Adult-HIV-Project3_1-', FormName ) ReportViewName
        from stg.vw_HIVProject3_1_rpt
        group by ChampsId,FormName 
        ) form_data
join [stg].[rpt_HIVReportName] rpt on form_data.ReportViewName = rpt.ReportViewName