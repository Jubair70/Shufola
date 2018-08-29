from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.maxmodule import views,views_cais

urlpatterns = patterns('',

                       url(r'^batchmodule/batchManagement/$', views.batchManagement, name="batchManagement"),
                       url(r'^batchmodule/createBatchManagementList/$', views.createBatchManagementList, name="createBatchManagementList"),

                       url(r'^batchmodule/batchlist/(?P<selectedBatchForm>[^/]+)/(?P<selectedBatchID>\d+)/$', views.batchlist, name="batchlist"),
                       url(r'^batchmodule/batchDetails/$', views.batchDetails, name="batchDetails"),
                       url(r'^batchmodule/creatingBatchAndBatchDetails/$', views.creatingBatchAndBatchDetails,
                           name="creatingBatchAndBatchDetails"),

                       url(r'^batchmodule/getBatchDelete/$', views.getBatchDelete, name="getBatchDelete"),

                       url(r'^batchmodule/importForCCVerification/$', views.importForCCVerification, name="importForCCVerification"),
                       url(r'^batchmodule/importDataForVerification/$', views.importDataForVerification,
                           name="importDataForVerification"),
                       url(r'^batchmodule/importDataForVerificationListCount/$', views.importDataForVerificationListCount,
                           name="importDataForVerificationListCount"),
                       url(r'^batchmodule/importDataForVerificationDelete/$', views.importDataForVerificationDelete,
                           name="importDataForVerificationDelete"),

                       url(r'^batchmodule/call_center_verification/$', views.call_center_verification,
                           name="call_center_verification"),

                       url(r'^batchmodule/call_center_verification/$', views.call_center_verification,
                           name="call_center_verification"),

                       url(r'^batchmodule/callCenterlist/$',views.callCenterlist, name="callCenterlist"),

                       url(r'^batchmodule/call_center_id_info_checking_page/(?P<selectedID>\d+)/$',views.call_center_id_info_checking_page, name="call_center_id_info_checking_page"),


                        ##**********************  CASI WORK (Start) *******************


                       url(r'^cais_module/crop/$', views_cais.crop, name="crop"),
                       url(r'^cais_module/cropCreate/$', views_cais.cropCreate, name="cropCreate"),
                       url(r'^cais_module/crop_Edit/$', views_cais.crop_Edit, name="crop_Edit"),

                       url(r'^cais_module/crop_Stage/$', views_cais.crop_Stage, name="crop_Stage"),
                       url(r'^cais_module/cropStageCreate/$', views_cais.cropStageCreate, name="cropStageCreate"),
                       url(r'^cais_module/crop_Stage_Edit/$', views_cais.crop_Stage_Edit, name="crop_Stage_Edit"),

                       url(r'^cais_module/crop_stage_alert/$', views_cais.crop_stage_alert, name="crop_stage_alert"),
                       url(r'^cais_module/cropStageAlertCreate/$', views_cais.cropStageAlertCreate, name="cropStageAlertCreate"),
                       url(r'^cais_module/crop_stage_alert_Edit/$', views_cais.crop_stage_alert_Edit, name="crop_stage_alert_Edit"),
                       url(r'^cais_module/alert_sms_stage_list/$', views_cais.alert_sms_stage_list, name="alert_sms_stage_list"),


                       url(r'^cais_module/group_details/$', views_cais.group_details, name="group_details"),
                       url(r'^cais_module/groupCreate/$', views_cais.groupCreate, name="groupCreate"),
                       url(r'^cais_module/group_details_Edit/$', views_cais.group_details_Edit, name="group_details_Edit"),




                       url(r'^cais_module/crop_group/$', views_cais.crop_group, name="crop_group"),
                       url(r'^cais_module/cropGroupCreate/$', views_cais.cropGroupCreate, name="cropGroupCreate"),
                       url(r'^cais_module/crop_group_Edit/$', views_cais.crop_group_Edit, name="crop_group_Edit"),



                       url(r'^cais_module/farmer/$', views_cais.farmer, name="farmer"),
                       url(r'^cais_module/farmerCreate/$', views_cais.farmerCreate, name="farmerCreate"),
                       url(r'^cais_module/farmer_Edit/$', views_cais.farmer_Edit, name="farmer_Edit"),


                       url(r'^cais_module/farmer_group/$', views_cais.farmer_group, name="farmer_group"),
                       url(r'^cais_module/farmer_groupCreate/$', views_cais.farmer_groupCreate, name="farmer_groupCreate"),
                       url(r'^cais_module/farmer_group_Edit/$', views_cais.farmer_group_Edit,
                           name="farmer_group_Edit"),
                       url(r'^cais_module/includedGroupCropList/$', views_cais.includedGroupCropList, name="includedGroupCropList"),
                       url(r'^cais_module/groupNameForEdit/$', views_cais.groupNameForEdit, name="groupNameForEdit"),
                       url(r'^cais_module/groupCropNameForEdit/$', views_cais.groupCropNameForEdit, name="groupCropNameForEdit"),




                       url(r'^cais_module/getUpazilas/$', views_cais.getUpazilas, name="getUpazilas"),
                       url(r'^cais_module/getUnions/$', views_cais.getUnions, name="getUnions"),

                       url(r'^cais_module/alert_sms_process/$', views_cais.alert_sms_process, name="alert_sms_process"),
                       url(r'^cais_module/alert_sms_process_crop_list/$', views_cais.alert_sms_process_crop_list, name="alert_sms_process_crop_list"),
                       url(r'^cais_module/alert_sms_process_stage_name/$', views_cais.alert_sms_process_stage_name,
                           name="alert_sms_process_stage_name"),

                       url(r'^cais_module/alert_sms_process_alert_list/$', views_cais.alert_sms_process_alert_list,
                           name="alert_sms_process_alert_list"),
                       url(r'^cais_module/alert_sms_process_alert_sms/$', views_cais.alert_sms_process_alert_sms,
                           name="alert_sms_process_alert_sms"),
                       url(r'^cais_module/alert_sms_process_info_store/$', views_cais.alert_sms_process_info_store,
                           name="alert_sms_process_info_store"),
                       url(r'^cais_module/alert_sms_process_Edit/$', views_cais.alert_sms_process_Edit,
                           name="alert_sms_process_Edit"),








                       ##**********************  CASI WORK (End) *******************



                       )
