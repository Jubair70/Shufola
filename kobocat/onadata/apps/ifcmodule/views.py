#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (
    HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth.models import User
from datetime import date, timedelta, datetime
# from django.utils import simplejson
import json
import logging
import sys
import operator
import pandas
from django.shortcuts import render
import numpy
import time
import datetime
from django.core.files.storage import FileSystemStorage

from django.core.urlresolvers import reverse

from datetime import date, timedelta, datetime
from django.db import (IntegrityError, transaction)
from django.db.models import ProtectedError
from django.shortcuts import redirect
from onadata.apps.main.models.user_profile import UserProfile
from onadata.apps.usermodule.forms import UserForm, UserProfileForm, ChangePasswordForm, UserEditForm, OrganizationForm, \
    OrganizationDataAccessForm, ResetPasswordForm
from onadata.apps.usermodule.models import UserModuleProfile, UserPasswordHistory, UserFailedLogin, Organizations, \
    OrganizationDataAccess

from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
# Menu imports
from onadata.apps.usermodule.forms import MenuForm
from onadata.apps.usermodule.models import MenuItem
# Unicef Imports
from onadata.apps.logger.models import Instance, XForm
# Organization Roles Import
from onadata.apps.usermodule.models import OrganizationRole, MenuRoleMap, UserRoleMap
from onadata.apps.usermodule.forms import OrganizationRoleForm, RoleMenuMapForm, UserRoleMapForm, UserRoleMapfForm
from django.forms.models import inlineformset_factory, modelformset_factory
from django.forms.formsets import formset_factory

from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from collections import OrderedDict
import decimal
import os
import shutil


def __db_fetch_values(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall()
    cursor.close()
    return fetchVal


def __db_fetch_single_value(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchone()
    cursor.close()
    return fetchVal[0]


def __db_fetch_values_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = dictfetchall(cursor)
    cursor.close()
    return fetchVal


def __db_commit_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


def decimal_date_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return obj
    raise TypeError


def makeTableList(tableListQuery):
    cursor = connection.cursor()
    cursor.execute(tableListQuery)
    tableList = list(cursor.fetchall())
    return tableList


def singleValuedQuryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = list(cursor.fetchone())
    cursor.close()
    return value


def index(request):
    return render(request, 'ifcmodule/index.html')


@login_required
def program_list(request):
    query = "select id,program_name,(select organization from usermodule_organizations where id = org_id limit 1) org_name  from usermodule_programs"
    program_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'ifcmodule/program_list.html', {
        'program_list': program_list
    })


@login_required
def add_program_form(request):
    query = "select id,organization from usermodule_organizations"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)
    return render(request, 'ifcmodule/add_program_form.html', {'organization': organization})


