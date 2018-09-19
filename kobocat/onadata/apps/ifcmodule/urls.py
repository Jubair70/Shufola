from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.ifcmodule import views

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
                       url(r'^add_crop/get_same_geo_locatio_as_farmer/$', views.get_same_geo_locatio_as_farmer, name='get_same_geo_locatio_as_farmer'),
                       url(r'^getVariety/$', views.getVariety, name='getVariety'),
                       url(r'^insert_crop_form/$', views.insert_crop_form, name='insert_crop_form'),
                       url(r'^change_status/$', views.change_status, name='change_status'),
                       url(r'^management_sms_form/$', views.management_sms_form, name='management_sms_form'),
                       url(r'^getProgram/$', views.getProgram, name='getProgram'),
                       url(r'^insert_management_sms_form/$', views.insert_management_sms_form,
                           name='insert_management_sms_form'),
                       url(r'^weather_forecast/$', views.weather_forecast, name='weather_forecast'),
                       url(r'^update_stage/$', views.update_stage, name='update_stage'),
                       )
