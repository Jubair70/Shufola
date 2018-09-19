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

    print(query)
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
def getProgram(request):
    org_id = request.POST.get('obj')
    query = "select id,program_name from usermodule_programs where org_id = " + str(org_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@login_required
def insert_management_sms_form(request):
    if request.POST:
        print(request.POST)
        category_id = request.POST.get('category')
        sms_description = request.POST.get('sms_description')
        org_id = request.POST.get('organization')
        program_id = request.POST.get('program')
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')
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

        insert_query = "INSERT INTO public.draft_sms(category_id, sms_description, voice_sms_file_path, org_id, program_id, crop_id, variety_id, season_id, created_at, created_by, updated_at, updated_by)VALUES(" + str(
            category_id) + ", '" + str(sms_description) + "', '" + str(voice_sms_file_path) + "', " + str(
            org_id) + ", " + str(program_id) + ", " + str(crop_id) + ", " + str(variety_id) + ", " + str(
            season_id) + ", now(), " + str(user_id) + ", now(), " + str(user_id) + ")"
        __db_commit_query(insert_query)
        messages.success(request, '<i class="fa fa-check-circle"></i>New SMS has been added successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/management_sms_form/")


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
                                rainfall) + "','forecast')"
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
            insert_query = "INSERT INTO farmer_crop_stage(farmer_crop_id, stage) VALUES (" + str(farmer_crop_id[
                                                                                                     i]) + ", (SELECT (SELECT CASE WHEN crop_variety_id :: INT = 0 AND season_id :: INT = 0 THEN (SELECT stage_name FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + ") ELSE (SELECT stage_name FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + ") end FROM crop_stage WHERE crop_id = t.crop_id LIMIT 1) FROM farmer_crop_info t WHERE t.id = " + str(
                farmer_crop_id[i]) + "))"
            __db_commit_query(insert_query)
        else:
            update_query = "update farmer_crop_stage set stage =(SELECT (SELECT CASE WHEN crop_variety_id :: INT = 0 AND season_id :: INT = 0 THEN (SELECT stage_name FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND Now() :: DATE - t.sowing_date >= start_day AND Now() :: DATE - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + ") ELSE (SELECT stage_name FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: DATE - t.sowing_date >= start_day AND Now() :: DATE - t.sowing_date <= end_day AND t.id =" + str(
                farmer_crop_id[
                    i]) + ") END FROM crop_stage WHERE crop_id = t.crop_id limit 1) FROM farmer_crop_info t WHERE t.id = " + str(
                farmer_crop_id[i]) + ") where id =" + str(farmer_crop_id[i])
            __db_commit_query(update_query)
    # return render(request,'ifcmodule/index.html')
    return HttpResponse('')
