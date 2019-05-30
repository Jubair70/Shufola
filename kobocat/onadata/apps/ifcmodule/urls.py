from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.ifcmodule import views, views_api

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^program_list/$', views.program_list, name='program_list'),
                       url(r'^add_program_form/$', views.add_program_form, name='add_program_form'),
                       url(r'^insert_program_form/$', views.insert_program_form, name='insert_program_form'),
                       url(r'^edit_program_form/(?P<program_id>\d+)/$', views.edit_program_form,
                           name='edit_program_form'),
                       url(r'^update_program_form/$', views.update_program_form, name='update_program_form'),
                       url(r'^delete_program_form/(?P<program_id>\d+)/$', views.delete_program_form,
                           name='delete_program_form'),
                       url(r'^farmer_profile_view/(?P<farmer_id>\d+)/$', views.farmer_profile_view,
                           name='farmer_profile_view'),
                       url(r'^add_crop/(?P<farmer_id>\d+)/$', views.add_crop_form, name='add_crop_form'),
                       url(r'^add_crop/get_same_geo_locatio_as_farmer/$', views.get_same_geo_locatio_as_farmer,
                           name='get_same_geo_locatio_as_farmer'),
                       url(r'^getVariety/$', views.getVariety, name='getVariety'),
                       url(r'^insert_crop_form/$', views.insert_crop_form, name='insert_crop_form'),
                       url(r'^change_status/$', views.change_status, name='change_status'),
                       url(r'^change_multiple_farmer_status/$', views.change_multiple_farmer_status, name='change_multiple_farmer_status'),
                       url(r'^management_sms_form/$', views.management_sms_form, name='management_sms_form'),
                       url(r'^management_sms_form/(?P<content_id>\d+)/$', views.management_sms_form_for_content, name='management_sms_form_for_content'),
                       url(r'^getProgram/$', views.getProgram, name='getProgram'),
                       url(r'^insert_management_sms_form/$', views.insert_management_sms_form,
                           name='insert_management_sms_form'),
                       url(r'^weather_forecast/$', views.weather_forecast, name='weather_forecast'),
                       url(r'^update_stage/$', views.update_stage, name='update_stage'),
                       url(r'^getStage/$', views.getStage, name='getStage'),
                       url(r'^management_sms_rule_list/$', views.management_sms_rule_list,
                           name='management_sms_rule_list'),
                       url(r'^edit_management_sms_form/(?P<sms_rule_id>\d+)/$', views.edit_management_sms_form,
                           name='edit_management_sms_form'),
                       url(r'^update_management_sms_form/$', views.update_management_sms_form,
                           name='update_management_sms_form'),
                       url(r'^delete_management_sms_form/(?P<sms_rule_id>\d+)/$', views.delete_management_sms_form,
                           name='delete_management_sms_form'),
                       url(r'^weather_sms_rule_list/$', views.weather_sms_rule_list, name='weather_sms_rule_list'),
                       url(r'^weather_sms_form/$', views.weather_sms_form, name='weather_sms_form'),
                       url(r'^insert_weather_sms_form/$', views.insert_weather_sms_form,
                           name='insert_weather_sms_form'),
                       url(r'^getSubParameter/$', views.getSubParameter, name='getSubParameter'),
                       url(r'^delete_weather_sms_form/(?P<sms_rule_id>\d+)/$', views.delete_weather_sms_form,
                           name='delete_weather_sms_form'),
                       url(r'^edit_weather_sms_form/(?P<sms_rule_id>\d+)/$', views.edit_weather_sms_form,
                           name='edit_weather_sms_form'),
                       url(r'^update_weather_sms_form/$', views.update_weather_sms_form,
                           name='update_weather_sms_form'),
                       url(r'^weather_observed/$', views.weather_observed, name='weather_observed'),
                       url(r'^get_farmers_sms/$', views.get_farmers_sms, name='get_farmers_sms'),
                       url(r'^sms_list/$', views.sms_list, name='sms_list'),
                       url(r'^get_sms_table/$', views.get_sms_table, name='get_sms_table'),
                       url(r'^send_sms/(?P<id>\d+)/$', views.send_sms, name='send_sms'),
                       url(r'^weather_sms_que_list/$', views.weather_sms_que_list, name='weather_sms_que_list'),
                       url(r'^approve_farmer_sms/$', views.approve_farmer_sms, name='approve_farmer_sms'),
                       url(r'^reject_farmer_sms/$', views.reject_farmer_sms, name='reject_farmer_sms'),
                       url(r'^getDivisions/$', views.getDivisions, name='getDivisions'),
                       url(r'^getDistricts/$', views.getDistricts, name='getDistricts'),
                       url(r'^getUpazillas/$', views.getUpazillas, name='getUpazillas'),
                       url(r'^getUnions/$', views.getUnions, name='getUnions'),
                       url(r'^getWeatherQueueData/$', views.getWeatherQueueData, name='getWeatherQueueData'),
                       url(r'^management_sms_que_list/$', views.management_sms_que_list,
                           name='management_sms_que_list'),
                       url(r'^approve_farmer_sms_management/$', views.approve_farmer_sms_management,
                           name='approve_farmer_sms_management'),
                       url(r'^reject_farmer_sms_management/$', views.reject_farmer_sms_management,
                           name='reject_farmer_sms_management'),
                       url(r'^getManagementQueueData/$', views.getManagementQueueData, name='getManagementQueueData'),

                       url(r'^promotional_sms_form/$', views.promotional_sms_form, name='promotional_sms_form'),
                       url(r'^promotional_sms_form/(?P<content_id>\d+)/$', views.promotional_sms_form_for_content, name='promotional_sms_form_for_content'),
                       url(r'^promotional_sms_history/$', views.promotional_sms_history, name='promotional_sms_history'),
                       url(r'^promotional_schedule_sms_history/$', views.promotional_schedule_sms_history, name='promotional_schedule_sms_history'),
                       url(r'^promotional_sms_history_map/$', views.promotional_sms_history_map, name='promotional_sms_history_map'),
                       url(r'^insert_promotional_sms_form/$', views.insert_promotional_sms_form,
                           name='insert_promotional_sms_form'),
                       url(r'^insert_promotional_sms_form_with_schedule/$', views.insert_promotional_sms_form_with_schedule,
                           name='insert_promotional_sms_form_with_schedule'),
                       url(r'^promotional_sms_list/$', views.promotional_sms_list, name='promotional_sms_list'),

                       url(r'^data_graph_view/$', views.data_graph_view, name='data_graph_view'),
                       url(r'^getGraphData/$', views.getGraphData, name='getGraphData'),
                       url(r'^edit_crop_form/(?P<farmer_id>\d+)/(?P<farmer_crop_id>\d+)/$', views.edit_crop_form,
                           name='edit_crop_form'),
                       url(r'^update_crop_form/$', views.update_crop_form, name='update_crop_form'),
                       url(r'^weather_farmer_xls_list/$', views.weather_farmer_xls_list,
                           name='weather_farmer_xls_list'),
                       url(r'^management_farmer_xls_list/$', views.management_farmer_xls_list,
                           name='management_farmer_xls_list'),
                       url(r'^sms_log/$', views.sms_log, name='sms_log'),
                       url(r'^sms_log_old/$', views.sms_log_old, name='sms_log_old'),
                       url(r'^export_sms_log/$', views.export_sms_log, name='export_sms_log'),
                       url(r'^bulk_upload/$', views.bulk_upload, name='bulk_upload'),
                       url(r'^getSMSLogData/$', views.getSMSLogData, name='getSMSLogData'),
                       url(r'^getSMSLogDataNew/$', views.getSMSLogDataNew, name='getSMSLogDataNew'),


                       url(r'^weather_forecast_list/$', views.weather_forecast_list, name='weather_forecast_list'),
                       url(r'^getWeatherForecastList/$', views.getWeatherForecastList, name='getWeatherForecastList'),
                       url(r'^getWeatherForecastGraphData/$', views.getWeatherForecastGraphData, name='getWeatherForecastGraphData'),
                       url(r'^getDailyWeatherForecastList/$', views.getDailyWeatherForecastList, name='getDailyWeatherForecastList'),


                       url(r'^weather_observed_list/$', views.weather_observed_list, name='weather_observed_list'),
                       url(r'^getWeatherObservedList/$', views.getWeatherObservedList, name='getWeatherObservedList'),
                       url(r'^getWeatherObservedGraphData/$', views.getWeatherObservedGraphData, name='getWeatherObservedGraphData'),
                       url(r'^getDailyWeatherObservedList/$', views.getDailyWeatherObservedList, name='getDailyWeatherObservedList'),


                       url(
                           r'^get_daily_weather_information/(?P<type>[^/]+)/(?P<location>[^/]+)/(?P<from_date>[^/]+)/(?P<to_date>[^/]+)/$',
                           views_api.get_daily_weather_information),
                       url(
                           r'^get_hourly_weather_information/(?P<type>[^/]+)/(?P<location>[^/]+)/(?P<from_date>[^/]+)/(?P<to_date>[^/]+)/$',
                           views_api.get_hourly_weather_information),
                       url(r'^get_load_offset_max/$', views.get_load_offset_max, name='get_load_offset_max'),

                       #Dashboard
                       url(r'^get_dashboard/$', views.get_dashboard, name='get_dashboard'),
                       url(r'^dashboard/program/graph/$', views.get_program_graph, name='get_program_graph'),
                       url(r'^dashboard/program/table/$', views.get_program_table, name='get_program_table'),

                       url(r'^dashboard/crop/$', views.get_crop, name='get_crop'),

                       url(r'^dashboard/farmer/map/$', views.get_farmer_map, name='get_farmer_map'),
                       url(r'^dashboard/farmer/bar/$', views.get_farmer_bar, name='get_farmer_bar'),
                       url(r'^dashboard/farmer/table/$', views.get_farmer_table, name='get_farmer_table'),
                       url(r'^dashboard/farmer/table/activity_history/$', views.get_farmer_table_activity_history, name='get_farmer_table_activity_history'),

                       url(r'^dashboard/sms/map/$', views.get_sms_map, name='get_sms_map'),
                       url(r'^dashboard/sms/bar/$', views.get_sms_bar, name='get_sms_bar'),

                       url(r'^dashboard/voice_sms/map/$', views.get_voice_sms_map, name='get_voice_sms_map'),
                       url(r'^dashboard/voice_sms/bar/$', views.get_voice_sms_bar, name='get_voice_sms_bar'),

                       url(r'^dashboard/area/$', views.get_area, name='get_area'),

                       url(r'^content_library/$', views.content_library, name='content_library'),
                       url(r'^edit_content/(?P<id>\d+)/$', views.edit_content_library, name='edit_content_library'),
                       url(r'^create_content/$', views.create_content, name='create_content'),
                       url(r'^insert_content_form/$', views.insert_content_form, name='insert_content_form'),
                       url(r'^update_content_form/(?P<id>\d+)/$', views.update_content_form, name='update_content_form'),
                       url(r'^weather_observed_info/$', views.weather_observed_info, name='weather_observed_info'),
                       url(r'^weather_forecast_info/$', views.weather_forecast_info, name='weather_forecast_info'),

                       url(r'^getMapData/$', views.getMapData, name='getMapData'),

                       )