@login_required
def insert_program_form(request):
    if request.POST:
        program = request.POST.get('program')
        org_id = request.POST.get('org_id')
        insert_query = "INSERT INTO public.usermodule_programs ( program_name, org_id) VALUES('" + str(
            program) + "', " + str(org_id) + ")"
        __db_commit_query(insert_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> New Program has been added successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/program_list/")


@login_required
def edit_program_form(request, program_id):
    query = "select program_name,org_id  from usermodule_programs where id=" + str(
        program_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    program_name = df.program_name.tolist()[0]
    set_org_id = df.org_id.tolist()[0]

    query = "select id,organization from usermodule_organizations"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    return render(request, 'ifcmodule/edit_program_form.html',
                  {'organization': organization, 'set_org_id': set_org_id,
                   'program_id': program_id, 'program_name': program_name
                   })


@login_required
def update_program_form(request):
    if request.POST:
        program_id = request.POST.get('program_id')
        program = request.POST.get('program')
        org_id = request.POST.get('org_id')
        update_query = "UPDATE public.usermodule_programs SET program_name='" + str(program) + "', org_id=" + str(
            org_id) + "  WHERE id=" + str(program_id)
        __db_commit_query(update_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> Program Info has been updated successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/program_list/")


@login_required
def delete_program_form(request, program_id):
    delete_query = "delete from usermodule_programs where id = " + str(program_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> Program Info has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/program_list/")


@login_required
def farmer_profile_view(request, farmer_id):
    # Farmer Details Information Query
    query = "select farmer_name,(select name from geo_district where id = district_id limit 1) district_name ,(select name from geo_upazilla where id = upazila_id limit 1) upazilla_name ,(select name from geo_union where id = union_id limit 1) union_name,mobile_number,(select organization from usermodule_organizations where id = organization_id limit 1)organization,(select program_name from usermodule_programs where id = program_id limit 1) as program,status from farmer where organization_id is not null and program_id is not null and id = " + str(
        farmer_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    farmer_name = df.farmer_name.tolist()[0]
    district_name = df.district_name.tolist()[0]
    upazilla_name = df.upazilla_name.tolist()[0]
    union_name = df.union_name.tolist()[0]
    mobile_number = df.mobile_number.tolist()[0]
    organization = df.organization.tolist()[0]
    program = df.program.tolist()[0]
    status = df.status.tolist()[0]

    # Crop List
    query = "select (select crop_name from crop where id = crop_id limit 1)," \
            "(select season_name from cropping_season where id = season_id limit 1)," \
            "(select variety_name from crop_variety where id = crop_variety_id)," \
            "sowing_date,land_size || ' '|| (select unit_name from land_units where id = unit_id limit 1) land_size , (select name from geo_district where id = district_id )district_name, " \
            "(select name from geo_upazilla where id = upazila_id )upazila_name , " \
            "(select name from geo_union where id = union_id )union_name " \
            "from farmer_crop_info where farmer_id = " + str(
        farmer_id)
    crop_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)


    return render(request, 'ifcmodule/farmer_profile_view.html',
                  {'farmer_name': farmer_name
                      , 'district_name': district_name
                      , 'upazilla_name': upazilla_name
                      , 'union_name': union_name
                      , 'mobile_number': mobile_number
                      , 'organization': organization
                      , 'program': program
                      , 'farmer_id': farmer_id
                      , 'crop_list': crop_list
                      , 'status': status})


@login_required
def add_crop_form(request, farmer_id):
    query = "select id, name , code from geo_zone"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    zone_id = df.id.tolist()
    zone_name = df.name.tolist()
    zone = zip(zone_id, zone_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop = zip(crop_id, crop_name)

    query = "select id,unit_name from land_units"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    unit_id = df.id.tolist()
    unit_name = df.unit_name.tolist()
    unit = zip(unit_id, unit_name)

    return render(request, 'ifcmodule/add_crop_form.html',
                  {'farmer_id': farmer_id, 'zone': zone, 'season': season, 'crop': crop, 'unit': unit})


@login_required
def get_same_geo_locatio_as_farmer(request):
    farmer_id = request.POST.get('farmer_id')

    querySameGeoAsFarmer = "SELECT id, zone_id, district_id, upazila_id, union_id FROM public.farmer where id = " + str(
        farmer_id);
    getSameGeoAsFarmer = singleValuedQuryExecution(querySameGeoAsFarmer)

    zoneQuery = "select id,name from geo_zone "
    zone_List = makeTableList(zoneQuery)

    districtQuery = "select id,name from geo_district where geo_zone_id =" + str(getSameGeoAsFarmer[1])
    district_List = makeTableList(districtQuery)

    upazilaQuery = "select id,name from geo_upazilla where geo_district_id =" + str(getSameGeoAsFarmer[2])
    upazila_List = makeTableList(upazilaQuery)
    # jsonUpaList = json.dumps({'upazila_List': upazila_List}, default=decimal_date_default)

    unionQuery = "select id,name from geo_union where geo_upazilla_id = " + str(getSameGeoAsFarmer[3])
    union_List = makeTableList(unionQuery)
    # jsonUnionList = json.dumps({'union_List': union_List}, default=decimal_date_default)

    jsonFetchSelectedFarmer = json.dumps({'getSameGeoAsFarmer': getSameGeoAsFarmer,
                                          'zone_List': zone_List,
                                          'district_List': district_List,
                                          'upazila_List': upazila_List,
                                          'union_List': union_List,
                                          }, default=decimal_date_default)
    return HttpResponse(jsonFetchSelectedFarmer)


@login_required
def getVariety(request):
    crop_id = request.POST.get('obj')
    query = "select id,variety_name from crop_variety where crop_id = " + str(crop_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@login_required
def insert_crop_form(request):
    if request.POST:
        farmer_id = request.POST.get('farmer_id')
        zone_id = request.POST.get('zone_id')
        district_id = request.POST.get('district_id')
        upazila_id = request.POST.get('upazila_id')
        union_id = request.POST.get('union_id')
        season = request.POST.get('season')
        crop = request.POST.get('crop')
        crop_variety = request.POST.get('crop_variety')
        sowing_date = request.POST.get('sowing_date')
        unit = request.POST.get('unit')
        land_size = request.POST.get('land_size')
        user_id = request.user.id
        insert_query = "INSERT INTO public.farmer_crop_info(farmer_id,zone_id , district_id , upazila_id, union_id , crop_id, season_id, crop_variety_id, sowing_date, unit_id, land_size, created_at, created_by, updated_at, updated_by) " \
                       " VALUES(" + str(farmer_id) + ", " + str(zone_id) + " , " + str(district_id) + " , " + str(
            upazila_id) + " , " + str(union_id) + " , " + str(crop) + ", " + str(season) + ", " + str(
            crop_variety) + ", '" + str(sowing_date) + "', " + str(unit) + ", '" + str(land_size) + "', now(), " + str(
            user_id) + ", now(), " + str(user_id) + ")"
        __db_commit_query(insert_query)
        messages.success(request,
                         '<i class="fa fa-check-circle"></i>New Crop Info has been added to this farmer successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/farmer_profile_view/" + str(farmer_id) + "/")


@login_required
def change_status(request):
    status = abs(int(request.POST.get('status')) - 1)
    farmer_id = request.POST.get('farmer_id')
    query = " update farmer set status = " + str(status) + " where id=" + str(farmer_id)
    __db_commit_query(query)
    return HttpResponse("")


@login_required
def management_sms_form(request):
    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop = zip(crop_id, crop_name)

    query = "select id,organization from usermodule_organizations"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)
    return render(request, 'ifcmodule/management_sms_form.html',
                  {'organization': organization, 'season': season, 'crop': crop})


@login_required
def promotional_sms_form(request):
    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop = zip(crop_id, crop_name)

    query = "select id,organization from usermodule_organizations"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select distinct geo_country_id,country_name from vwunion"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    country_id = df.geo_country_id.tolist()
    country_name = df.country_name.tolist()
    country = zip(country_id, country_name)

    return render(request, 'ifcmodule/promotional_sms_form.html',
                  {'organization': organization,'season': season, 'crop': crop,'country':country})


@login_required
def promotional_sms_list(request):
    query = "select 'Promotional/Broadcast' category_name,coalesce((select organization from usermodule_organizations where id::text = organization_id limit 1),'All') organization_name, coalesce((select program_name from usermodule_programs where id::text = program_id limit 1),'All') program_name, coalesce((select crop_name from crop where id::text = crop_id limit 1),'All') crop_name, coalesce((select variety_name from crop_variety where id::text = variety_id limit 1),'All') variety_name, coalesce((select season_name from cropping_season where id::text = season_id limit 1),'All') season_name, coalesce((select name from geo_country where id::text = country_id limit 1),'All') country_name, coalesce((select name from geo_zone where id::text = division_id limit 1),'All') division_name, coalesce((select name from geo_district where id::text = district_id limit 1),'All') district_name, coalesce((select name from geo_upazilla where id::text = upazilla_id limit 1),'All') upazilla_name, coalesce((select name from geo_union where id::text = union_id limit 1),'All') union_name,sms_description,mobile_number,farmer_name from promotional_sms"
    promotional_sms_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'ifcmodule/promotional_sms_list.html', {
        'promotional_sms_list': promotional_sms_list
    })


@login_required
def insert_promotional_sms_form(request):
    if request.POST:
        category_id = request.POST.get('category')
        sms_description = request.POST.get('sms_description')
        sms_description = sms_description.encode('utf-8').strip()
        org_id = request.POST.get('organization')
        program_id = request.POST.get('program')
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')
        country_id = request.POST.get('country')
        division_id = request.POST.get('division')
        district_id = request.POST.get('district')
        upazilla_id = request.POST.get('upazilla')
        union_id = request.POST.get('union')
        username = request.user.username
        voice_sms_file_path = ""
        if "voice_sms" in request.FILES:
            myfile = request.FILES['voice_sms']
            url = "onadata/media/uploaded_files/"
            userName = request.user
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            voice_sms_file_path = "onadata/media/uploaded_files/" + myfile.name

        insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by) select '"+str(org_id)+"', '"+str(program_id)+"', '"+str(crop_id)+"', '"+str(variety_id)+"', '"+str(season_id)+"', '"+str(country_id)+"', '"+str(division_id)+"', '"+str(district_id)+"', '"+str(upazilla_id)+"', '"+str(union_id)+"', id farmer_id,farmer_name,mobile_number::text,'"+str(sms_description)+"','"+str(username)+"' from farmer where country_id::text LIKE '"+str(country_id)+"' AND zone_id::text like '"+str(division_id)+"' AND district_id::text like '"+str(district_id)+"' AND upazila_id::text like '"+str(upazilla_id)+"' AND union_id::text like '"+str(union_id)+"' AND organization_id::text like '"+str(org_id)+"' AND program_id::text like '"+str(program_id)+"' and id = any( select distinct farmer_id from farmer_crop_info where crop_id::text like '"+str(crop_id)+"' AND season_id::text like '"+str(season_id)+"' AND crop_variety_id::text like '"+str(variety_id)+"') returning id"
        df = pandas.read_sql(insert_query,connection)
        id = str(df.id.tolist()).replace('[','').replace(']','').replace(' ', '')
        # print(df.id)
        if country_id == '%':
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),'1' from promotional_sms where id::text = any(string_to_array('" + str(
                id) + "',','))"
            __db_commit_query(insert_query1)
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),'2' from promotional_sms where id::text = any(string_to_array('" + str(
                id) + "',','))"
            __db_commit_query(insert_query1)
        else:
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),country_id from promotional_sms where id::text = any(string_to_array('"+str(id)+"',','))"
            __db_commit_query(insert_query1)

        messages.success(request, '<i class="fa fa-check-circle"></i>New SMS has been added successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/promotional_sms_list/")

@login_required
def getProgram(request):
    org_id = request.POST.get('obj')
    query = "select id,program_name from usermodule_programs where org_id = " + str(org_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@login_required
def insert_management_sms_form(request):
    if request.POST:
        category_id = request.POST.get('category')
        sms_description = request.POST.get('sms_description')
        sms_description = sms_description.encode('utf-8').strip()
        org_id = request.POST.get('organization')
        program_id = request.POST.get('program')
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')
        stage_id = request.POST.get('crop_stage')
        user_id = request.user.id
        voice_sms_file_path = ""
        if "voice_sms" in request.FILES:
            myfile = request.FILES['voice_sms']
            url = "onadata/media/uploaded_files/"
            userName = request.user
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            voice_sms_file_path = "onadata/media/uploaded_files/" + myfile.name

        insert_query = "INSERT INTO public.management_sms_rule(stage_id,category_id, sms_description, voice_sms_file_path, org_id, program_id, crop_id, variety_id, season_id, created_at, created_by, updated_at, updated_by)VALUES("+str(stage_id)+"," + str(
            category_id) + ", '" + str(sms_description) + "', '" + str(voice_sms_file_path) + "', " + str(
            org_id) + ", " + str(program_id) + ", " + str(crop_id) + ", " + str(variety_id) + ", " + str(
            season_id) + ", now(), " + str(user_id) + ", now(), " + str(user_id) + ")"
        __db_commit_query(insert_query)
        messages.success(request, '<i class="fa fa-check-circle"></i>New SMS has been added successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/management_sms_rule_list/")


import shutil
# import pwd
# import grp

def weather_forecast(request):
    # os.system("sudo -S chmod -R 777 /home/ftpuserifc/20180826_00")
    start = datetime.now()
    query = "select * from weather_forecast"
    # directory = "20180916_00"
    # os.system("echo ''|sudo -S chmod -R 777 /home/ftpuserifc/20180916_00")
    directory = str(datetime.now().date()).replace('-', '') + '_00'
    print(directory)
    if not os.path.exists("onadata/media/weather_files/"):
        os.makedirs("onadata/media/weather_files/")
    if not os.path.exists("onadata/media/weather_files/" + str(directory)) and os.path.exists(
                    '/home/ftpuserifc/' + str(directory)):
        shutil.copytree('/home/ftpuserifc/' + str(directory), 'onadata/media/weather_files/' + str(directory))
        # list_of_files in that directory
        list_of_files = os.listdir('onadata/media/weather_files/' + str(directory))
        # print(list_of_files)
        for each in list_of_files:
            print('.txt' in each)
            if '.txt' in each:
                # read from directory
                # shutil.copyfile('onadata/media/test/Tar_02.txt', 'onadata/media/uploaded_files/Tar_02.txt')
                file = open('onadata/media/weather_files/' + str(directory) + '/' + str(each), 'r')
                insert_content = file.read()
                file.close()
                insert_content = insert_content.split('\n')
                for each in insert_content:
                    # print(re.split(r"\s+",each,maxsplit=6))
                    temp_data = each.split(None, 6)
                    place_name = ''
                    date_time = ''
                    temperature = ''
                    humidity = ''
                    wind_speed = ''
                    wind_direction = ''
                    rainfall = ''

                    if len(temp_data):
                        place_name = temp_data[0]
                        date_time = str(temp_data[1]).split(':')
                        temperature = temp_data[2]
                        humidity = temp_data[3]
                        wind_speed = temp_data[4]
                        wind_direction = temp_data[5]
                        rainfall = temp_data[6].strip()
                        if rainfall[0] == 'E':
                            rainfall = '-1'

                        # formatting the date_time
                        res_date = ''
                        res_date = date_time[0] + '-'
                        if int(date_time[1]) <= 9:
                            res_date += '0' + date_time[1] + '-'
                        else:
                            res_date += date_time[1] + '-'
                        if int(date_time[2]) <= 9:
                            res_date += '0' + date_time[2]
                        else:
                            res_date += date_time[2]
                        if int(date_time[3]) <= 9:
                            res_date += ' 0' + date_time[3] + ':00' + ':00'
                        else:
                            res_date += ' ' + date_time[3] + ':00' + ':00'

                        # check if data is exists or not
                        query = "select id from weather_forecast where place_name = '" + str(
                            place_name) + "' and date_time = '" + str(res_date) + "'"
                        df = pandas.DataFrame()
                        df = pandas.read_sql(query, connection)
                        if not df.empty:
                            # update query
                            id = df.id.tolist()[0]
                            update_query = "UPDATE public.weather_forecast SET temperature='" + str(
                                temperature) + "', humidity='" + str(humidity) + "', wind_speed='" + str(
                                wind_speed) + "', wind_direction='" + str(wind_direction) + "', rainfall='" + str(
                                rainfall) + "' where id = " + str(id)
                            __db_commit_query(update_query)
                        else:
                            # insert query
                            insert_query = "INSERT INTO public.weather_forecast (place_name, date_time, temperature, humidity, wind_speed, wind_direction, rainfall,data_type) VALUES('" + str(
                                place_name) + "', '" + str(res_date) + "', '" + str(temperature) + "', '" + str(
                                humidity) + "', '" + str(wind_speed) + "', '" + str(wind_direction) + "', '" + str(
                                rainfall) + "','2')"
                            __db_commit_query(insert_query)
    print(datetime.now() - start)
    # return render(request,'ifcmodule/index.html')
    return HttpResponse('')


def update_stage(request):
    query = "select id, sowing_date from farmer_crop_info"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    farmer_crop_id = []
    sowing_date = []
    if not df.empty:
        farmer_crop_id = df.id.tolist()
        sowing_date = df.sowing_date.tolist()
    for i in range(len(farmer_crop_id)):
        query = "select * from farmer_crop_stage where farmer_crop_id = " + str(farmer_crop_id[i])
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        if df.empty:
            insert_query = "INSERT INTO farmer_crop_stage(farmer_crop_id, stage) VALUES (" + str(farmer_crop_id[i]) + ", (SELECT(SELECT CASE when crop_variety_id :: INT = 0 and season_id :: INT != 0 then (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = "+str(farmer_crop_id[i])+" limit 1) when crop_variety_id :: INT != 0 and season_id :: INT = 0 then (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = "+str(farmer_crop_id[i])+" limit 1) WHEN crop_variety_id :: INT = 0 and season_id :: INT = 0 THEN (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = "+str(farmer_crop_id[i])+" limit 1) ELSE (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = "+str(farmer_crop_id[i])+") end FROM crop_stage WHERE crop_id = t.crop_id LIMIT 1) FROM farmer_crop_info t WHERE t.id = "+str(farmer_crop_id[i])+"))"
            __db_commit_query(insert_query)
        else:
            update_query = "update farmer_crop_stage set stage =(SELECT(SELECT CASE when crop_variety_id :: INT = 0 and season_id :: INT != 0 then (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = "+str(farmer_crop_id[i])+" limit 1) when crop_variety_id :: INT != 0 and season_id :: INT = 0 then (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = "+str(farmer_crop_id[i])+" limit 1) WHEN crop_variety_id :: INT = 0 and season_id :: INT = 0 THEN (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = "+str(farmer_crop_id[i])+" limit 1) ELSE (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = "+str(farmer_crop_id[i])+") end FROM crop_stage WHERE crop_id = t.crop_id LIMIT 1) FROM farmer_crop_info t WHERE t.id = "+str(farmer_crop_id[i])+") where farmer_crop_id =" + str(farmer_crop_id[i])
            __db_commit_query(update_query)
    # return render(request,'ifcmodule/index.html')
    return HttpResponse('')


@login_required
def getStage(request):
    season_id = request.POST.get('season_id')
    crop_id = request.POST.get('crop_id')
    var_id = request.POST.get('var_id')
    query = "select id,stage_name from crop_stage where season_id::int ="+str(season_id)+" and crop_variety_id::int = " + str(var_id)+" and crop_id = "+str(crop_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@login_required
def management_sms_rule_list(request):
    query = "select id,case when category_id = 1 then 'Management' when category_id = 2 then 'Promotional' end as category, sms_description, case when org_id = 0 then 'ALL' else(select organization from usermodule_organizations where id = org_id limit 1) end as organization, case when program_id = 0 then 'ALL' else (select program_name from usermodule_programs where id = program_id limit 1) end as program, case when crop_id = 0 then 'ALL' else (select crop_name from crop where id = crop_id limit 1) end as crop, case when season_id = 0 then 'ALL' else (select season_name from cropping_season where id = season_id limit 1) end as season, case when variety_id = 0 then 'ALL' else (select variety_name from crop_variety where id = variety_id limit 1) end as variety, case when variety_id = 0 then 'ALL' else (select stage_name from crop_stage where id = stage_id limit 1) end as stage from management_sms_rule order by id desc"
    management_sms_rule_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'ifcmodule/management_sms_rule.html', {
        'management_sms_rule_list': management_sms_rule_list
    })

@login_required
def edit_management_sms_form(request, sms_rule_id):
    query = "select * from management_sms_rule where id = " + str(sms_rule_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    set_category_id = df.category_id.tolist()[0]
    set_sms_description = df.sms_description.tolist()[0]
    voice_sms_file_path = df.voice_sms_file_path.tolist()[0]
    set_organization  = df.org_id.tolist()[0]
    set_program_id = df.program_id.tolist()[0]
    set_crop_id = df.crop_id.tolist()[0]
    set_variety_id = df.variety_id.tolist()[0]
    set_season_id = df.season_id.tolist()[0]
    set_stage_id = df.stage_id.tolist()[0]

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop = zip(crop_id, crop_name)

    query = "select id,organization from usermodule_organizations"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)


    query = "select id,variety_name from crop_variety where crop_id = "+str(set_crop_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    name = df.variety_name.tolist()
    variety = zip(id, name)

    query = "select id,stage_name from crop_stage where crop_id = " + str(set_crop_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    name = df.stage_name.tolist()
    stage = zip(id, name)

    query = "select id,program_name from usermodule_programs where org_id = " + str(set_organization)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    name = df.program_name.tolist()
    program = zip(id, name)

    return render(request, 'ifcmodule/edit_management_sms_form.html',
                  {
                     'season':season,
                      'crop':crop,
                      'organization':organization,
                      'set_category_id':set_category_id,
                      'set_sms_description':set_sms_description,
                      'set_organization':set_organization,
                      'set_program_id':set_program_id,
                      'set_crop_id':set_crop_id,
                      'set_variety_id':set_variety_id,
                      'set_season_id':set_season_id,
                      'set_stage_id':set_stage_id,
                      'variety':variety,
                      'stage':stage,
                      'program':program,
                      'sms_rule_id':sms_rule_id
                  })



@login_required
def update_management_sms_form(request):
    if request.POST:
        sms_rule_id = request.POST.get('sms_rule_id')
        category_id = request.POST.get('category')
        sms_description = request.POST.get('sms_description')
        org_id = request.POST.get('organization')
        program_id = request.POST.get('program')
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')
        stage_id = request.POST.get('crop_stage')
        user_id = request.user.id
        voice_sms_file_path = ""
        if "voice_sms" in request.FILES:
            myfile = request.FILES['voice_sms']
            url = "onadata/media/uploaded_files/"
            userName = request.user
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            voice_sms_file_path = "onadata/media/uploaded_files/" + myfile.name
        update_query = "UPDATE public.management_sms_rule SET category_id="+str(category_id)+", sms_description='"+str(sms_description)+"', voice_sms_file_path='"+str(voice_sms_file_path)+"', org_id="+str(org_id)+", program_id="+str(program_id)+", crop_id="+str(crop_id)+", variety_id="+str(variety_id)+", season_id="+str(season_id)+",updated_at=now(), updated_by="+str(user_id)+", stage_id="+str(stage_id)+" WHERE id=" + str(sms_rule_id)
        __db_commit_query(update_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> SMS Info has been updated successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/management_sms_rule_list/")


@login_required
def delete_management_sms_form(request, sms_rule_id):
    delete_query = "delete from management_sms_rule where id = " + str(sms_rule_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> SMS Info has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/management_sms_rule_list/")


@login_required
def weather_sms_rule_list(request):
    query = "SELECT id, CASE WHEN category_id = 3 THEN 'Weather' end AS category, sms_description,(SELECT organization FROM usermodule_organizations WHERE id = org_id LIMIT 1) organization, (SELECT program_name FROM usermodule_programs WHERE id = program_id LIMIT 1) as program, (SELECT crop_name FROM crop WHERE id = crop_id LIMIT 1) crop, (SELECT season_name FROM cropping_season WHERE id = season_id LIMIT 1) season, (SELECT variety_name FROM crop_variety WHERE id = variety_id LIMIT 1) variety, (SELECT stage_name FROM crop_stage WHERE id = stage_id LIMIT 1) stage FROM weather_sms_rule ORDER BY id DESC"
    weather_sms_rule_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'ifcmodule/weather_sms_rule.html', {
        'weather_sms_rule_list': weather_sms_rule_list
    })

@login_required
def weather_sms_form(request):
    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop = zip(crop_id, crop_name)

    query = "select id,organization from usermodule_organizations"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,parameter_name from weather_parameters"
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    id = df.id.tolist()
    parameter_name = df.parameter_name.tolist()
    parameter = zip(id, parameter_name)
    return render(request, 'ifcmodule/weather_sms_form.html',
                  {'organization': organization, 'season': season, 'crop': crop,'parameter':parameter})

@login_required
def insert_weather_sms_form(request):
    if request.POST:
        category_id = request.POST.get('category')
        sms_description = request.POST.get('sms_description')
        sms_description = sms_description.encode('utf-8').strip()
        org_id = request.POST.get('organization')
        program_id = request.POST.get('program')
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')
        stage_id = request.POST.get('crop_stage')
        user_id = request.user.id
        voice_sms_file_path = ""
        count = int(request.POST.get('count'))
        idx = 1
        if "voice_sms" in request.FILES:
            myfile = request.FILES['voice_sms']
            url = "onadata/media/uploaded_files/"
            userName = request.user
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            voice_sms_file_path = "onadata/media/uploaded_files/" + myfile.name

        insert_query = "INSERT INTO public.weather_sms_rule(stage_id,category_id, sms_description, voice_sms_file_path, org_id, program_id, crop_id, variety_id, season_id, created_at, created_by, updated_at, updated_by)VALUES("+str(stage_id)+"," + str(
            category_id) + ", '" + str(sms_description) + "', '" + str(voice_sms_file_path) + "', " + str(
            org_id) + ", " + str(program_id) + ", " + str(crop_id) + ", " + str(variety_id) + ", " + str(
            season_id) + ", now(), " + str(user_id) + ", now(), " + str(user_id) + ") returning id"
        # print(insert_query)
        weather_sms_rule_id = __db_fetch_single_value(insert_query)

        rules_relation = ""

        while  count >= idx:
            # print(idx,count)
            parameter_id = request.POST.get('parameter_id_'+str(idx))
            parameter_type_id = request.POST.get('parameter_type_'+str(idx))
            sub_parameter_id = request.POST.get('sub_parameter_id_'+str(idx))
            consecutive_days = request.POST.get('consecutive_days_'+str(idx))
            operators = request.POST.get('operators_'+str(idx))
            calculation_type = request.POST.get('calculation_type_'+str(idx))
            unit = request.POST.get('unit_'+str(idx))
            parameter_value = request.POST.get('parameter_value_'+str(idx))
            unit = unit.encode('utf-8').strip()
            # print(parameter_id,parameter_type_id,sub_parameter_id,consecutive_days,operators,calculation_type,unit,parameter_value)
            insert_query_rules  = "INSERT INTO public.weather_sms_rule_details (parameter_id, parameter_type_id, sub_parameter_id, consecutive_days, operators, calculation_type, unit,parameter_value)VALUES("+str(parameter_id)+", "+str(parameter_type_id)+", "+str(sub_parameter_id)+", "+str(consecutive_days)+", '"+str(operators)+"', '"+str(calculation_type)+"', '"+str(unit)+"','"+str(parameter_value)+"') returning id"
            # print(insert_query_rules)
            details_id = __db_fetch_single_value(insert_query_rules)
            if idx != 1:
                operation = request.POST.get('operation_'+str(idx))
                rules_relation += str(operation) + str(details_id)
            else:
                rules_relation += str(details_id)
            idx += 1

        # insert into weather_sms_rule_relation table

        insert_query_relation = "INSERT INTO public.weather_sms_rule_relation (weather_sms_rule_id, rules_relation) VALUES("+str(weather_sms_rule_id)+", '"+str(rules_relation)+"')"
        __db_commit_query(insert_query_relation)

        messages.success(request, '<i class="fa fa-check-circle"></i> New SMS Rule has been added successfully!',
                         extra_tags='alert-success crop-both-side')

    return HttpResponseRedirect("/ifcmodule/weather_sms_rule_list/")

@login_required
def getSubParameter(request):
    sub_parameter_id = request.POST.get('obj')
    query = "select id,sub_parameter_name from weather_sub_parameters where parameter_id ="+str(sub_parameter_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@login_required
def delete_weather_sms_form(request, sms_rule_id):
    delete_rules_details = "delete from weather_sms_rule_details where id in (select unnest(regexp_split_to_array(rules_relation, '[&||]'))::int from weather_sms_rule_relation where weather_sms_rule_id = "+str(sms_rule_id)+")"
    __db_commit_query(delete_rules_details)
    delete_query = "delete from weather_sms_rule where id = " + str(sms_rule_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> SMS Rule has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/weather_sms_rule_list/")


@login_required
def edit_weather_sms_form(request,sms_rule_id):
    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop = zip(crop_id, crop_name)

    query = "select id,organization from usermodule_organizations"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,parameter_name from weather_parameters"
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    id = df.id.tolist()
    parameter_name = df.parameter_name.tolist()
    parameter = zip(id, parameter_name)

    info_query = "with first_q as( SELECT weather_sms_rule.id,category_id, sms_description,org_id, program_id,crop_id,season_id,variety_id,stage_id,rules_relation FROM weather_sms_rule,weather_sms_rule_relation where weather_sms_rule.id = weather_sms_rule_relation.weather_sms_rule_id and weather_sms_rule.id = "+str(sms_rule_id)+"), q2 as ( select unnest(regexp_split_to_array(rules_relation, '[&||]')) details_id,* from first_q )select q2.*,weather_sms_rule_details.*,substring(rules_relation,position(weather_sms_rule_details.id::text in rules_relation)::int-1,1) operations from weather_sms_rule_details,q2 where weather_sms_rule_details.id = q2.details_id::int"
    data = json.dumps(__db_fetch_values_dict(info_query))

    return render(request, 'ifcmodule/edit_weather_sms_form.html',
                  {'sms_rule_id':sms_rule_id,'data':data,'organization': organization, 'season': season, 'crop': crop,'parameter':parameter})


@login_required
def update_weather_sms_form(request):
    if request.POST:
        sms_rule_id = request.POST.get('sms_rule_id')
        category_id = request.POST.get('category')
        sms_description = request.POST.get('sms_description')
        sms_description = sms_description.encode('utf-8').strip()
        org_id = request.POST.get('organization')
        program_id = request.POST.get('program')
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')
        stage_id = request.POST.get('crop_stage')
        user_id = request.user.id
        voice_sms_file_path = ""
        count = int(request.POST.get('count'))
        idx = 1
        if "voice_sms" in request.FILES:
            myfile = request.FILES['voice_sms']
            url = "onadata/media/uploaded_files/"
            userName = request.user
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            voice_sms_file_path = "onadata/media/uploaded_files/" + myfile.name

        update_query = "UPDATE public.weather_sms_rule SET category_id="+str(category_id)+", sms_description='"+str(sms_description)+"', voice_sms_file_path='"+str(voice_sms_file_path)+"', org_id="+str(org_id)+", program_id="+str(program_id)+", crop_id="+str(crop_id)+" , variety_id="+str(variety_id)+", season_id="+str(season_id)+", updated_at=now() , updated_by="+str(user_id)+", stage_id="+str(stage_id)+" WHERE id="+str(sms_rule_id)+""
        # print(update_query)
        __db_commit_query(update_query)


        rules_relation = ""

        while  count >= idx:
            print(idx,count)
            parameter_id = request.POST.get('parameter_id_'+str(idx))
            parameter_type_id = request.POST.get('parameter_type_'+str(idx))
            sub_parameter_id = request.POST.get('sub_parameter_id_'+str(idx))
            consecutive_days = request.POST.get('consecutive_days_'+str(idx))
            operators = request.POST.get('operators_'+str(idx))
            calculation_type = request.POST.get('calculation_type_'+str(idx))
            unit = request.POST.get('unit_'+str(idx))
            unit = unit.encode('utf-8').strip()
            details_id = request.POST.get('details_id_'+str(idx))
            parameter_value = request.POST.get('parameter_value_' + str(idx))
            # print(details_id,parameter_id,parameter_type_id,sub_parameter_id,consecutive_days,operators,calculation_type,unit)
            if not len(str(details_id)):
                insert_query_rules  = "INSERT INTO public.weather_sms_rule_details (parameter_id, parameter_type_id, sub_parameter_id, consecutive_days, operators, calculation_type, unit,parameter_value)VALUES("+str(parameter_id)+", "+str(parameter_type_id)+", "+str(sub_parameter_id)+", "+str(consecutive_days)+", '"+str(operators)+"', '"+str(calculation_type)+"', '"+str(unit)+"','"+str(parameter_value)+"') returning id"
                # print(insert_query_rules)
                details_id = __db_fetch_single_value(insert_query_rules)
            else:
                update_query_rules = "UPDATE public.weather_sms_rule_details SET parameter_value='"+str(parameter_value)+"',parameter_id="+str(parameter_id)+", parameter_type_id="+str(parameter_type_id)+", sub_parameter_id="+str(sub_parameter_id)+", consecutive_days="+str(consecutive_days)+", operators='"+str(operators)+"', calculation_type='"+str(calculation_type)+"' , unit='"+str(unit)+"' WHERE id="+str(details_id)+""
                __db_commit_query(update_query_rules)
            if idx != 1:
                operation = request.POST.get('operation_'+str(idx))
                rules_relation += str(operation) + str(details_id)
            else:
                rules_relation += str(details_id)
            idx += 1

        # update weather_sms_rule_relation table

        update_query_relation = "UPDATE public.weather_sms_rule_relation SET  rules_relation='"+str(rules_relation)+"' WHERE weather_sms_rule_id="+str(sms_rule_id)+""
        __db_commit_query(update_query_relation)

        messages.success(request, '<i class="fa fa-check-circle"></i> SMS  Rule has been updated successfully!',
                         extra_tags='alert-success crop-both-side')

    return HttpResponseRedirect("/ifcmodule/weather_sms_rule_list/")

def set_nan_to_blank(var):
    if str(var) == "nan":
        var = ""
    return var

def weather_observed(request):
    start = datetime.now()
    directory = str(datetime.now().date()).replace('-','')+'_99'
    if not os.path.exists("/home/ftpuserifc/weather_files/"):
        os.makedirs("/home/ftpuserifc/weather_files/")
    if not os.path.exists("/home/ftpuserifc/weather_files/"+str(directory)) and os.path.exists('/home/ftpuserifc/'+str(directory)):
        shutil.copytree('/home/ftpuserifc/'+str(directory),'/home/ftpuserifc/weather_files/'+str(directory))
        full_file_path = "/home/ftpuserifc/weather_files/"+str(directory)+"/weather_observed.csv"
        df = pandas.DataFrame()
        df = pandas.read_csv(full_file_path)
        cols = df.columns
        for each in df.index:
            station_id = set_nan_to_blank(df.loc[each][str(cols[0])])
            date_time = set_nan_to_blank(df.loc[each][str(cols[1])])
            wind_speed = set_nan_to_blank(df.loc[each][str(cols[2])])
            temperature = set_nan_to_blank(df.loc[each][str(cols[13])])
            humidity = set_nan_to_blank(df.loc[each][str(cols[14])])
            dew_point_temperature = set_nan_to_blank(df.loc[each][str(cols[15])])
            rainfall = set_nan_to_blank(df.loc[each][str(cols[16])])
            solar_radiation = set_nan_to_blank(df.loc[each][str(cols[17])])
            # check if data exists
            query = "select id from weather_observed where date_time = '" + str(date_time) + "'"
            df1 = pandas.DataFrame()
            df1 = pandas.read_sql(query, connection)
            if not df1.empty:
                # update query
                id = df1.id.tolist()[0]
                update_query = "UPDATE public.weather_observed SET station_id='"+str(station_id)+"', date_time='"+str(date_time)+"', wind_speed ='"+str(wind_speed)+"', temperature ='"+str(temperature)+"', dew_point_temperature ='"+str(dew_point_temperature)+"', humidity ='"+str(humidity)+"', solar_radiation ='"+str(solar_radiation)+"', rainfall ='"+str(rainfall)+"' where id = " + str(id)
                __db_commit_query(update_query)
            else:
                # insert query
                insert_query = "INSERT INTO public.weather_observed (station_id, date_time, wind_speed, temperature, dew_point_temperature, humidity, solar_radiation, rainfall) VALUES('"+str(station_id)+"', '"+str(date_time)+"', '"+str(wind_speed)+"', '"+str(temperature)+"','"+str(dew_point_temperature)+"', '"+str(humidity)+"', '"+str(solar_radiation)+"', '"+str(rainfall)+"')"
                __db_commit_query(insert_query)
    print(datetime.now())
    print(datetime.now()-start)
    print('\n\n\n\n\n')
    return render(request, 'ifcmodule/index.html')


def get_farmers_sms(request):
    start = datetime.now()
    query = "WITH first_q AS(SELECT weather_sms_rule.id, category_id, sms_description, org_id, program_id, crop_id, season_id, variety_id, stage_id, rules_relation FROM weather_sms_rule, weather_sms_rule_relation WHERE  weather_sms_rule.id = weather_sms_rule_relation.weather_sms_rule_id), q2 AS (SELECT Unnest(Regexp_split_to_array(rules_relation, '[&||]')) details_id, * FROM first_q), q3 AS (SELECT q2.id weather_sms_rule_id, q2.*, weather_sms_rule_details.*, Substring(rules_relation, Position( weather_sms_rule_details.id :: text IN rules_relation) :: INT - 1, 1) operations FROM weather_sms_rule_details, q2 WHERE weather_sms_rule_details.id = q2.details_id :: INT) SELECT *,(select sub_parameter_name from weather_sub_parameters where id = sub_parameter_id::int) FROM q3 order by weather_sms_rule_id,details_id"
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    if not df.empty:
        weather_sms_rule_id = df.weather_sms_rule_id.unique().tolist()
        # print(weather_sms_rule_id)
        for each in weather_sms_rule_id:
            # print(df.loc[df['weather_sms_rule_id'] == each]['weather_sms_rule_id'])

            temp_weather_sms_rule_id = df.loc[df.index[df['weather_sms_rule_id'] == each]]['weather_sms_rule_id'].tolist()
            # print(temp_weather_sms_rule_id)
            wea_sms_id = temp_weather_sms_rule_id[0]
            parameter_id = df.loc[df.index[df['weather_sms_rule_id'] == each]]['parameter_id'].tolist()
            parameter_type_id = df.loc[df.index[df['weather_sms_rule_id'] == each]]['parameter_type_id'].tolist()
            sub_parameter_name =  df.loc[df.index[df['weather_sms_rule_id'] == each]]['sub_parameter_name'].tolist()
            consecutive_days = df.loc[df.index[df['weather_sms_rule_id'] == each]]['consecutive_days'].tolist()
            operators = df.loc[df.index[df['weather_sms_rule_id'] == each]]['operators'].tolist()
            calculation_type = df.loc[df.index[df['weather_sms_rule_id'] == each]]['calculation_type'].tolist()
            parameter_value = df.loc[df.index[df['weather_sms_rule_id'] == each]]['parameter_value'].tolist()
            operations = df.loc[df.index[df['weather_sms_rule_id'] == each]]['operations'].tolist()
            # print(temp_weather_sms_rule_id,parameter_id,parameter_type_id,consecutive_days,operators,calculation_type,operations)
            result_str_condition = ""
            for i in range(0,len(temp_weather_sms_rule_id)):
                column_name = get_column_name(parameter_id[i],sub_parameter_name[i])
                agg_fun_sub_parameter = get_agg_function_sub_parameter(sub_parameter_name[i])
                if parameter_type_id[i] == 2:
                    str_condition = "with t as( select place_id, date_time::date," + str(agg_fun_sub_parameter) + "(" + str(
                        column_name) + "::numeric) daily_calc from weather_forecast where date_time::date between now()::date + interval '1 day' and now()::date + interval '" + str(
                        consecutive_days[i]) + " day' group by place_id,date_time::date)select distinct place_id from t group by place_id having " + str(
                        calculation_type[i]) + "(daily_calc) " + str(operators[i]) + " " + str(parameter_value[i]) + " "
                elif parameter_type_id[i] == 1:
                    str_condition = "with t as( select station_id, date_time::date," + str(agg_fun_sub_parameter) + "(" + str(
                        column_name) + "::numeric) daily_calc from weather_observed where date_time::date between now()::date - interval '1 day' and now()::date - interval '" + str(
                        consecutive_days[i]) + " day' group by station_id,date_time::date)select  (select distinct place_id from union_place_station_mapping where station_id = t.station_id::int)place_id from t group by station_id having " + str(
                        calculation_type[i]) + "(daily_calc) " + str(operators[i]) + " " + str(parameter_value[i]) + " "

                if i != 0:
                    if operations[i] == '&':
                        result_str_condition += ' INTERSECT '
                    else:
                        result_str_condition += ' UNION '
                    result_str_condition += '(' + str_condition + ')'
                else:
                    result_str_condition += str_condition

            # print(result_str_condition)

            query_t = "insert into weather_sms_rule_queue(weather_sms_rule_id,mobile_number,sms_description,crop_id,season_id,variety_id,stage_id,org_id,program_id,union_id) with dfg1 as( select * from farmer_crop_info,farmer_crop_stage where farmer_crop_info.id = farmer_crop_stage.farmer_crop_id),dfg as ( select * from dfg1,farmer where dfg1.farmer_id = farmer.id ) select weather_sms_rule.id weather_sms_rule_id,(select mobile_number from farmer where id = farmer_id limit 1)mobile_number,sms_description, weather_sms_rule.crop_id,weather_sms_rule.season_id,weather_sms_rule.variety_id,weather_sms_rule.stage_id,weather_sms_rule.org_id,weather_sms_rule.program_id,( SELECT union_id FROM farmer WHERE id = farmer_id limit 1) union_id from weather_sms_rule,dfg where weather_sms_rule.id = "+str(wea_sms_id)+" and weather_sms_rule.crop_id = dfg.crop_id and weather_sms_rule.season_id = dfg.season_id and weather_sms_rule.variety_id = dfg.crop_variety_id and weather_sms_rule.stage_id = dfg.stage::int and weather_sms_rule.org_id = dfg.organization_id and weather_sms_rule.program_id = dfg.program_id and farmer_id=any ( select distinct farmer_id from farmer_crop_info where union_id = any (select distinct union_id from union_place_station_mapping where place_id =any ("+str(result_str_condition)+"))) order by farmer_id"
            __db_commit_query(query_t)
            # query_u = "update weather_sms_rule set sms_status = 1 where id = "+str(wea_sms_id)
            # __db_commit_query(query_u)
            print(query_t)
    print(datetime.now())
    print(datetime.now() - start)
    print('\n\n\n\n\n')
    return render(request, 'ifcmodule/index.html')

def get_column_name(id,sub_param):
    if id == 1:
        if "Dew" in sub_param:
            return "dew_point_temperature"
        return "temperature"
    elif id == 2:
        return "rainfall"
    elif id == 3:
        return "humidity"
    elif id == 4:
        return "solar_radiation"
    elif id == 5:
        return "wind_speed"


def get_agg_function_sub_parameter(sub_param):
    sub_param = sub_param.lower()
    if "average" in sub_param or "dew" in sub_param:
        return "avg"
    elif "maximum" in sub_param:
        return "max"
    elif "minimum" in sub_param:
        return "min"
    elif "cumulative" in sub_param:
        return "sum"


@login_required
def sms_list(request):
    q = 'select distinct crop_id,crop_name from vwcrop_variety'
    crop_list = __db_fetch_values_dict(q)
    return render(request, "ifcmodule/sms_list.html",{'crop_list' : crop_list})


def get_sms_table(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    crop = request.POST.get('crop')
    if (from_date == '' or to_date == ''):
        date_query = " and date(schedule_time) >=  current_date"
    else:
        date_query = " and  date(schedule_time) between '" + from_date + "' and '" + to_date + "'"
    q = "select id::text,farmer_name,mobile_number,sms_text,status,(select crop_name from vwcrop_variety where crop_id =management_sms_que.crop_id limit 1) crop_name,(select crop_name from vwcrop_variety where variety_id =management_sms_que.variety_id limit 1 ) variety_name from management_sms_que where crop_id::text like '"+str(crop)+"' "+date_query+" order by id asc"
    dataset = __db_fetch_values_dict(q)
    #main_df = (pandas.read_sql(q, connection)).values.tolist()
    #print main_df
    return render(request, 'ifcmodule/sms_table.html',
                  {'dataset': dataset}, status=200)


def send_sms(request,id):
    q = "update management_sms_que set status = 'Sent',updated_at = NOW(),updated_by = "+str(request.user.id)+" where id = "+str(id)
    __db_commit_query(q)
    return HttpResponse(json.dumps('ok'), content_type="application/json", status=200)





def weather_sms_que_list(request):
    query = "SELECT DISTINCT weather_sms_rule_id AS sms_id, sms_description, union_id,(select name from vwunion where id = union_id::int limit 1)union_name, crop_id,(select crop_name from crop where id = crop_id::int limit 1)crop_name, season_id,(select season_name from cropping_season where id = season_id::int limit 1)season_name, variety_id,(select variety_name from crop_variety where id = variety_id::int limit 1)variety_name, stage_id, (select stage_name from crop_stage where id = stage_id::int limit 1)stage_name, to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS')  schedule_time FROM weather_sms_rule_queue WHERE status = 'New'"
    weather_sms_que_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id,crop_name)

    query = "select distinct geo_country_id,country_name from vwunion"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    country_id = df.geo_country_id.tolist()
    country_name = df.country_name.tolist()
    country = zip(country_id, country_name)

    return render(request, 'ifcmodule/weather_sms_que_list.html', {
        'weather_sms_que_list': weather_sms_que_list,'crop_list':crop_list,'country':country
    })


def management_sms_que_list(request):
    query = "SELECT DISTINCT sms_id, sms_text,(select union_id from farmer where id = farmer_id::int limit 1) union_id,(select (select name from vwunion where id = union_id::int limit 1) from farmer where id = farmer_id::int limit 1)union_name, crop_id,(select crop_name from crop where id = crop_id::int limit 1)crop_name, season_id,(select season_name from cropping_season where id = season_id::int limit 1)season_name, variety_id,(select variety_name from crop_variety where id = variety_id::int limit 1)variety_name, stage_id, (select stage_name from crop_stage where id = stage_id::int limit 1)stage_name, to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') schedule_time FROM management_sms_que WHERE status = 'New'"
    management_sms_que_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id,crop_name)

    query = "select distinct geo_country_id,country_name from vwunion"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    country_id = df.geo_country_id.tolist()
    country_name = df.country_name.tolist()
    country = zip(country_id, country_name)

    return render(request, 'ifcmodule/management_sms_que_list.html', {
        'management_sms_que_list': management_sms_que_list,'crop_list':crop_list,'country':country
    })


def approve_farmer_sms(request):
    weather_sms_rule_id = request.POST.get('weather_sms_rule_id')
    union_id  = request.POST.get('union_id')
    crop_id = request.POST.get('crop_id')
    season_id = request.POST.get('season_id')
    variety_id = request.POST.get('variety_id')
    stage_id = request.POST.get('stage_id')
    schedule_time = request.POST.get('schedule_time')
    username = request.user.username
    print(request.user.username,schedule_time)
    query = "INSERT INTO public.sms_que (mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id) SELECT mobile_number,sms_description,schedule_time,id,'weather_sms_rule_queue' as sms_source ,status ,'"+str(username)+"' as created_by,now() as created_at,(select country_id from farmer where mobile_number = weather_sms_rule_queue.mobile_number limit 1) FROM weather_sms_rule_queue WHERE status = 'New' and union_id = '"+str(union_id)+"' and weather_sms_rule_id = '"+str(weather_sms_rule_id)+"' and crop_id = '"+str(crop_id)+"' and season_id = '"+str(season_id)+"' and variety_id = '"+str(variety_id)+"' and stage_id = '"+str(stage_id)+"' and to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') = '"+str(schedule_time)+"'"
    print(query)
    __db_commit_query(query)
    query_t = "UPDATE public.weather_sms_rule_queue SET status='Sent'::text WHERE union_id = '"+str(union_id)+"' and weather_sms_rule_id = '"+str(weather_sms_rule_id)+"' and crop_id = '"+str(crop_id)+"' and season_id = '"+str(season_id)+"' and variety_id = '"+str(variety_id)+"' and stage_id = '"+str(stage_id)+"' and to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') = '"+str(schedule_time)+"'"
    __db_commit_query(query_t)
    return HttpResponse("")

def approve_farmer_sms_management(request):
    sms_id = request.POST.get('sms_id')
    union_id  = request.POST.get('union_id')
    crop_id = request.POST.get('crop_id')
    season_id = request.POST.get('season_id')
    variety_id = request.POST.get('variety_id')
    stage_id = request.POST.get('stage_id')
    schedule_time = request.POST.get('schedule_time')
    username = request.user.username
    print(request.user.username,schedule_time)
    query = "INSERT INTO public.sms_que (mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id)  with t as( select *,(select union_id from farmer where id = farmer_id::int limit 1) union_id from management_sms_que) SELECT mobile_number, sms_text, schedule_time, id, 'management_sms_que' AS sms_source, status, '"+str(username)+"' AS created_by, Now() AS created_at, (SELECT country_id FROM farmer WHERE mobile_number = t.mobile_number LIMIT 1) FROM t WHERE status = 'New' AND union_id = '"+str(union_id)+"' AND sms_id = '"+str(sms_id)+"' AND crop_id = '"+str(crop_id)+"' AND season_id = '"+str(season_id)+"' AND variety_id = '"+str(variety_id)+"' AND stage_id = '"+str(stage_id)+"' AND to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') = '"+str(schedule_time)+"'"
    print(query)
    __db_commit_query(query)
    query_t = "UPDATE public.management_sms_que SET status = 'Sent' :: text WHERE farmer_id = any(select id from farmer where union_id = '"+str(union_id)+"') AND sms_id = '"+str(sms_id)+"' AND crop_id = '"+str(crop_id)+"' AND season_id = '"+str(season_id)+"' AND variety_id = '"+str(variety_id)+"' AND stage_id = '"+str(stage_id)+"' AND to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') = '"+str(schedule_time)+"'"
    print(query_t)
    __db_commit_query(query_t)
    return HttpResponse("")

def reject_farmer_sms(request):
    weather_sms_rule_id = request.POST.get('weather_sms_rule_id')
    union_id = request.POST.get('union_id')
    crop_id = request.POST.get('crop_id')
    season_id = request.POST.get('season_id')
    variety_id = request.POST.get('variety_id')
    stage_id = request.POST.get('stage_id')
    schedule_time = request.POST.get('schedule_time')
    username = request.user.username
    print(request.user.username, schedule_time)
    query_t = "UPDATE public.weather_sms_rule_queue SET status='Reject'::text WHERE union_id = '" + str(
        union_id) + "' and weather_sms_rule_id = '" + str(weather_sms_rule_id) + "' and crop_id = '" + str(
        crop_id) + "' and season_id = '" + str(season_id) + "' and variety_id = '" + str(
        variety_id) + "' and stage_id = '" + str(
        stage_id) + "' and to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') = '" + str(schedule_time) + "'"
    print(query_t)
    __db_commit_query(query_t)
    return HttpResponse("")


def reject_farmer_sms_management(request):
    sms_id = request.POST.get('sms_id')
    union_id = request.POST.get('union_id')
    crop_id = request.POST.get('crop_id')
    season_id = request.POST.get('season_id')
    variety_id = request.POST.get('variety_id')
    stage_id = request.POST.get('stage_id')
    schedule_time = request.POST.get('schedule_time')
    username = request.user.username
    print(request.user.username, schedule_time)
    query_t = "UPDATE public.management_sms_que SET status='Reject'::text WHERE farmer_id = any(select id from farmer where union_id = '"+str(union_id)+"') and sms_id = '" + str(sms_id) + "' and crop_id = '" + str(crop_id) + "' and season_id = '" + str(season_id) + "' and variety_id = '" + str(variety_id) + "' and stage_id = '" + str(stage_id) + "' and to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') = '" + str(schedule_time) + "'"
    print(query_t)
    __db_commit_query(query_t)
    return HttpResponse("")

def getDivisions(request):
    obj = request.POST.get('obj')
    query = "select distinct geo_zone_id id,division_name field_name from vwunion where geo_country_id = '"+str(obj)+"'"
    data = json.dumps(__db_fetch_values_dict(query),default=decimal_date_default)
    return HttpResponse(data)


def getDistricts(request):
    obj = request.POST.get('obj')
    query = "select distinct geo_district_id id,district_name field_name from vwunion where geo_zone_id = '"+str(obj)+"'"
    data = json.dumps(__db_fetch_values_dict(query),default=decimal_date_default)
    return HttpResponse(data)

def getUpazillas(request):
    obj = request.POST.get('obj')
    query = "select distinct geo_upazilla_id id,upazilla_name field_name from vwunion where geo_district_id = '"+str(obj)+"'"
    data = json.dumps(__db_fetch_values_dict(query),default=decimal_date_default)
    return HttpResponse(data)

def getUnions(request):
    obj = request.POST.get('obj')
    query = "select distinct id,name field_name from vwunion where geo_upazilla_id = '"+str(obj)+"'"
    data = json.dumps(__db_fetch_values_dict(query),default=decimal_date_default)
    return HttpResponse(data)

def getWeatherQueueData(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    crop = request.POST.get('crop')
    country = request.POST.get('country')
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazilla = request.POST.get('upazilla')
    union = request.POST.get('union')
    query = "SELECT distinct weather_sms_rule_id AS sms_id, sms_description, union_id,(select name from vwunion where id = union_id::int limit 1)union_name, crop_id,(select crop_name from crop where id = crop_id::int limit 1)crop_name, season_id,(select season_name from cropping_season where id = season_id::int limit 1)season_name, variety_id,(select variety_name from crop_variety where id = variety_id::int limit 1)variety_name, stage_id, (select stage_name from crop_stage where id = stage_id::int limit 1)stage_name,to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') schedule_time FROM weather_sms_rule_queue,vwunion WHERE union_id::int = vwunion.id and status = 'New' and schedule_time between '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp and geo_country_id::text like '"+str(country)+"' and geo_zone_id::text like '"+str(division)+"' and geo_upazilla_id::text like '"+str(upazilla)+"' and geo_district_id::text like '"+str(district )+"' and union_id::text like '"+str(union)+"' and crop_id::text like '"+str(crop)+"'"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    print(data,query)
    return HttpResponse(data)

def getManagementQueueData(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    crop = request.POST.get('crop')
    country = request.POST.get('country')
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazilla = request.POST.get('upazilla')
    union = request.POST.get('union')
    query = "with t as( select (select union_id from farmer where id = farmer_id),* from management_sms_que) SELECT DISTINCT sms_id, sms_text, union_id, ( SELECT NAME FROM vwunion WHERE id = union_id::int limit 1)union_name, crop_id, ( SELECT crop_name FROM crop WHERE id = crop_id::int limit 1)crop_name, season_id, ( SELECT season_name FROM cropping_season WHERE id = season_id::int limit 1)season_name, variety_id, ( SELECT variety_name FROM crop_variety WHERE id = variety_id::int limit 1)variety_name, stage_id, ( SELECT stage_name FROM crop_stage WHERE id = stage_id::int limit 1) stage_name, to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') schedule_time FROM t, vwunion WHERE union_id::int = vwunion.id and status = 'New' and schedule_time between '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp and geo_country_id::text like '"+str(country)+"' and geo_zone_id::text like '"+str(division)+"' and geo_upazilla_id::text like '"+str(upazilla)+"' and geo_district_id::text like '"+str(district )+"' and union_id::text like '"+str(union)+"' and crop_id::text like '"+str(crop)+"'"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    print(data,query)
    return HttpResponse(data)