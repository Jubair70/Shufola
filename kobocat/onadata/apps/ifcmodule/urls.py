from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.ifcmodule import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^program_list/$', views.program_list, name='program_list'),
    url(r'^add_program_form/$', views.add_program_form, name='add_program_form'),
    url(r'^insert_program_form/$', views.insert_program_form, name='insert_program_form'),
    url(r'^edit_program_form/(?P<program_id>\d+)/$', views.edit_program_form,name='edit_program_form'),
    url(r'^update_program_form/$', views.update_program_form, name='update_program_form'),
    url(r'^delete_program_form/(?P<program_id>\d+)/$', views.delete_program_form,name='delete_program_form'),
    )
