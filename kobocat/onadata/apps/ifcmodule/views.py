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
import AdvancedHTMLParser
import json
import logging
import sys
import operator
import pandas
from django.shortcuts import render
import numpy as np
import time
import datetime
from django.core.files.storage import FileSystemStorage
from dateutil.relativedelta import relativedelta

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
import os
import datetime
import xlsxwriter

def multipleValuedQuryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchall()
    cursor.close()
    return value

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


def __db_run_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    nid = cursor.fetchone()[0]
    cursor.close()
    return nid


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

def __db_fetch_single_value_excption(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchone()
    cursor.close()
    print '---------fetchval--------'
    print fetchVal
    if fetchVal is None:
        return 0
    else:
        if fetchVal[0] is None:
            return 0
        else:
            return fetchVal[0]


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


def getOrgId(request):
    user_id = request.user.id
    org_id = __db_fetch_single_value("select organisation_name_id from usermodule_usermoduleprofile where user_id = " + str(user_id))
    return org_id


def getOrgList(request):
    org_list = []
    if request.user.is_superuser:
        org_list_result = __db_fetch_values_dict("select id from usermodule_organizations")
        for data in org_list_result:
            org_list.append(data['id'])
    else:
        org_list.append(getOrgId(request))
    return org_list


@login_required
def program_list(request):
    org_list = getOrgList(request)
    query = "select id,program_name,(select organization from usermodule_organizations where id = org_id limit 1) org_name  from usermodule_programs where org_id = any('{"+str(org_list).strip('[]')+" }')"
    program_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'ifcmodule/program_list.html', {
        'program_list': program_list
    })


@login_required
def add_program_form(request):
    org_list = getOrgList(request)
    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
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
    query = "select id,(select crop_name from crop where id = crop_id limit 1)," \
            "(select season_name from cropping_season where id = season_id limit 1)," \
            "(select variety_name from crop_variety where id = crop_variety_id)," \
            "sowing_date,land_size || ' '|| (select unit_name from land_units where id = unit_id limit 1) land_size , (select name from geo_district where id = district_id )district_name, " \
            "(select name from geo_upazilla where id = upazila_id )upazila_name , " \
            "(select name from geo_union where id = union_id )union_name " \
            "from farmer_crop_info where farmer_id = " + str(
        farmer_id)
    print(query)
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

def edit_crop_form(request,farmer_id,farmer_crop_id):
    info_query = "select farmer_id,crop_id,season_id,crop_variety_id,sowing_date::date,unit_id,land_size,zone_id,district_id,upazila_id,union_id from farmer_crop_info where id = "+str(farmer_crop_id)
    data = __db_fetch_values_dict(info_query)

    query = "select id, name , code from geo_zone"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    zone_id = df.id.tolist()
    zone_name = df.name.tolist()
    zone = zip(zone_id, zone_name)

    query = "select id,name from geo_district where geo_zone_id = "+str(data[0]['zone_id'])
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    district_id = df.id.tolist()
    district_name = df.name.tolist()
    district = zip(district_id, district_name)

    query = "select id,name from geo_upazilla where geo_district_id = " + str(data[0]['district_id'])
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    upz_id = df.id.tolist()
    upz_name = df.name.tolist()
    upazilla = zip(upz_id, upz_name)

    query = "select id,name from geo_union where geo_upazilla_id = " + str(data[0]['upazila_id'])
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    uni_id = df.id.tolist()
    uni_name = df.name.tolist()
    union = zip(uni_id, uni_name)

    query = "select id,variety_name from crop_variety where crop_id =" + str(data[0]['crop_id'])
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    var_id = df.id.tolist()
    var_name = df.variety_name.tolist()
    variety = zip(var_id, var_name)

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

    data = json.dumps(data, default=decimal_date_default)
    return render(request,'ifcmodule/edit_crop_form.html',{'farmer_crop_id':farmer_crop_id,'data':data,'farmer_id':farmer_id,'district':district,'upazilla':upazilla,'union':union,'variety':variety, 'zone': zone, 'season': season, 'crop': crop, 'unit': unit})


@login_required
def update_crop_form(request):
    if request.POST:
        farmer_id = request.POST.get('farmer_id')
        farmer_crop_id = request.POST.get('farmer_crop_id')
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
        update_query = "UPDATE public.farmer_crop_info SET crop_id="+str(crop)+", season_id="+str(season)+", crop_variety_id="+str(crop_variety)+", sowing_date='"+str(sowing_date)+"', unit_id="+str(unit)+", land_size='"+str(land_size)+"', updated_at=now(), updated_by="+str(user_id)+", zone_id="+str(zone_id)+", district_id="+str(district_id)+", upazila_id="+str(upazila_id)+", union_id="+str(union_id)+" WHERE id="+str(farmer_crop_id)+""
        print(update_query)
        __db_commit_query(update_query)
        messages.success(request,
                         '<i class="fa fa-check-circle"></i>Crop Info has been updated successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/farmer_profile_view/" + str(farmer_id) + "/")

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
def change_multiple_farmer_status(request):
    farmer_id = []
    status = request.POST.get('status')
    farmer_id_list = request.POST.getlist('farmer_ids')
    for row in farmer_id_list:
        farmer_id.append(int(row))
    query = "update farmer set status = " + str(status) + ", updated_at = now() where id = any('{"+str(farmer_id).strip('[]')+" }')"
    __db_commit_query(query)
    return HttpResponse("")



@login_required
def management_sms_form(request):
    org_list = getOrgList(request)
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

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,group_name from group_details where org_id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    grp_id = df.id.tolist()
    grp_name = df.group_name.tolist()
    grp = zip(grp_id, grp_name)
    return render(request, 'ifcmodule/management_sms_form.html',
                  {'organization': organization, 'season': season, 'crop': crop,'grp':grp})

@login_required
def management_sms_form_for_content(request,content_id):
    org_list = getOrgList(request)
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

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,group_name from group_details where org_id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    grp_id = df.id.tolist()
    grp_name = df.group_name.tolist()
    grp = zip(grp_id, grp_name)

    data = __db_fetch_values_dict("select * from content where id = "+str(content_id))
    season_id = data[0]['season']
    crop_id = data[0]['crop']
    crop_variety_id = data[0]['crop_variety']
    sms_type = data[0]['content_type']
    sms = data[0]['sms_description']
    org_id = data[0]['org_id']
    voice_sms_file_path = data[0]['voice_sms_file_path']

    return render(request, 'ifcmodule/management_sms_form_for_content.html',{
        'organization': organization,
        'season': season,
        'crop': crop,
        'grp':grp,
        'crop_id': int(crop_id),
        'season_id': int(season_id),
        'crop_variety_id': int(crop_variety_id),
        'sms_type': sms_type,
        'sms': sms,
        'org_id_': int(org_id),
        'voice_path':voice_sms_file_path
    })


@login_required
def promotional_sms_form(request):
    org_list = getOrgList(request)
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

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
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

    query = "select id,group_name from group_details where org_id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    grp_id = df.id.tolist()
    grp_name = df.group_name.tolist()
    grp = zip(grp_id, grp_name)

    return render(request, 'ifcmodule/promo_sms_form_work.html',{
            'organization': organization,
            'season': season,
            'crop': crop,
            'country': country,
            'grp':grp
        })


def getMapData(request):

    print '--------map data------------'
    org_list = getOrgList(request)
    processed_dist_dict = {}
    range_list = []
    store_range_list = []
    farmer_crop_list = []

    crop = '%'
    program = '%'
    crop_variety = '%'
    season = '%'
    division = '%'
    district = '%'
    upazilla = '%'
    union = '%'
    sub_query = ''

    if request.method == 'POST':
        crop = request.POST.get('crop')
        program = request.POST.get('program')
        crop_variety = request.POST.get('crop_variety')
        season = request.POST.get('season')
        division = request.POST.get('division')
        district = request.POST.get('district')
        upazilla = request.POST.get('upazilla')
        union = request.POST.get('union')

        print season

        if crop != '%':
            crop_result_list = __db_fetch_values_dict("select id from farmer where id in (select distinct farmer_id from farmer_crop_info where crop_id ="+str(crop)+") and organization_id = any('{"+str(org_list).strip('[]')+" }') ")

            for row in crop_result_list:
                farmer_crop_list.append(int(row['id']))

            sub_query = "and id = any('{" + str(farmer_crop_list).strip('[]') + " }')"

        if crop != '%' and crop_variety != '%':
            farmer_crop_list = []
            crop_result_list = __db_fetch_values_dict("select id from farmer where id in (select distinct farmer_id from farmer_crop_info where crop_id ="+str(crop)+" and crop_variety_id = "+str(crop_variety)+") and organization_id = any('{"+str(org_list).strip('[]')+" }') ")

            for row in crop_result_list:
                farmer_crop_list.append(int(row['id']))

            sub_query = "and id = any('{" + str(farmer_crop_list).strip('[]') + " }')"

        if crop != '%' and crop_variety != '%' and season != '%':
            farmer_crop_list = []
            crop_result_list = __db_fetch_values_dict("select id from farmer where id in (select distinct farmer_id from farmer_crop_info where crop_id ="+str(crop)+" and crop_variety_id = "+str(crop_variety)+" and season_id = "+str(season)+") and organization_id = any('{"+str(org_list).strip('[]')+" }') ")

            for row in crop_result_list:
                farmer_crop_list.append(int(row['id']))

            sub_query = "and id = any('{" + str(farmer_crop_list).strip('[]') + " }')"

    dist_list = __db_fetch_values_dict("select (select name from vwdistrict where id = district_id ) dist_name, count(district_id) as total_no_of_farmer from farmer where organization_id = any('{"+str(org_list).strip('[]')+" }') and zone_id::text like '"+str(division)+"' and district_id::text like '"+str(district)+"'  and union_id::text like '"+str(union)+"' and upazila_id::text like '"+str(upazilla)+"' and program_id::text like'"+str(program)+"'"+sub_query +"  group by district_id")

    print '----dist list----'
    print dist_list

    if not dist_list:
        processed_dist_dict.update({str("Dhaka"): 0})
        total_no_of_farmer = 0
    else:
        for dist in dist_list:
            processed_dist_dict.update({str(dist['dist_name']): int(dist['total_no_of_farmer'])})
            store_range_list.append(int(dist['total_no_of_farmer']))

        total_no_of_farmer = __db_fetch_single_value("select count(*) from farmer where organization_id = any('{" + str(org_list).strip('[]') + " }')" + sub_query)

    print '------processed_dist_dict---------'
    print processed_dist_dict

    print '------total farmer-------------'
    print total_no_of_farmer

    if total_no_of_farmer < 100:
        range_value = 1000
    else:
        range_value = max(store_range_list)

    p1 = (range_value * 10) / 100
    p2 = (range_value * 25) / 100
    p3 = (range_value * 50) / 100
    p4 = (range_value * 75) / 100

    range_list.append(0)
    range_list.append(int(p1))
    range_list.append(int(p1 + 1))
    range_list.append(int(p2))
    range_list.append(int(p2 + 1))
    range_list.append(int(p3))
    range_list.append(int(p3 + 1))
    range_list.append(int(p4))
    range_list.append(int(p4 + 1))
    range_list.append(int(range_value))

    processed_range_list = json.dumps(range_list)

    b = json.dumps(processed_dist_dict)

    return HttpResponse(json.dumps({
        'dist_dict': b,
        'processed_range_list': processed_range_list,
        'total_farmer_no': total_no_of_farmer,
        },
        default=decimal_date_default))


@login_required
def promotional_sms_form_for_content(request,content_id):
    org_list = getOrgList(request)
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

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
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

    query = "select id,group_name from group_details where org_id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    grp_id = df.id.tolist()
    grp_name = df.group_name.tolist()
    grp = zip(grp_id, grp_name)

    data = __db_fetch_values_dict("select * from content where id = "+str(content_id))
    season_id = data[0]['season']
    crop_id = data[0]['crop']
    crop_variety_id = data[0]['crop_variety']
    sms_type = data[0]['content_type']
    sms = data[0]['sms_description']
    org_id = data[0]['org_id']
    voice_sms_file_path = data[0]['voice_sms_file_path']

    return render(request, 'ifcmodule/promotional_sms_form_for_content.html',{
            'organization': organization,
            'season': season,
            'crop': crop,
            'country': country,
            'grp':grp,
            'crop_id': int(crop_id),
            'season_id': int(season_id),
            'crop_variety_id': int(crop_variety_id),
            'sms_type': sms_type,
            'sms': sms,
            'org_id_': int(org_id),
            'voice_path': voice_sms_file_path
    })


@login_required
def promotional_sms_list(request):
    org_list = getOrgList(request)
    # query = "select 'Promotional/Broadcast' category_name,coalesce((select organization from usermodule_organizations where id::text = organization_id limit 1),'All') organization_name, coalesce((select program_name from usermodule_programs where id::text = program_id limit 1),'All') program_name, coalesce((select crop_name from crop where id::text = crop_id limit 1),'All') crop_name, coalesce((select variety_name from crop_variety where id::text = variety_id limit 1),'All') variety_name, coalesce((select season_name from cropping_season where id::text = season_id limit 1),'All') season_name, coalesce((select name from geo_country where id::text = country_id limit 1),'All') country_name, coalesce((select name from geo_zone where id::text = division_id limit 1),'All') division_name, coalesce((select name from geo_district where id::text = district_id limit 1),'All') district_name, coalesce((select name from geo_upazilla where id::text = upazilla_id limit 1),'All') upazilla_name, coalesce((select name from geo_union where id::text = union_id limit 1),'All') union_name,sms_description,mobile_number,farmer_name,substring(voice_sms_file_path from 8)voice_sms_file_path,content_type from promotional_sms where organization_id::int = any('{"+str(org_list).strip('[]')+" }')"
    # promotional_sms_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'ifcmodule/promotional_sms_list.html', {
        'promotional_sms_list': promotional_sms_list
    })


@login_required
def promotional_schedule_sms_history(request):
    org_list = getOrgList(request)
    promo_schedule_history_list = __db_fetch_values_dict("with t2 as (with t1 as (select promotional_sms.schedule_time::timestamp::date::text as sending_date, promotional_sms.program_id,promotional_sms.country_id,promotional_sms.crop_id, promotional_sms.farmer_id::int , promotional_sms.content_type,promotional_sms.organization_id from promotional_sms, sms_que where sms_que.alertlog_id = promotional_sms.id and sms_que.sms_source = 'promotional_sms' and sms_que.status != 'Sent' and promotional_sms.schedule_type != 0) select t1.sending_date,t1.program_id, t1.crop_id,t1.farmer_id, t1.content_type,t1.organization_id, t1.country_id, farmer.zone_id, farmer.district_id , farmer.upazila_id ,farmer.union_id from farmer,t1 where t1.farmer_id = farmer.id) select t2.sending_date, count(distinct t2.program_id)as t_program,count(distinct t2.farmer_id) as t_farmer, count(distinct t2.organization_id) as t_org, count(distinct t2.country_id) as t_country,count(distinct t2.zone_id) as t_zone,count(distinct t2.district_id) as t_district,count(distinct t2.upazila_id) as t_upazila,count(distinct t2.union_id) as t_union , 'promotional' as sms_type from t2 group by sending_date")

    return render(request, 'ifcmodule/promotional_schedule_sms_history.html', {
        'promotional_schedule_sms_list':promo_schedule_history_list
    })


@login_required
def promotional_sms_history(request):
    promo_history_list = __db_fetch_values_dict("with t2 as (with t1 as (select promotional_sms.schedule_time::timestamp::date::text as sending_date, promotional_sms.program_id,promotional_sms.country_id,promotional_sms.crop_id, promotional_sms.farmer_id::int , promotional_sms.content_type,promotional_sms.organization_id from promotional_sms, sms_que where sms_que.alertlog_id = promotional_sms.id and sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent') select t1.sending_date,t1.program_id, t1.crop_id,t1.farmer_id, t1.content_type,t1.organization_id, t1.country_id, farmer.zone_id, farmer.district_id , farmer.upazila_id ,farmer.union_id from farmer,t1 where t1.farmer_id = farmer.id) select t2.sending_date, count(distinct t2.program_id)as t_program,count(distinct t2.farmer_id) as t_farmer, count(distinct t2.organization_id) as t_org, count(distinct t2.country_id) as t_country,count(distinct t2.zone_id) as t_zone,count(distinct t2.district_id) as t_district,count(distinct t2.upazila_id) as t_upazila,count(distinct t2.union_id) as t_union , 'promotional' as sms_type from t2 group by sending_date")

    return render(request, 'ifcmodule/promotional_sms_history.html', {
        'promo_history_list':promo_history_list
    })


@login_required
def promotional_sms_history_map(request):
    processed_dist_dict = {}
    range_list = []
    store_range_list = []
    org_list = getOrgList(request)
    org_list_text = []
    for row in org_list:
        org_list_text.append(str(row))

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    _org = '%'
    _program = '%'
    _crop = '%'
    _sms_type = '%'

    _country = '%'
    _division = '%'
    _district = '%'
    _upazilla = '%'

    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    #start_date = '2017-01-01'
    sub_query = " and organization_id in ("+str(org_list_text).strip('[]')+")"

    if request.method == 'POST':
        _org = request.POST.get('organization')
        _program = request.POST.get('program')
        _crop = request.POST.get('crop')
        _sms_type = request.POST.get('sms_type')

        if request.POST.get('start_date') != '':
            if request.POST.get('start_date'):
                start_date = request.POST.get('start_date')
                print start_date

        if request.POST.get('end_date') != '':
            if request.POST.get('end_date'):
                end_date = request.POST.get('end_date')
                print end_date
        sub_query = " and organization_id LIKE '"+str(_org)+"' "
        _country = request.POST.get('country_id')
        _division = request.POST.get('division')
        _district = request.POST.get('district')
        _upazilla = request.POST.get('upazilla')

    dist_list = __db_fetch_values_dict("with t2 as(with t1 as (select promotional_sms.schedule_time::timestamp::date::text as sending_date, promotional_sms.program_id,promotional_sms.country_id,promotional_sms.crop_id, promotional_sms.farmer_id::int , promotional_sms.content_type,promotional_sms.organization_id from promotional_sms, sms_que where sms_que.alertlog_id = promotional_sms.id and sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and promotional_sms.content_type::text LIKE '" + str(_sms_type) + "' and promotional_sms.crop_id::text LIKE '" + str(_crop) + "' "+sub_query+" and program_id LIKE '"+str(_program)+"' and sms_que.schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date)+"' ) select t1.sending_date,t1.program_id, t1.crop_id,t1.farmer_id, t1.content_type,t1.organization_id, t1.country_id, farmer.zone_id, farmer.district_id , farmer.upazila_id ,farmer.union_id from farmer,t1 where t1.farmer_id = farmer.id) select (select name from vwdistrict,t2 where id = t2.district_id limit 1) as dist_name, count(t2.district_id) as total_no_of_sms from t2 where t2.district_id::text LIKE '"+str(_district)+"' and t2.zone_id::text LIKE '"+str(_division)+"' and t2.upazila_id::text LIKE '"+str(_upazilla)+"' and t2.country_id::text LIKE '"+str(_country)+"' group by t2.district_id")

    print '----dist list----'
    print dist_list

    if not dist_list:
        processed_dist_dict.update({str("Dhaka"): 0})
        total_no_of_sms = 0
    else:
        for dist in dist_list:
            processed_dist_dict.update({str(dist['dist_name']): int(dist['total_no_of_sms'])})
            store_range_list.append(int(dist['total_no_of_sms']))

        total_no_of_sms = __db_fetch_single_value("select count(*) from promotional_sms, sms_que where sms_que.alertlog_id = promotional_sms.id and sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and promotional_sms.crop_id::text LIKE '" + str(_crop) + "' "+sub_query+" and program_id LIKE '"+str(_program)+"' and sms_que.schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date)+"' ")

    print '------processed_dist_dict---------'
    print processed_dist_dict

    print '------total sms-------------'
    print total_no_of_sms

    if total_no_of_sms < 100:
        range_value = 1000
    else:
        range_value = max(store_range_list)

    p1 = (range_value * 10) / 100
    p2 = (range_value * 25) / 100
    p3 = (range_value * 50) / 100
    p4 = (range_value * 75) / 100

    range_list.append(0)
    range_list.append(int(p1))
    range_list.append(int(p1 + 1))
    range_list.append(int(p2))
    range_list.append(int(p2 + 1))
    range_list.append(int(p3))
    range_list.append(int(p3 + 1))
    range_list.append(int(p4))
    range_list.append(int(p4 + 1))
    range_list.append(int(range_value))

    processed_range_list = json.dumps(range_list)

    b = json.dumps(processed_dist_dict)

    if _org is None or _org == '%':
        org_for_template = 0
    else:
        org_for_template = int(_org)

    if _crop is None or _crop == '%':
        crop_for_template = 0
    else:
        crop_for_template = int(_crop)

    if _crop is None or _crop == '%':
        type_for_template = 0
    else:
        if _sms_type == 'text':
            type_for_template = 1
        else:
            type_for_template = 2

    return render(request, 'ifcmodule/promotional_sms_history_map.html', {
        'dist_dict': b,
        'processed_range_list': processed_range_list,
        'crop_list':crop_list,
        'total_no_of_sms':total_no_of_sms,
        'organization':organization,
        'start_date':start_date,
        'end_date':end_date,
        'org_for_template':org_for_template,
        'crop_for_template':crop_for_template,
        'country': _country,
        'division': _division,
        'district': _district,
        'upazilla': _upazilla,
        'type_for_template':type_for_template
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
        content_id = request.POST.get('content_id', '')
        group_id = request.POST.get('group')
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

        if group_id == '0':
            if crop_id == '%' and season_id == '%' and variety_id == '%':
                insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by,voice_sms_file_path,content_id,group_id) select '" + str(
                    org_id) + "', '" + str(program_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(
                    season_id) + "', '" + str(country_id) + "', '" + str(division_id) + "', '" + str(
                    district_id) + "', '" + str(upazilla_id) + "', '" + str(
                    union_id) + "', id farmer_id,farmer_name,mobile_number::text,'" + str(sms_description) + "','" + str(
                    username) + "','" + str(voice_sms_file_path) + "','" + str(
                    content_id) + "',"+str(group_id)+" from farmer where country_id::text LIKE '" + str(
                    country_id) + "' AND zone_id::text like '" + str(division_id) + "' AND district_id::text like '" + str(
                    district_id) + "' AND upazila_id::text like '" + str(upazilla_id) + "' AND union_id::text like '" + str(
                    union_id) + "' AND organization_id::text like '" + str(org_id) + "' AND program_id::text like '" + str(
                    program_id) + "'  returning id"
            else:
                insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by,voice_sms_file_path,content_id,group_id) select '" + str(
                    org_id) + "', '" + str(program_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(
                    season_id) + "', '" + str(country_id) + "', '" + str(division_id) + "', '" + str(
                    district_id) + "', '" + str(upazilla_id) + "', '" + str(
                    union_id) + "', id farmer_id,farmer_name,mobile_number::text,'" + str(sms_description) + "','" + str(
                    username) + "','" + str(voice_sms_file_path) + "','" + str(
                    content_id) + "',"+str(group_id)+" from farmer where country_id::text LIKE '" + str(
                    country_id) + "' AND zone_id::text like '" + str(division_id) + "' AND district_id::text like '" + str(
                    district_id) + "' AND upazila_id::text like '" + str(upazilla_id) + "' AND union_id::text like '" + str(
                    union_id) + "' AND organization_id::text like '" + str(org_id) + "' AND program_id::text like '" + str(
                    program_id) + "' and id = any( select distinct farmer_id from farmer_crop_info where crop_id::text like '" + str(
                    crop_id) + "' AND season_id::text like '" + str(season_id) + "' AND crop_variety_id::text like '" + str(
                    variety_id) + "') returning id"
        else:
            if crop_id == '%' and season_id == '%' and variety_id == '%':
                insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by,voice_sms_file_path,content_id,group_id) select '" + str(
                    org_id) + "', '" + str(program_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(
                    season_id) + "', '" + str(country_id) + "', '" + str(division_id) + "', '" + str(
                    district_id) + "', '" + str(upazilla_id) + "', '" + str(
                    union_id) + "', id farmer_id,farmer_name,mobile_number::text,'" + str(sms_description) + "','" + str(
                    username) + "','" + str(voice_sms_file_path) + "','" + str(
                    content_id) + "',"+str(group_id)+" from farmer where country_id::text LIKE '" + str(
                    country_id) + "' AND zone_id::text like '" + str(division_id) + "' AND district_id::text like '" + str(
                    district_id) + "' AND upazila_id::text like '" + str(upazilla_id) + "' AND union_id::text like '" + str(
                    union_id) + "' AND organization_id::text like '" + str(org_id) + "' AND program_id::text like '" + str(
                    program_id) + "' and id = any(select farmer_id from farmer_group where group_id = "+str(group_id)+")  returning id"
            else:
                insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by,voice_sms_file_path,content_id,group_id) select '" + str(
                    org_id) + "', '" + str(program_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(
                    season_id) + "', '" + str(country_id) + "', '" + str(division_id) + "', '" + str(
                    district_id) + "', '" + str(upazilla_id) + "', '" + str(
                    union_id) + "', id farmer_id,farmer_name,mobile_number::text,'" + str(sms_description) + "','" + str(
                    username) + "','" + str(voice_sms_file_path) + "','" + str(
                    content_id) + "',"+str(group_id)+" from farmer where country_id::text LIKE '" + str(
                    country_id) + "' AND zone_id::text like '" + str(division_id) + "' AND district_id::text like '" + str(
                    district_id) + "' AND upazila_id::text like '" + str(upazilla_id) + "' AND union_id::text like '" + str(
                    union_id) + "' AND organization_id::text like '" + str(org_id) + "' AND program_id::text like '" + str(
                    program_id) + "' and id = any( select distinct farmer_id from farmer_crop_info where crop_id::text like '" + str(
                    crop_id) + "' AND season_id::text like '" + str(season_id) + "' AND crop_variety_id::text like '" + str(
                    variety_id) + "' and farmer_id = any(select farmer_id from farmer_group where group_id = "+str(group_id)+"))  returning id"

        df = pandas.read_sql(insert_query, connection)
        id = str(df.id.tolist()).replace('[', '').replace(']', '').replace(' ', '')
        if country_id == '%':
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id,content_type,content_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),'1',content_type,content_id from promotional_sms where id::text = any(string_to_array('" + str(
                id) + "',','))"
            __db_commit_query(insert_query1)
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id,content_type,content_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),'2',content_type,content_id from promotional_sms where id::text = any(string_to_array('" + str(
                id) + "',','))"
            __db_commit_query(insert_query1)
        else:
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id,content_type,content_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),country_id,content_type,content_id from promotional_sms where id::text = any(string_to_array('" + str(
                id) + "',','))"
            __db_commit_query(insert_query1)

        messages.success(request, '<i class="fa fa-check-circle"></i>New SMS has been added successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/promotional_sms_list/")


@login_required
def insert_promotional_sms_form_with_schedule(request):
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
        content_id = request.POST.get('content_id', '')
        group_id = request.POST.get('group')
        schedule_date_value = request.POST.get('schedule_date_value')
        repeat_value = request.POST.get('repeat_value')
        repeat_cycle = request.POST.get('repeat_cycle')
        username = request.user.username
        voice_sms_file_path = ""

        print sms_description
        print repeat_value
        print schedule_date_value
        print repeat_cycle

        if "voice_sms" in request.FILES:
            myfile = request.FILES['voice_sms']
            url = "onadata/media/uploaded_files/"
            userName = request.user
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            voice_sms_file_path = "onadata/media/uploaded_files/" + myfile.name

        if group_id == '0':
            if crop_id == '%' and season_id == '%' and variety_id == '%':
                insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by,voice_sms_file_path,content_id,group_id,schedule_time,schedule_type,repeat_cycle) select '" + str(
                    org_id) + "', '" + str(program_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(
                    season_id) + "', '" + str(country_id) + "', '" + str(division_id) + "', '" + str(
                    district_id) + "', '" + str(upazilla_id) + "', '" + str(
                    union_id) + "', id farmer_id,farmer_name,mobile_number::text,'" + str(sms_description) + "','" + str(
                    username) + "','" + str(voice_sms_file_path) + "','" + str(
                    content_id) + "',"+str(group_id)+ ", '" + str(schedule_date_value)+"', "+str(repeat_value)+", "+str(repeat_cycle)+" from farmer where country_id::text LIKE '" + str(
                    country_id) + "' AND zone_id::text like '" + str(division_id) + "' AND district_id::text like '" + str(
                    district_id) + "' AND upazila_id::text like '" + str(upazilla_id) + "' AND union_id::text like '" + str(
                    union_id) + "' AND organization_id::text like '" + str(org_id) + "' AND program_id::text like '" + str(
                    program_id) + "'  returning id"
            else:
                insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by,voice_sms_file_path,content_id,group_id,schedule_time,schedule_type,repeat_cycle) select '" + str(
                    org_id) + "', '" + str(program_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(
                    season_id) + "', '" + str(country_id) + "', '" + str(division_id) + "', '" + str(
                    district_id) + "', '" + str(upazilla_id) + "', '" + str(
                    union_id) + "', id farmer_id,farmer_name,mobile_number::text,'" + str(sms_description) + "','" + str(
                    username) + "','" + str(voice_sms_file_path) + "','" + str(
                    content_id) + "',"+str(group_id)+ ", '" + str(schedule_date_value)+"', "+str(repeat_value)+", "+str(repeat_cycle)+" from farmer where country_id::text LIKE '" + str(
                    country_id) + "' AND zone_id::text like '" + str(division_id) + "' AND district_id::text like '" + str(
                    district_id) + "' AND upazila_id::text like '" + str(upazilla_id) + "' AND union_id::text like '" + str(
                    union_id) + "' AND organization_id::text like '" + str(org_id) + "' AND program_id::text like '" + str(
                    program_id) + "' and id = any( select distinct farmer_id from farmer_crop_info where crop_id::text like '" + str(
                    crop_id) + "' AND season_id::text like '" + str(season_id) + "' AND crop_variety_id::text like '" + str(
                    variety_id) + "') returning id"
        else:
            if crop_id == '%' and season_id == '%' and variety_id == '%':
                insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by,voice_sms_file_path,content_id,group_id,schedule_time,schedule_type,repeat_cycle) select '" + str(
                    org_id) + "', '" + str(program_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(
                    season_id) + "', '" + str(country_id) + "', '" + str(division_id) + "', '" + str(
                    district_id) + "', '" + str(upazilla_id) + "', '" + str(
                    union_id) + "', id farmer_id,farmer_name,mobile_number::text,'" + str(sms_description) + "','" + str(
                    username) + "','" + str(voice_sms_file_path) + "','" + str(
                    content_id) + "',"+str(group_id)+", '" + str(schedule_date_value)+"', "+str(repeat_value)+", "+str(repeat_cycle)+" from farmer where country_id::text LIKE '" + str(
                    country_id) + "' AND zone_id::text like '" + str(division_id) + "' AND district_id::text like '" + str(
                    district_id) + "' AND upazila_id::text like '" + str(upazilla_id) + "' AND union_id::text like '" + str(
                    union_id) + "' AND organization_id::text like '" + str(org_id) + "' AND program_id::text like '" + str(
                    program_id) + "' and id = any(select farmer_id from farmer_group where group_id = "+str(group_id)+")  returning id"
            else:
                insert_query = "INSERT INTO public.promotional_sms(organization_id, program_id, crop_id, variety_id, season_id, country_id, division_id, district_id, upazilla_id, union_id, farmer_id, farmer_name, mobile_number, sms_description, created_by,voice_sms_file_path,content_id,group_id,schedule_time,schedule_type,repeat_cycle) select '" + str(
                    org_id) + "', '" + str(program_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(
                    season_id) + "', '" + str(country_id) + "', '" + str(division_id) + "', '" + str(
                    district_id) + "', '" + str(upazilla_id) + "', '" + str(
                    union_id) + "', id farmer_id,farmer_name,mobile_number::text,'" + str(sms_description) + "','" + str(
                    username) + "','" + str(voice_sms_file_path) + "','" + str(
                    content_id) + "',"+str(group_id)+", '" + str(schedule_date_value)+"', "+str(repeat_value)+", "+str(repeat_cycle)+" from farmer where country_id::text LIKE '" + str(
                    country_id) + "' AND zone_id::text like '" + str(division_id) + "' AND district_id::text like '" + str(
                    district_id) + "' AND upazila_id::text like '" + str(upazilla_id) + "' AND union_id::text like '" + str(
                    union_id) + "' AND organization_id::text like '" + str(org_id) + "' AND program_id::text like '" + str(
                    program_id) + "' and id = any( select distinct farmer_id from farmer_crop_info where crop_id::text like '" + str(
                    crop_id) + "' AND season_id::text like '" + str(season_id) + "' AND crop_variety_id::text like '" + str(
                    variety_id) + "' and farmer_id = any(select farmer_id from farmer_group where group_id = "+str(group_id)+"))  returning id"

        df = pandas.read_sql(insert_query, connection)
        id = str(df.id.tolist()).replace('[', '').replace(']', '').replace(' ', '')
        if country_id == '%':
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id,content_type,content_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),'1',content_type,content_id from promotional_sms where id::text = any(string_to_array('" + str(
                id) + "',','))"
            __db_commit_query(insert_query1)
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id,content_type,content_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),'2',content_type,content_id from promotional_sms where id::text = any(string_to_array('" + str(
                id) + "',','))"
            __db_commit_query(insert_query1)
        else:
            insert_query1 = "INSERT INTO public.sms_que(mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id,content_type,content_id) select mobile_number,sms_description,schedule_time,id,'promotional_sms','New','ifc',now(),country_id,content_type,content_id from promotional_sms where id::text = any(string_to_array('" + str(
                id) + "',','))"
            __db_commit_query(insert_query1)
    print '---------ok-----------'
    return HttpResponse("ok")

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
        sms_type = request.POST.get('sms_type')
        content_id = request.POST.get('content_id', '')
        group_id = request.POST.get('group')
        offset_days = request.POST.get('offset_days')
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

        insert_query = "INSERT INTO public.management_sms_rule(stage_id,category_id, sms_description, voice_sms_file_path, org_id, program_id, crop_id, variety_id, season_id, created_at, created_by, updated_at, updated_by,sms_type,content_id,group_id,offset_days)VALUES(" + str(
            stage_id) + "," + str(
            category_id) + ", '" + str(sms_description) + "', '" + str(voice_sms_file_path) + "', " + str(
            org_id) + ", " + str(program_id) + ", " + str(crop_id) + ", " + str(variety_id) + ", " + str(
            season_id) + ", now(), " + str(user_id) + ", now(), " + str(user_id) + ",'" + str(sms_type) + "','" + str(
            content_id) + "',"+str(group_id)+","+str(offset_days)+")"
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
def get_load_offset_max(request):
    stage_id = request.POST.get('stage_id')
    query = "select end_day-start_day diff from crop_stage where id = "+str(stage_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@login_required
def management_sms_rule_list(request):
    _org = '%'
    _crop = '%'
    _variety_crop = '%'
    _season = '%'
    _stage = '%'
    _content = '%'
    _program = '%'

    if request.method == 'POST':
        _org = request.POST.get('org_id')
        _crop = request.POST.get('crop')
        _variety_crop = request.POST.get('crop_variety')
        _season = request.POST.get('season')
        _stage = request.POST.get('crop_stage')
        _content = request.POST.get('content_type')
        _program = request.POST.get('program')

    org_list = getOrgList(request)
    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    org_list_data = __db_fetch_values_dict("select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')")
    print org_list_data

    org_list = getOrgList(request)
    query = "select id,case when category_id = 1 then 'Management' when category_id = 2 then 'Promotional' end as category, sms_description, case when org_id = 0 then 'ALL' else(select organization from usermodule_organizations where id = org_id limit 1) end as organization, case when program_id = 0 then 'ALL' else (select program_name from usermodule_programs where id = program_id limit 1) end as program, case when crop_id = 0 then 'ALL' else (select crop_name from crop where id = crop_id limit 1) end as crop, case when season_id = 0 then 'ALL' else (select season_name from cropping_season where id = season_id limit 1) end as season, case when variety_id = 0 then 'ALL' else (select variety_name from crop_variety where id = variety_id limit 1) end as variety, case when variety_id = 0 then 'ALL' else (select stage_name from crop_stage where id = stage_id limit 1) end as stage,COALESCE(sms_type,'') sms_type,substring(voice_sms_file_path from 8)voice_sms_file_path,content_type from management_sms_rule where org_id = any('{"+str(org_list).strip('[]')+" }') and program_id::text like '"+str(_program)+"' and crop_id::text like '"+str(_crop)+"' and variety_id::text like '"+str(_variety_crop)+"' and season_id::text like '"+str(_season)+"' and stage_id::text like '"+str(_stage)+"' and content_type like '"+str(_content)+"' order by id desc"
    management_sms_rule_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    if _org is None or _org == '%':
        org_for_template = 0
    else:
        org_for_template = int(_org)

    if _program is None or _program == '%':
        program_for_template = 0
    else:
        program_for_template = int(_program)

    if _crop is None or _crop == '%':
        crop_for_template = 0
    else:
        crop_for_template = int(_crop)

    if _season is None or _season == '%':
        season_for_template = 0
    else:
        season_for_template = int(_season)

    if _variety_crop is None or _variety_crop == '%':
        variety_crop_for_template = 0
    else:
        variety_crop_for_template = int(_variety_crop)

    if _stage is None or _stage == '%':
        stage_for_template = 0
    else:
        stage_for_template = int(_stage)

    content_for_template = 0
    if _content != '%':
        if _content == 'text':
            content_for_template = 1
        else:
            content_for_template = 2

    return render(request, 'ifcmodule/management_sms_rule.html', {
        'management_sms_rule_list': management_sms_rule_list,
        'season': season,
        'crop_list': crop_list,
        'org_list': org_list_data,
        'org_for_template': org_for_template,
        'program_for_template': program_for_template,
        'crop_for_template': crop_for_template,
        'season_for_template': season_for_template,
        'variety_crop_for_template': variety_crop_for_template,
        'content_for_template': content_for_template,
        'stage_for_template': stage_for_template
    })

@login_required
def edit_management_sms_form(request, sms_rule_id):
    org_list = getOrgList(request)
    query = "select category_id,sms_description,voice_sms_file_path,org_id,crop_id,variety_id,stage_id,season_id,program_id,COALESCE(sms_type,'')sms_type,COALESCE(content_id,'') content_id,group_id,offset_days from management_sms_rule where id = " + str(
        sms_rule_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    set_category_id = df.category_id.tolist()[0]
    set_sms_description = df.sms_description.tolist()[0]
    voice_sms_file_path = df.voice_sms_file_path.tolist()[0]
    set_organization = df.org_id.tolist()[0]
    set_program_id = df.program_id.tolist()[0]
    set_crop_id = df.crop_id.tolist()[0]
    set_variety_id = df.variety_id.tolist()[0]
    set_season_id = df.season_id.tolist()[0]
    set_stage_id = df.stage_id.tolist()[0]
    set_sms_type = df.sms_type.tolist()[0]
    set_content_id = df.content_id.tolist()[0]
    set_group_id = df.group_id.tolist()[0]
    set_offset_days = df.offset_days.tolist()[0]

    query = "select end_day-start_day diffs from crop_stage where id = "+str(set_stage_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    max_days = df.diffs.tolist()[0]

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

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,variety_name from crop_variety where crop_id = " + str(set_crop_id)
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

    query = "select id,group_name from group_details"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    grp_id = df.id.tolist()
    grp_name = df.group_name.tolist()
    grp = zip(grp_id, grp_name)

    return render(request, 'ifcmodule/edit_management_sms_form.html',
                  {
                      'season': season,
                      'crop': crop,
                      'organization': organization,
                      'set_category_id': set_category_id,
                      'set_sms_description': set_sms_description,
                      'set_organization': set_organization,
                      'set_program_id': set_program_id,
                      'set_crop_id': set_crop_id,
                      'set_variety_id': set_variety_id,
                      'set_season_id': set_season_id,
                      'set_stage_id': set_stage_id,
                      'set_sms_type': set_sms_type,
                      'variety': variety,
                      'stage': stage,
                      'program': program,
                      'sms_rule_id': sms_rule_id,
                      'set_content_id': set_content_id,
                      'set_group_id':set_group_id,
                      'grp':grp,
                      'set_offset_days': set_offset_days,
                      'max_days':max_days
                  })



@login_required
def update_management_sms_form(request):
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
        sms_type = request.POST.get('sms_type')
        content_id = request.POST.get('content_id', '')
        group_id = request.POST.get('group')
        offset_days = request.POST.get('offset_days')
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

            # deletePreviousAudio
            query = "select voice_sms_file_path from management_sms_rule where id = "+str(sms_rule_id)
            df = pandas.read_sql(query,connection)
            path = df.voice_sms_file_path.tolist()[0]
            if os.path.exists(path):
                os.remove(path)

        update_query = "UPDATE public.management_sms_rule SET content_id='" + str(content_id) + "' ,sms_type='" + str(
            sms_type) + "', category_id=" + str(category_id) + ", sms_description='" + str(
            sms_description) + "', voice_sms_file_path='" + str(voice_sms_file_path) + "', org_id=" + str(
            org_id) + ", program_id=" + str(program_id) + ", crop_id=" + str(crop_id) + ", variety_id=" + str(
            variety_id) + ", season_id=" + str(season_id) + ",updated_at=now(), updated_by=" + str(
            user_id) + ", stage_id=" + str(stage_id) + ",group_id = "+str(group_id)+",offset_days = "+str(offset_days)+" WHERE id=" + str(sms_rule_id)
        __db_commit_query(update_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> SMS Info has been updated successfully!',
                         extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/management_sms_rule_list/")


@login_required
def delete_management_sms_form(request, sms_rule_id):
    query = "select voice_sms_file_path from management_sms_rule where id = " + str(sms_rule_id)
    df = pandas.read_sql(query, connection)
    path = df.voice_sms_file_path.tolist()[0]
    if os.path.exists(path):
        os.remove(path)
    delete_query = "delete from management_sms_rule where id = " + str(sms_rule_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> SMS Info has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/management_sms_rule_list/")


@login_required
def weather_sms_rule_list(request):
    _org = '%'
    _crop = '%'
    _variety_crop = '%'
    _season = '%'
    _stage = '%'
    _content = '%'
    _program = '%'

    if request.method == 'POST':
        _org = request.POST.get('org_id')
        _crop = request.POST.get('crop')
        _variety_crop = request.POST.get('crop_variety')
        _season = request.POST.get('season')
        _stage = request.POST.get('crop_stage')
        _content = request.POST.get('content_type')
        _program = request.POST.get('program')

    org_list = getOrgList(request)
    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    org_list_data = __db_fetch_values_dict("select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')")
    print org_list_data

    query = "SELECT id, CASE WHEN category_id = 3 THEN 'Weather' end AS category, sms_description,(SELECT organization FROM usermodule_organizations WHERE id = org_id LIMIT 1) organization, (SELECT program_name FROM usermodule_programs WHERE id = program_id LIMIT 1) as program, (SELECT crop_name FROM crop WHERE id = crop_id LIMIT 1) crop, (SELECT season_name FROM cropping_season WHERE id = season_id LIMIT 1) season, (SELECT variety_name FROM crop_variety WHERE id = variety_id LIMIT 1) variety, (SELECT stage_name FROM crop_stage WHERE id = stage_id LIMIT 1) stage,COALESCE(sms_type,'') sms_type,substring(voice_sms_file_path from 8)voice_sms_file_path,content_type FROM weather_sms_rule where org_id = any('{"+str(org_list).strip('[]')+" }') and program_id::text like '"+str(_program)+"' and crop_id::text like '"+str(_crop)+"' and variety_id::text like '"+str(_variety_crop)+"' and season_id::text like '"+str(_season)+"' and stage_id::text like '"+str(_stage)+"' and content_type like '"+str(_content)+"' ORDER BY id DESC"
    weather_sms_rule_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    if _org is None or _org == '%':
        org_for_template = 0
    else:
        org_for_template = int(_org)

    if _program is None or _program == '%':
        program_for_template = 0
    else:
        program_for_template = int(_program)

    if _crop is None or _crop == '%':
        crop_for_template = 0
    else:
        crop_for_template = int(_crop)

    if _season is None or _season == '%':
        season_for_template = 0
    else:
        season_for_template = int(_season)

    if _variety_crop is None or _variety_crop == '%':
        variety_crop_for_template = 0
    else:
        variety_crop_for_template = int(_variety_crop)

    if _stage is None or _stage == '%':
        stage_for_template = 0
    else:
        stage_for_template = int(_stage)

    content_for_template = 0
    if _content != '%':
        if _content == 'text':
            content_for_template = 1
        else:
            content_for_template = 2

    return render(request, 'ifcmodule/weather_sms_rule.html', {
        'weather_sms_rule_list': weather_sms_rule_list,
        'season': season,
        'crop_list': crop_list,
        'org_list':org_list_data,
        'org_for_template': org_for_template,
        'program_for_template': program_for_template,
        'crop_for_template': crop_for_template,
        'season_for_template': season_for_template,
        'variety_crop_for_template': variety_crop_for_template,
        'content_for_template': content_for_template,
        'stage_for_template':stage_for_template
    })

@login_required
def weather_sms_form(request):
    org_list = getOrgList(request)
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

    query = "select id,organization from usermodule_organizations where id = any('{"+str(org_list).strip('[]')+" }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,parameter_name from weather_parameters"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    parameter_name = df.parameter_name.tolist()
    parameter = zip(id, parameter_name)

    query = "select id,group_name from group_details where org_id = any('{"+str(org_list).strip('[]')+" }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    grp_id = df.id.tolist()
    grp_name = df.group_name.tolist()
    grp = zip(grp_id, grp_name)
    return render(request, 'ifcmodule/weather_sms_form.html',
                  {'organization': organization, 'season': season, 'crop': crop, 'parameter': parameter,'grp':grp})

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
        sms_type = request.POST.get('sms_type')
        content_id = request.POST.get('content_id', '')
        group_id = request.POST.get('group')
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

        insert_query = "INSERT INTO public.weather_sms_rule(stage_id,category_id, sms_description, voice_sms_file_path, org_id, program_id, crop_id, variety_id, season_id, created_at, created_by, updated_at, updated_by,sms_type,content_id,group_id)VALUES(" + str(
            stage_id) + "," + str(
            category_id) + ", '" + str(sms_description) + "', '" + str(voice_sms_file_path) + "', " + str(
            org_id) + ", " + str(program_id) + ", " + str(crop_id) + ", " + str(variety_id) + ", " + str(
            season_id) + ", now(), " + str(user_id) + ", now(), " + str(user_id) + ",'" + str(sms_type) + "','" + str(
            content_id) + "'," + str(group_id) + ") returning id"
        # print(insert_query)
        weather_sms_rule_id = __db_fetch_single_value(insert_query)

        rules_relation = ""

        while count >= idx:
            # print(idx,count)
            parameter_id = request.POST.get('parameter_id_' + str(idx))
            parameter_type_id = request.POST.get('parameter_type_' + str(idx))
            sub_parameter_id = request.POST.get('sub_parameter_id_' + str(idx))
            consecutive_days = request.POST.get('consecutive_days_' + str(idx))
            operators = request.POST.get('operators_' + str(idx))
            calculation_type = request.POST.get('calculation_type_' + str(idx))
            unit = request.POST.get('unit_' + str(idx))
            parameter_value = request.POST.get('parameter_value_' + str(idx))
            unit = unit.encode('utf-8').strip()
            # print(parameter_id,parameter_type_id,sub_parameter_id,consecutive_days,operators,calculation_type,unit,parameter_value)
            insert_query_rules = "INSERT INTO public.weather_sms_rule_details (parameter_id, parameter_type_id, sub_parameter_id, consecutive_days, operators, calculation_type, unit,parameter_value)VALUES(" + str(
                parameter_id) + ", " + str(parameter_type_id) + ", " + str(sub_parameter_id) + ", " + str(
                consecutive_days) + ", '" + str(operators) + "', '" + str(calculation_type) + "', '" + str(
                unit) + "','" + str(parameter_value) + "') returning id"
            # print(insert_query_rules)
            details_id = __db_fetch_single_value(insert_query_rules)
            if idx != 1:
                operation = request.POST.get('operation_' + str(idx))
                rules_relation += str(operation) + str(details_id)
            else:
                rules_relation += str(details_id)
            idx += 1

        # insert into weather_sms_rule_relation table

        insert_query_relation = "INSERT INTO public.weather_sms_rule_relation (weather_sms_rule_id, rules_relation) VALUES(" + str(
            weather_sms_rule_id) + ", '" + str(rules_relation) + "')"
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

@csrf_exempt
def weather_farmer_xls_list(request):
    org_list = getOrgList(request)
    row_id = request.POST.get('export_data')
    row_id = row_id.split('_')
    weather_sms_rule_id = row_id[0]
    union_id = row_id[1]
    crop_id = row_id[2]
    season_id = row_id[3]
    variety_id = row_id[4]
    stage_id = row_id[5]
    schedule_time = row_id[6]
    query = "with t as( select distinct  farmer_id::int,farmer_name,mobile_number FROM weather_sms_rule_queue WHERE status = 'New' and org_id::int = any('{"+str(org_list).strip('[]')+" }') and union_id = '" + str(
        union_id) + "' and weather_sms_rule_id = '" + str(weather_sms_rule_id) + "' and crop_id = '" + str(
        crop_id) + "' and season_id = '" + str(season_id) + "' and variety_id = '" + str(
        variety_id) + "' and stage_id = '" + str(stage_id) + "' and schedule_time::date = '" + str(
        schedule_time) + "'::date),t1 as ( select farmer_id,sowing_date from farmer_crop_info where crop_id = '" + str(
        crop_id) + "' and season_id = '" + str(season_id) + "' and crop_variety_id = '" + str(
        variety_id) + "' ), t2 as (select t.farmer_id,farmer_name,mobile_number,sowing_date from t,t1 where t.farmer_id = t1.farmer_id)select t2.farmer_id,farmer_name,mobile_number,sowing_date,group_id,coalesce((select group_name from group_details where id = group_id limit 1),'') group_name from t2 left join farmer_group on t2.farmer_id = farmer_group.farmer_id"

    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    writer = pandas.ExcelWriter("onadata/media/uploaded_files/output.xlsx")
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    f = open('onadata/media/uploaded_files/output.xlsx', 'r')
    response = HttpResponse(f, mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=weather_farmer_info.xls'
    return response

@csrf_exempt
def management_farmer_xls_list(request):
    org_list = getOrgList(request)
    row_id = request.POST.get('export_data')
    row_id = row_id.split('_')
    sms_id = row_id[0]
    union_id = row_id[1]
    crop_id = row_id[2]
    season_id = row_id[3]
    variety_id = row_id[4]
    stage_id = row_id[5]
    schedule_time = row_id[6]
    query = "with t as( with g as( SELECT *,( SELECT union_id FROM farmer WHERE id = farmer_id::INT limit 1) union_id FROM management_sms_que) select farmer_id,farmer_name,mobile_number FROM g where status = 'New' and organization_id = any('{"+str(org_list).strip('[]')+" }') and union_id = " + str(
        union_id) + " and sms_id = " + str(sms_id) + " and crop_id = " + str(crop_id) + " and season_id =" + str(
        season_id) + " and variety_id = " + str(variety_id) + " and stage_id = " + str(
        stage_id) + " and schedule_time::date = '" + str(
        schedule_time) + "'::date ),t1 as ( select farmer_id,sowing_date from farmer_crop_info where crop_id = " + str(
        crop_id) + " and season_id = " + str(season_id) + " and crop_variety_id = " + str(
        variety_id) + " ), t2 as (select t.farmer_id,farmer_name,mobile_number,sowing_date from t,t1 where t.farmer_id = t1.farmer_id)select distinct t2.farmer_id,farmer_name,mobile_number,sowing_date,group_id,coalesce((select group_name from group_details where id = group_id limit 1),'') group_name from t2 left join farmer_group on t2.farmer_id = farmer_group.farmer_id"
    print(query)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    writer = pandas.ExcelWriter("onadata/media/uploaded_files/output.xlsx")
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    f = open('onadata/media/uploaded_files/output.xlsx', 'r')
    response = HttpResponse(f, mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=management_farmer_info.xls'
    return response


@login_required
def sms_log_old(request):
    sms_log = ''
    return render(request, 'ifcmodule/sms_log.html', {
        'sms_log': sms_log
    })


@login_required
def sms_log(request):
    sms_log = ''
    return render(request, 'ifcmodule/sms_log_new.html', {
        'sms_log': sms_log
    })

@csrf_exempt
def getSMSLogData(request):
    org_list = getOrgList(request)
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    status = request.POST.get('status')
    sms_source = request.POST.get('sms_source')
    query = "WITH t AS( SELECT case when sms_source = 'management_sms_que' then (select (select sms_type from management_sms_rule where id = sms_id limit 1) from management_sms_que where id = alertlog_id limit 1) when sms_source = 'weather_sms_rule_queue' then (select (select sms_type from weather_sms_rule where id = weather_sms_rule_id limit 1) from weather_sms_rule_queue where id = alertlog_id limit 1) when sms_source = 'promotional_sms' then '' end sms_type, mobile_number, sms_text, voice_sms_file_path, schedule_time, sent_time, content_type,tx_id response FROM sms_que WHERE status like '"+str(status)+"' AND schedule_time BETWEEN '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp and sms_source like '"+str(sms_source)+"' ORDER BY schedule_time::date desc), t1 AS ( SELECT t.mobile_number, farmer_name, sms_text, sms_type, to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') schedule_time, COALESCE( to_char(sent_time, 'YYYY-MM-DD HH24:MI:SS'),'') sent_time, district_id, upazila_id, union_id,organization_id, content_type,substring(voice_sms_file_path FROM 8) voice_sms_file_path,response FROM t, farmer WHERE t.mobile_number = farmer.mobile_number and farmer.organization_id = any('{"+str(org_list).strip('[]')+" }')) SELECT mobile_number, farmer_name, sms_text, schedule_time, sms_type, sent_time, ( SELECT NAME FROM geo_district WHERE id = district_id limit 1)district_name, ( SELECT NAME FROM geo_upazilla WHERE id = upazila_id limit 1)upazilla_name, ( SELECT NAME FROM geo_union WHERE id = union_id limit 1)union_name, content_type,voice_sms_file_path,response,t1.organization_id FROM t1"

    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    print data
    return HttpResponse(data)


@csrf_exempt
def getSMSLogDataNew(request):
    draw = request.POST['draw']
    start = int(request.POST['start'])
    length = int(request.POST['length'])

    org_list = getOrgList(request)
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    status = request.POST.get('status')
    sms_source = request.POST.get('sms_source')

    data_query = "WITH t AS( SELECT case when sms_source = 'management_sms_que' then (select (select sms_type from management_sms_rule where id = sms_id limit 1) from management_sms_que where id = alertlog_id limit 1) when sms_source = 'weather_sms_rule_queue' then (select (select sms_type from weather_sms_rule where id = weather_sms_rule_id limit 1) from weather_sms_rule_queue where id = alertlog_id limit 1) when sms_source = 'promotional_sms' then '' end sms_type, mobile_number, sms_text, voice_sms_file_path, schedule_time, sent_time, content_type,tx_id response FROM sms_que WHERE status like '"+str(status)+"' AND schedule_time BETWEEN '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp and sms_source like '"+str(sms_source)+"' ORDER BY schedule_time::date desc), t1 AS ( SELECT t.mobile_number, farmer_name, sms_text, sms_type, to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') schedule_time, COALESCE( to_char(sent_time, 'YYYY-MM-DD HH24:MI:SS'),'') sent_time, district_id, upazila_id, union_id,organization_id, content_type,substring(voice_sms_file_path FROM 8) voice_sms_file_path,response FROM t, farmer WHERE t.mobile_number = farmer.mobile_number and farmer.organization_id = any('{"+str(org_list).strip('[]')+" }')) SELECT farmer_name ,mobile_number, case when content_type = 'audio' then '<audio preload=\"metadata\" controls><source src="'||voice_sms_file_path||'" type=\"audio/mp4;\" codecs=\"mp4a.40.2\"/> <source src="'||voice_sms_file_path||'" type=\"audio/mpeg;\" codecs=\"vorbis\"/> <source src=\"'||voice_sms_file_path||'\" type=\"audio/ogg;\" codecs=\"vorbis\"/></audio>' else sms_text end, sms_type , schedule_time, sent_time, ( SELECT NAME FROM geo_district WHERE id = district_id limit 1)district_name, ( SELECT NAME FROM geo_upazilla WHERE id = upazila_id limit 1)upazilla_name, ( SELECT NAME FROM geo_union WHERE id = union_id limit 1)union_name, content_type,response,t1.organization_id FROM t1 limit "+str(length)+" offset "+str(start)

    data = multipleValuedQuryExecution(data_query)

    total_count = __db_fetch_single_value_excption("WITH t AS( SELECT case when sms_source = 'management_sms_que' then (select (select sms_type from management_sms_rule where id = sms_id limit 1) from management_sms_que where id = alertlog_id limit 1) when sms_source = 'weather_sms_rule_queue' then (select (select sms_type from weather_sms_rule where id = weather_sms_rule_id limit 1) from weather_sms_rule_queue where id = alertlog_id limit 1) when sms_source = 'promotional_sms' then '' end sms_type, mobile_number, sms_text, voice_sms_file_path, schedule_time, sent_time, content_type,tx_id response FROM sms_que WHERE status like '"+str(status)+"' AND schedule_time BETWEEN '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp and sms_source like '"+str(sms_source)+"' ORDER BY schedule_time::date desc), t1 AS ( SELECT t.mobile_number, farmer_name, sms_text, sms_type, to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') schedule_time, COALESCE( to_char(sent_time, 'YYYY-MM-DD HH24:MI:SS'),'') sent_time, district_id, upazila_id, union_id,organization_id, content_type,substring(voice_sms_file_path FROM 8) voice_sms_file_path,response FROM t, farmer WHERE t.mobile_number = farmer.mobile_number and farmer.organization_id = any('{"+str(org_list).strip('[]')+" }')) SELECT count(*) FROM t1")

    print '----total-----'
    print total_count

    return HttpResponse(json.dumps({
        "draw": draw,
        "recordsTotal": total_count,
        "recordsFiltered": total_count,
        "data": data,
        },
        default=decimal_date_default))


def export_sms_log(request):
    org_list = getOrgList(request)
    status = request.POST.get('status','%')
    sms_source = request.POST.get('sms_source','%')

    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = datetime.datetime.now().strftime("%Y-%m-%d")

    if request.method == 'POST':
        if request.POST.get('from_date') != '':
            if request.POST.get('from_date'):
                start_date = request.POST.get('from_date')
                print start_date

        if request.POST.get('to_date') != '':
            if request.POST.get('to_date'):
                end_date = request.POST.get('to_date')
                print end_date

    query = "WITH t AS( SELECT case when sms_source = 'management_sms_que' then (select (select sms_type from management_sms_rule where id = sms_id limit 1) from management_sms_que where id = alertlog_id limit 1) when sms_source = 'weather_sms_rule_queue' then (select (select sms_type from weather_sms_rule where id = weather_sms_rule_id limit 1) from weather_sms_rule_queue where id = alertlog_id limit 1) when sms_source = 'promotional_sms' then '' end sms_type, mobile_number, sms_text, voice_sms_file_path, schedule_time, sent_time, content_type,tx_id response FROM sms_que WHERE status like '"+str(status)+"' AND schedule_time BETWEEN '"+str(start_date)+" 00:00:00'::timestamp and '"+str(end_date)+" 23:59:59'::timestamp and sms_source like '"+str(sms_source)+"' ORDER BY schedule_time::date desc), t1 AS ( SELECT t.mobile_number, farmer_name, sms_text, sms_type, to_char(schedule_time, 'YYYY-MM-DD HH24:MI:SS') schedule_time, COALESCE( to_char(sent_time, 'YYYY-MM-DD HH24:MI:SS'),'') sent_time, district_id, upazila_id, union_id,organization_id, content_type,substring(voice_sms_file_path FROM 8) voice_sms_file_path,response FROM t, farmer WHERE t.mobile_number = farmer.mobile_number and farmer.organization_id = any('{"+str(org_list).strip('[]')+" }')) SELECT farmer_name ,mobile_number, case when content_type = 'audio' then '' else sms_text end, sms_type , schedule_time, sent_time, ( SELECT NAME FROM geo_district WHERE id = district_id limit 1)district_name, ( SELECT NAME FROM geo_upazilla WHERE id = upazila_id limit 1)upazilla_name, ( SELECT NAME FROM geo_union WHERE id = union_id limit 1)union_name, content_type,response,t1.organization_id FROM t1"
    df = pandas.read_sql(query, connection)

    writer = pandas.ExcelWriter("onadata/media/uploaded_files/output.xlsx", engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    f = open('onadata/media/uploaded_files/output.xlsx', 'r')
    response = HttpResponse(f, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=SMS Log.xlsx'
    return response


@login_required
def weather_forecast_list(request):
    list = ''
    query = "select distinct place_name from weather_forecast"
    df = pandas.read_sql(query,connection)
    place_name = df.place_name.tolist()
    return render(request,'ifcmodule/weather_forecast_list.html',{'list':list,'place_name':place_name})


@csrf_exempt
def getWeatherForecastList(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    place_name = request.POST.get('place_name')
    query = "select place_name,TO_CHAR(date_time::timestamp,'YYYY-MM-DD HH24:MM:SS') as date_time,coalesce(temperature,'') temperature, coalesce(humidity,'') humidity, coalesce(wind_speed,'') wind_speed, coalesce(wind_direction,'') wind_direction, coalesce(rainfall,'') rainfall from weather_forecast  where place_name like '"+str(place_name)+"' AND date_time::timestamp BETWEEN '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp order by date_time::timestamp"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)



def getDailyWeatherForecastList(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    place_name = request.POST.get('place_name')

    query = "with t1 as (select place_name,TO_CHAR(date_time::timestamp,'YYYY-MM-DD HH24:MM:SS') as date_time,coalesce(temperature,'0') temperature, coalesce(humidity,'0') humidity, coalesce(wind_speed,'0') wind_speed, coalesce(wind_direction,'0') wind_direction, coalesce(rainfall,'0') rainfall from weather_forecast  where place_name like '" + str(place_name) + "' AND date_time::timestamp BETWEEN '" + str(from_date) + " 00:00:00'::timestamp and '" + str(to_date) + " 23:59:59'::timestamp order by date_time::timestamp) select place_name, date_time,min(cast(temperature as double precision)) temp_min, max(cast(temperature as double precision)) temp_max, avg(cast(temperature as double precision)) temp_avg, min(cast(humidity as double precision)) humidity_min, max(cast(humidity as double precision)) humidity_max, avg(cast(humidity as double precision)) humidity_avg, sum(cast(rainfall as double precision)) sum_rainfall,max(cast(wind_speed as double precision)) max_wind_speed, max(cast(wind_direction as double precision)) max_wind_direction  from t1 group by date_time,place_name"

    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@csrf_exempt
def getWeatherForecastGraphData(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    place_name = request.POST.get('place_name')
    temp_dict = __db_fetch_values_dict("with t1 as (select place_name,TO_CHAR(date_time::timestamp,'YYYY-MM-DD') as date_time,coalesce(temperature,'0') temperature, coalesce(humidity,'0') humidity, coalesce(wind_speed,'0') wind_speed, coalesce(wind_direction,'0') wind_direction, coalesce(rainfall,'0') rainfall from weather_forecast  where place_name like '" + str(place_name) + "' AND date_time::timestamp BETWEEN '" + str(from_date) + " 00:00:00'::timestamp and '" + str(to_date) + " 23:59:59'::timestamp order by date_time::timestamp) select place_name, date_time,min(cast(temperature as double precision)) temp_min, max(cast(temperature as double precision)) temp_max, avg(cast(temperature as double precision)) temp_avg, min(cast(humidity as double precision)) humidity_min, max(cast(humidity as double precision)) humidity_max, avg(cast(humidity as double precision)) humidity_avg, sum(cast(rainfall as double precision)) sum_rainfall,max(cast(wind_speed as double precision)) max_wind_speed, max(cast(wind_direction as double precision)) max_wind_direction  from t1 group by date_time,place_name")

    print temp_dict

    categories = []
    series_list_temp = []
    series_list_hum = []
    series_list_rainfall = []

    temp_min_list = []
    temp_max_list = []
    temp_avg_list = []

    hum_min_list = []
    hum_max_list = []
    hum_avg_list = []

    rainfall_list = []

    for row in temp_dict:
        categories.append(str(row['date_time']))
        temp_min_list.append(float(row['temp_min']))
        temp_max_list.append(float(row['temp_max']))
        temp_avg_list.append(float(row['temp_avg']))

        hum_min_list.append(float(row['humidity_min']))
        hum_max_list.append(float(row['humidity_max']))
        hum_avg_list.append(float(row['humidity_avg']))

        rainfall_list.append(float(row['sum_rainfall']))

    series_list_temp.append({'name': 'Min', 'data': temp_min_list})
    series_list_temp.append({'name': 'Max', 'data': temp_max_list})
    series_list_temp.append({'name': 'Avg', 'data': temp_avg_list})

    series_list_hum.append({'name': 'Min', 'data': hum_min_list})
    series_list_hum.append({'name': 'Max', 'data': hum_max_list})
    series_list_hum.append({'name': 'Avg', 'data': hum_avg_list})

    series_list_rainfall.append({'name': 'Daily Rainfall', 'data': rainfall_list})

    print categories
    print series_list_temp

    #data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    return HttpResponse(json.dumps({
        'category_list':categories,
        'series_list_temp':series_list_temp,
        'series_list_hum':series_list_hum,
        'series_list_rainfall':series_list_rainfall

    }))

@login_required
def weather_observed_list(request):
    list = ''
    return render(request,'ifcmodule/weather_observed_list.html',{'list':list})


@csrf_exempt
def getWeatherObservedList(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    station_id = request.POST.get('station_name')
    print '--------processing----------'
    query = "select case when station_id = '1' then 'Khulna' when station_id = '2' then 'Biratnagar' when station_id = '3' then 'Barisal' end station_name,substring(date_time from 1 for  20) as date_time,coalesce(temperature,'') temperature,coalesce(dew_point_temperature,'') dew_point_temperature,coalesce(humidity,'') humidity,coalesce(solar_radiation,'') solar_radiation, coalesce(wind_speed,'') wind_speed, coalesce(wind_direction,'') wind_direction, coalesce(soil_moisture,'') soil_moisture, coalesce(rainfall,'') rainfall, coalesce(qfe,'') qfe,coalesce(qff,'') qff from weather_observed  where station_id like '"+str(station_id)+"' AND date_time::timestamp BETWEEN '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp order by date_time::timestamp"
    print '------process done---------'
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)



@csrf_exempt
def getDailyWeatherObservedList(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    station_id = request.POST.get('station_name')
    print '-----processing---------'

    query = "with t1 as (select case when station_id = '1' then 'Khulna' when station_id = '2' then 'Biratnagar' when station_id = '3' then 'Barisal' end station_name,substring(date_time from 1 for  20) as date_time, date_time::timestamp::date as date_info,coalesce(temperature,'') temperature,coalesce(dew_point_temperature,'') dew_point_temperature, coalesce(humidity,'') humidity,coalesce(solar_radiation,'') solar_radiation, coalesce(wind_speed,'') wind_speed, coalesce(wind_direction,'') wind_direction, coalesce(soil_moisture,'') soil_moisture, coalesce(rainfall,'') rainfall, coalesce(qfe,'') qfe,coalesce(qff,'') qff from weather_observed where station_id like '"+str(station_id)+"' AND date_time::timestamp BETWEEN '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp order by date_time::timestamp) select station_name, date_info,min(cast(temperature as double precision)) temp_min, max(cast(temperature as double precision)) temp_max, avg(cast(temperature as double precision)) temp_avg, min(cast(humidity as double precision)) humidity_min, max(cast(humidity as double precision)) humidity_max, avg(cast(humidity as double precision)) humidity_avg, sum(cast(solar_radiation as double precision)) sum_solar_radiation, SUM(NULLIF(rainfall, '')::numeric) sum_rainfall,max(cast(wind_speed as double precision)) max_wind_speed from t1 group by date_info,station_name"

    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@csrf_exempt
def getWeatherObservedGraphData(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    station_id = request.POST.get('station_name')
    temp_dict = __db_fetch_values_dict("with t1 as (select case when station_id::int = 1 then 'Khulna' when station_id::int = 2 then 'Biratnagar' when station_id::int = 3 then 'Barisal' end station_name,substring(date_time from 1 for  20) as date_time, date_time::timestamp::date as date_info,coalesce(temperature,'') temperature,coalesce(dew_point_temperature,'') dew_point_temperature, coalesce(humidity,'') humidity,coalesce(solar_radiation,'') solar_radiation, coalesce(wind_speed,'') wind_speed, coalesce(wind_direction,'') wind_direction, coalesce(soil_moisture,'') soil_moisture, coalesce(rainfall,'') rainfall, coalesce(qfe,'') qfe,coalesce(qff,'') qff from weather_observed where station_id like '"+str(station_id)+"' AND date_time::timestamp BETWEEN '"+str(from_date)+" 00:00:00'::timestamp and '"+str(to_date)+" 23:59:59'::timestamp order by date_time::timestamp) select station_name, date_info::text,min(cast(temperature as double precision)) temp_min, max(cast(temperature as double precision)) temp_max, avg(cast(temperature as double precision)) temp_avg,min(cast(humidity as double precision)) humidity_min, max(cast(humidity as double precision)) humidity_max, avg(cast(humidity as double precision)) humidity_avg,sum(cast(solar_radiation as double precision)) sum_solar_radiation,SUM(NULLIF(rainfall, '')::numeric) sum_rainfall from t1 group by date_info,station_name order by date_info")

    categories = []
    series_list_temp = []
    series_list_hum = []
    series_list_solar_rad = []
    series_list_rainfall = []

    temp_min_list = []
    temp_max_list = []
    temp_avg_list = []

    hum_min_list = []
    hum_max_list = []
    hum_avg_list = []

    solar_rad_list = []
    rainfall_list = []

    for row in temp_dict:
        categories.append(str(row['date_info']))
        temp_min_list.append(float(row['temp_min']))
        temp_max_list.append(float(row['temp_max']))
        temp_avg_list.append(float(row['temp_avg']))

        hum_min_list.append(float(row['humidity_min']))
        hum_max_list.append(float(row['humidity_max']))
        hum_avg_list.append(float(row['humidity_avg']))

        solar_rad_list.append(float(row['sum_solar_radiation']))
        rainfall_list.append(float(row['sum_rainfall']))

    series_list_temp.append({'name': 'Min', 'data': temp_min_list})
    series_list_temp.append({'name': 'Max', 'data': temp_max_list})
    series_list_temp.append({'name': 'Avg', 'data': temp_avg_list})

    series_list_hum.append({'name': 'Min', 'data': hum_min_list})
    series_list_hum.append({'name': 'Max', 'data': hum_max_list})
    series_list_hum.append({'name': 'Avg', 'data': hum_avg_list})

    series_list_solar_rad.append({'name': 'Sum Srad', 'data': solar_rad_list})
    series_list_rainfall.append({'name': 'Sum Rainfall', 'data': rainfall_list})

    print categories
    print series_list_temp

    #data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    return HttpResponse(json.dumps({
        'category_list':categories,
        'series_list_temp':series_list_temp,
        'series_list_hum':series_list_hum,
        'series_list_solar_rad':series_list_solar_rad,
        'series_list_rainfall':series_list_rainfall

    }))


@login_required
def delete_weather_sms_form(request, sms_rule_id):
    query = "select voice_sms_file_path from weather_sms_rule where id = " + str(sms_rule_id)
    df = pandas.read_sql(query, connection)
    path = df.voice_sms_file_path.tolist()[0]
    if os.path.exists(path):
        os.remove(path)
    delete_rules_details = "delete from weather_sms_rule_details where id in (select unnest(regexp_split_to_array(rules_relation, '[&||]'))::int from weather_sms_rule_relation where weather_sms_rule_id = "+str(sms_rule_id)+")"
    __db_commit_query(delete_rules_details)
    delete_query = "delete from weather_sms_rule where id = " + str(sms_rule_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> SMS Rule has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/weather_sms_rule_list/")


@login_required
def edit_weather_sms_form(request, sms_rule_id):
    org_list = getOrgList(request)
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

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,parameter_name from weather_parameters"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    parameter_name = df.parameter_name.tolist()
    parameter = zip(id, parameter_name)

    query = "select id,group_name from group_details"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    grp_id = df.id.tolist()
    grp_name = df.group_name.tolist()
    grp = zip(grp_id, grp_name)

    info_query = "with first_q as( SELECT weather_sms_rule.id,category_id, sms_description,org_id, program_id,crop_id,season_id,variety_id,stage_id,coalesce(sms_type,'') sms_type,coalesce(content_id,'') content_id,group_id,rules_relation FROM weather_sms_rule,weather_sms_rule_relation where weather_sms_rule.id = weather_sms_rule_relation.weather_sms_rule_id and weather_sms_rule.id = " + str(
        sms_rule_id) + "), q2 as ( select unnest(regexp_split_to_array(rules_relation, '[&||]')) details_id,* from first_q )select q2.*,weather_sms_rule_details.*,substring(rules_relation,position(weather_sms_rule_details.id::text in rules_relation)::int-1,1) operations from weather_sms_rule_details,q2 where weather_sms_rule_details.id = q2.details_id::int"
    data = json.dumps(__db_fetch_values_dict(info_query))

    return render(request, 'ifcmodule/edit_weather_sms_form.html',
                  {'sms_rule_id': sms_rule_id, 'data': data, 'organization': organization, 'season': season,
                   'crop': crop, 'parameter': parameter, 'grp':grp})


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
        sms_type = request.POST.get('sms_type')
        content_id = request.POST.get('content_id', '')
        group_id = request.POST.get('group')
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

            # deletePreviousAudio
            query = "select voice_sms_file_path from weather_sms_rule where id = " + str(sms_rule_id)
            df = pandas.read_sql(query, connection)
            path = df.voice_sms_file_path.tolist()[0]
            if os.path.exists(path):
                os.remove(path)

        update_query = "UPDATE public.weather_sms_rule SET sms_type='" + str(sms_type) + "',category_id=" + str(
            category_id) + ", sms_description='" + str(sms_description) + "', voice_sms_file_path='" + str(
            voice_sms_file_path) + "', org_id=" + str(org_id) + ", program_id=" + str(program_id) + ", crop_id=" + str(
            crop_id) + " , variety_id=" + str(variety_id) + ", season_id=" + str(
            season_id) + ", updated_at=now() , updated_by=" + str(user_id) + ", stage_id=" + str(
            stage_id) + ",content_id = '" + str(content_id) + "',group_id = "+str(group_id)+" WHERE id=" + str(sms_rule_id) + ""
        # print(update_query)
        __db_commit_query(update_query)

        rules_relation = ""

        while count >= idx:
            print(idx, count)
            parameter_id = request.POST.get('parameter_id_' + str(idx))
            parameter_type_id = request.POST.get('parameter_type_' + str(idx))
            sub_parameter_id = request.POST.get('sub_parameter_id_' + str(idx))
            consecutive_days = request.POST.get('consecutive_days_' + str(idx))
            operators = request.POST.get('operators_' + str(idx))
            calculation_type = request.POST.get('calculation_type_' + str(idx))
            unit = request.POST.get('unit_' + str(idx))
            unit = unit.encode('utf-8').strip()
            details_id = request.POST.get('details_id_' + str(idx))
            parameter_value = request.POST.get('parameter_value_' + str(idx))
            # print(details_id,parameter_id,parameter_type_id,sub_parameter_id,consecutive_days,operators,calculation_type,unit)
            if not len(str(details_id)):
                insert_query_rules = "INSERT INTO public.weather_sms_rule_details (parameter_id, parameter_type_id, sub_parameter_id, consecutive_days, operators, calculation_type, unit,parameter_value)VALUES(" + str(
                    parameter_id) + ", " + str(parameter_type_id) + ", " + str(sub_parameter_id) + ", " + str(
                    consecutive_days) + ", '" + str(operators) + "', '" + str(calculation_type) + "', '" + str(
                    unit) + "','" + str(parameter_value) + "') returning id"
                # print(insert_query_rules)
                details_id = __db_fetch_single_value(insert_query_rules)
            else:
                update_query_rules = "UPDATE public.weather_sms_rule_details SET parameter_value='" + str(
                    parameter_value) + "',parameter_id=" + str(parameter_id) + ", parameter_type_id=" + str(
                    parameter_type_id) + ", sub_parameter_id=" + str(sub_parameter_id) + ", consecutive_days=" + str(
                    consecutive_days) + ", operators='" + str(operators) + "', calculation_type='" + str(
                    calculation_type) + "' , unit='" + str(unit) + "' WHERE id=" + str(details_id) + ""
                __db_commit_query(update_query_rules)
            if idx != 1:
                operation = request.POST.get('operation_' + str(idx))
                rules_relation += str(operation) + str(details_id)
            else:
                rules_relation += str(details_id)
            idx += 1

        # update weather_sms_rule_relation table

        update_query_relation = "UPDATE public.weather_sms_rule_relation SET  rules_relation='" + str(
            rules_relation) + "' WHERE weather_sms_rule_id=" + str(sms_rule_id) + ""
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
    df = pandas.read_sql(query, connection)
    if not df.empty:
        weather_sms_rule_id = df.weather_sms_rule_id.unique().tolist()
        # print(weather_sms_rule_id)
        for each in weather_sms_rule_id:
            # print(df.loc[df['weather_sms_rule_id'] == each]['weather_sms_rule_id'])

            temp_weather_sms_rule_id = df.loc[df.index[df['weather_sms_rule_id'] == each]][
                'weather_sms_rule_id'].tolist()
            # print(temp_weather_sms_rule_id)
            wea_sms_id = temp_weather_sms_rule_id[0]
            parameter_id = df.loc[df.index[df['weather_sms_rule_id'] == each]]['parameter_id'].tolist()
            parameter_type_id = df.loc[df.index[df['weather_sms_rule_id'] == each]]['parameter_type_id'].tolist()
            sub_parameter_name = df.loc[df.index[df['weather_sms_rule_id'] == each]]['sub_parameter_name'].tolist()
            consecutive_days = df.loc[df.index[df['weather_sms_rule_id'] == each]]['consecutive_days'].tolist()
            operators = df.loc[df.index[df['weather_sms_rule_id'] == each]]['operators'].tolist()
            calculation_type = df.loc[df.index[df['weather_sms_rule_id'] == each]]['calculation_type'].tolist()
            parameter_value = df.loc[df.index[df['weather_sms_rule_id'] == each]]['parameter_value'].tolist()
            operations = df.loc[df.index[df['weather_sms_rule_id'] == each]]['operations'].tolist()
            # print(temp_weather_sms_rule_id,parameter_id,parameter_type_id,consecutive_days,operators,calculation_type,operations)
            result_str_condition = ""
            for i in range(0, len(temp_weather_sms_rule_id)):
                column_name = get_column_name(parameter_id[i], sub_parameter_name[i])
                agg_fun_sub_parameter = get_agg_function_sub_parameter(sub_parameter_name[i])
                if parameter_type_id[i] == 2:
                    str_condition = "with t as( select place_id, date_time::date," + str(
                        agg_fun_sub_parameter) + "(" + str(
                        column_name) + "::numeric) daily_calc from weather_forecast where date_time::date between now()::date + interval '1 day' and now()::date + interval '" + str(
                        consecutive_days[
                            i]) + " day' group by place_id,date_time::date)select distinct place_id from t where place_id is not null group by place_id having " + str(
                        calculation_type[i]) + "(daily_calc) " + str(operators[i]) + " " + str(parameter_value[i]) + " "
                elif parameter_type_id[i] == 1:
                    str_condition = "with t as( select station_id, date_time::date," + str(
                        agg_fun_sub_parameter) + "(" + str(
                        column_name) + "::numeric) daily_calc from weather_observed where date_time::date between now()::date - interval '1 day' and now()::date - interval '" + str(
                        consecutive_days[
                            i]) + " day' group by station_id,date_time::date)select  (select distinct place_id from union_place_station_mapping where station_id = t.station_id::int)place_id from t where station_id is not null group by station_id having " + str(
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

            query_t = "insert into weather_sms_rule_queue(weather_sms_rule_id,mobile_number,sms_description,crop_id,season_id,variety_id,stage_id,org_id,program_id,union_id) with dfg1 as( select * from farmer_crop_info,farmer_crop_stage where farmer_crop_info.id = farmer_crop_stage.farmer_crop_id),dfg as ( select * from dfg1,farmer where dfg1.farmer_id = farmer.id ) select weather_sms_rule.id weather_sms_rule_id,(select mobile_number from farmer where id = farmer_id limit 1)mobile_number,sms_description, weather_sms_rule.crop_id,weather_sms_rule.season_id,weather_sms_rule.variety_id,weather_sms_rule.stage_id,weather_sms_rule.org_id,weather_sms_rule.program_id,( SELECT union_id FROM farmer WHERE id = farmer_id limit 1) union_id from weather_sms_rule,dfg where weather_sms_rule.id = " + str(
                wea_sms_id) + " and weather_sms_rule.crop_id = dfg.crop_id and weather_sms_rule.season_id = dfg.season_id and weather_sms_rule.variety_id = dfg.crop_variety_id and weather_sms_rule.stage_id = dfg.stage::int and weather_sms_rule.org_id = dfg.organization_id and weather_sms_rule.program_id = dfg.program_id and farmer_id=any ( select distinct farmer_id from farmer_crop_info where union_id = any (select distinct union_id from union_place_station_mapping where place_id =any (" + str(
                result_str_condition) + "))) order by farmer_id"
            __db_commit_query(query_t)
            # query_u = "update weather_sms_rule set sms_status = 1 where id = "+str(wea_sms_id)
            # __db_commit_query(query_u)
            if each == 77:
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

@login_required
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

@login_required
def send_sms(request,id):
    q = "update management_sms_que set status = 'Sent',updated_at = NOW(),updated_by = "+str(request.user.id)+" where id = "+str(id)
    __db_commit_query(q)
    return HttpResponse(json.dumps('ok'), content_type="application/json", status=200)




@login_required
def weather_sms_que_list(request):
    weather_sms_que_list = ''
    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select distinct geo_country_id,country_name from vwunion"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    country_id = df.geo_country_id.tolist()
    country_name = df.country_name.tolist()
    country = zip(country_id, country_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    return render(request, 'ifcmodule/weather_sms_que_list.html', {
        'weather_sms_que_list': weather_sms_que_list, 'season': season, 'crop_list': crop_list, 'country': country
    })

@login_required
def management_sms_que_list(request):
    management_sms_que_list = ''
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

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)
    return render(request, 'ifcmodule/management_sms_que_list.html', {
        'management_sms_que_list': management_sms_que_list,'season': season,'crop_list':crop_list,'country':country
    })

@login_required
def approve_farmer_sms(request):
    org_list = getOrgList(request)
    weather_sms_rule_id = request.POST.get('weather_sms_rule_id')
    union_id  = request.POST.get('union_id')
    crop_id = request.POST.get('crop_id')
    season_id = request.POST.get('season_id')
    variety_id = request.POST.get('variety_id')
    stage_id = request.POST.get('stage_id')
    schedule_time = request.POST.get('schedule_time')
    username = request.user.username
    query = "INSERT INTO public.sms_que (mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id, content_type,voice_sms_file_path,content_id) SELECT mobile_number,sms_description,schedule_time,id,'weather_sms_rule_queue' as sms_source ,status ,'"+str(username)+"' as created_by,now() as created_at,(select country_id from farmer where mobile_number = weather_sms_rule_queue.mobile_number limit 1),content_type,voice_sms_file_path,content_id FROM weather_sms_rule_queue WHERE status = 'New' and org_id::int = any('{"+str(org_list).strip('[]')+" }') and union_id = '"+str(union_id)+"' and weather_sms_rule_id = '"+str(weather_sms_rule_id)+"' and crop_id = '"+str(crop_id)+"' and season_id = '"+str(season_id)+"' and variety_id = '"+str(variety_id)+"' and stage_id = '"+str(stage_id)+"' and schedule_time::date = '"+str(schedule_time)+"'::date"
    __db_commit_query(query)
    query_t = "UPDATE public.weather_sms_rule_queue SET status='Sent'::text WHERE union_id = '"+str(union_id)+"' and weather_sms_rule_id = '"+str(weather_sms_rule_id)+"' and crop_id = '"+str(crop_id)+"' and season_id = '"+str(season_id)+"' and variety_id = '"+str(variety_id)+"' and stage_id = '"+str(stage_id)+"' and schedule_time::date = '"+str(schedule_time)+"'::date"
    __db_commit_query(query_t)
    return HttpResponse("")

@login_required
def approve_farmer_sms_management(request):
    org_list = getOrgList(request)
    sms_id = request.POST.get('sms_id')
    union_id  = request.POST.get('union_id')
    crop_id = request.POST.get('crop_id')
    season_id = request.POST.get('season_id')
    variety_id = request.POST.get('variety_id')
    stage_id = request.POST.get('stage_id')
    schedule_time = request.POST.get('schedule_time')
    username = request.user.username
    query = "INSERT INTO public.sms_que (mobile_number, sms_text, schedule_time,alertlog_id, sms_source, status, created_by, created_at, country_id, content_type,voice_sms_file_path,content_id)  with t as( select *,(select union_id from farmer where id = farmer_id::int limit 1) union_id from management_sms_que) SELECT mobile_number, sms_text, schedule_time, id, 'management_sms_que' AS sms_source, status, '"+str(username)+"' AS created_by, Now() AS created_at, (SELECT country_id FROM farmer WHERE mobile_number = t.mobile_number LIMIT 1), content_type,voice_sms_file_path,content_id FROM t WHERE status = 'New' and organization_id = any('{"+str(org_list).strip('[]')+" }') AND union_id = '"+str(union_id)+"' AND sms_id = '"+str(sms_id)+"' AND crop_id = '"+str(crop_id)+"' AND season_id = '"+str(season_id)+"' AND variety_id = '"+str(variety_id)+"' AND stage_id = '"+str(stage_id)+"' AND schedule_time::date = '"+str(schedule_time)+"'::date"
    __db_commit_query(query)
    query_t = "UPDATE public.management_sms_que SET status = 'Sent' :: text WHERE farmer_id = any(select id from farmer where union_id = '"+str(union_id)+"') AND sms_id = '"+str(sms_id)+"' AND crop_id = '"+str(crop_id)+"' AND season_id = '"+str(season_id)+"' AND variety_id = '"+str(variety_id)+"' AND stage_id = '"+str(stage_id)+"' AND schedule_time::date= '"+str(schedule_time)+"'::date"
    __db_commit_query(query_t)
    return HttpResponse("")

@login_required
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
        stage_id) + "' and schedule_time::date = '" + str(schedule_time) + "'::date"
    __db_commit_query(query_t)
    return HttpResponse("")


@login_required
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
    __db_commit_query(query_t)
    return HttpResponse("")

@login_required
def getDivisions(request):
    obj = request.POST.get('obj')
    query = "select distinct geo_zone_id id,division_name field_name from vwunion where geo_country_id = '"+str(obj)+"'"
    data = json.dumps(__db_fetch_values_dict(query),default=decimal_date_default)
    return HttpResponse(data)

@login_required
def getDistricts(request):
    obj = request.POST.get('obj')
    query = "select distinct geo_district_id id,district_name field_name from vwunion where geo_zone_id = '"+str(obj)+"'"
    data = json.dumps(__db_fetch_values_dict(query),default=decimal_date_default)
    return HttpResponse(data)

@login_required
def getUpazillas(request):
    obj = request.POST.get('obj')
    query = "select distinct geo_upazilla_id id,upazilla_name field_name from vwunion where geo_district_id = '"+str(obj)+"'"
    data = json.dumps(__db_fetch_values_dict(query),default=decimal_date_default)
    return HttpResponse(data)

@login_required
def getUnions(request):
    obj = request.POST.get('obj')
    query = "select distinct id,name field_name from vwunion where geo_upazilla_id = '"+str(obj)+"'"
    data = json.dumps(__db_fetch_values_dict(query),default=decimal_date_default)
    return HttpResponse(data)

@login_required
def getWeatherQueueData(request):
    org_list = getOrgList(request)
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    crop = request.POST.get('crop')
    variety = request.POST.get('variety')
    season = request.POST.get('season')
    stage = request.POST.get('stage')
    country = request.POST.get('country')
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazilla = request.POST.get('upazilla')
    union = request.POST.get('union')
    content_type = request.POST.get('content_type')
    query = "with t as( SELECT DISTINCT weather_sms_rule_id AS sms_id, sms_description,(select name from vwunion where id = union_id::int limit 1) union_name, union_id, crop_id, season_id, variety_id,(select stage_name from crop_stage where id = stage_id::int limit 1) , stage_id, schedule_time::date, content_type, substring(voice_sms_file_path FROM 8) voice_sms_file_path,(select sms_type from weather_sms_rule where id = weather_sms_rule_id limit 1) FROM weather_sms_rule_queue, vwunion WHERE union_id::int = vwunion.id AND status = 'New' and org_id::int = any('{"+str(org_list).strip('[]')+" }') and schedule_time between '" + str( from_date) + " 00:00:00'::timestamp and '" + str( to_date) + " 23:59:59'::timestamp and geo_country_id::text like '" + str( country) + "' and geo_zone_id::text like '" + str(division) + "' and geo_upazilla_id::text like '" + str( upazilla) + "' and geo_district_id::text like '" + str(district) + "' and union_id::text like '" + str( union) + "' and crop_id::text like '" + str(crop) + "' and variety_id::text like '" + str(variety) + "' and season_id::text like '" + str(season) + "' and stage_id::text like '" + str(stage) + "' and content_type::text like '"+str(content_type)+"')select *,( select count(distinct mobile_number) FROM weather_sms_rule_queue WHERE status = 'New' AND union_id = t.union_id AND weather_sms_rule_id = sms_id AND crop_id = t.crop_id AND season_id = t.season_id AND variety_id = t.variety_id AND stage_id = t.stage_id AND schedule_time::date = t.schedule_time::date )farmer_cnt from t"
    print(query)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

@login_required
def getManagementQueueData(request):
    org_list = getOrgList(request)
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    crop = request.POST.get('crop')
    variety = request.POST.get('variety')
    season = request.POST.get('season')
    stage = request.POST.get('stage')
    country = request.POST.get('country')
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazilla = request.POST.get('upazilla')
    union = request.POST.get('union')
    content_type = request.POST.get('content_type')
    query = "WITH t AS( SELECT ( SELECT union_id FROM farmer WHERE id = farmer_id), * FROM management_sms_que), t1 as ( SELECT DISTINCT sms_id, sms_text, union_id, crop_id, season_id, variety_id, stage_id, schedule_time::date, content_type, substring(voice_sms_file_path FROM 8)voice_sms_file_path,(select sms_type from management_sms_rule where id = sms_id) FROM t, vwunion WHERE union_id::int = vwunion.id AND status = 'New' and organization_id = any('{"+str(org_list).strip('[]')+" }') AND schedule_time BETWEEN '"+str(from_date)+" 00:00:00'::timestamp AND '"+str(to_date)+" 23:59:59'::timestamp AND geo_country_id::text LIKE '"+str(country)+"' AND geo_zone_id::text LIKE '"+str(division)+"' AND geo_upazilla_id::text LIKE '"+str(upazilla)+"' AND geo_district_id::text LIKE '"+str(district )+"' AND union_id::text LIKE '"+str(union)+"' AND crop_id::text LIKE '"+str(crop)+"' AND variety_id::text LIKE '" + str(variety) + "' AND season_id::text LIKE '" + str(season) + "' AND stage_id::text LIKE '" + str(stage) + "' and content_type::text like '"+str(content_type)+"' ) SELECT *,( SELECT count(DISTINCT mobile_number) FROM t WHERE t.union_id = t1.union_id AND t.sms_id = t1.sms_id AND t.crop_id = t1.crop_id AND t.season_id = t1.season_id AND t.variety_id = t1.variety_id AND t.stage_id = t1.stage_id AND t.schedule_time::date = t1.schedule_time::date and t.content_type = t1.content_type)farmer_cnt FROM t1"
    print(query)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

@login_required
def data_graph_view(request):
    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop = zip(crop_id, crop_name)

    query = "select distinct geo_country_id,country_name from vwunion"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    country_id = df.geo_country_id.tolist()
    country_name = df.country_name.tolist()
    country = zip(country_id, country_name)

    query = "select id,organization from usermodule_organizations"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    return render(request,'ifcmodule/data_graph_view.html',{'country':country,'crop':crop,'organization':organization})

@login_required
def getGraphData(request):
    program = request.POST.get('program')
    organization = request.POST.get('organization')
    crop = json.loads(request.POST.get('crop'))
    country = request.POST.get('country')
    if crop is None:
        query_farmer = "select (select name from geo_zone where id = zone_id)division_name,count(*) farmer_count from farmer where organization_id::text like '"+str(organization)+"' and program_id::text like '"+str(program)+"' and country_id::text like '"+str(country)+"' group by zone_id "
        query_land = "select(select name from geo_zone where id = zone_id)division_name,sum(land_size::numeric) land_size from farmer_crop_info where unit_id = 2  and farmer_id = any(select id from farmer where organization_id::text like '"+str(organization)+"' and program_id::text like '"+str(program)+"' and country_id::text like '"+str(country)+"') group by zone_id"
    else:
        crop = str(crop).replace('[','').replace(']','').replace('\'', '').replace('u','').replace(' ','')
        query_farmer = "select(select name from geo_zone where id = zone_id)division_name,count(*) farmer_count from farmer where organization_id::text like '"+str(organization)+"' and program_id::text like '"+str(program)+"' and country_id::text like '"+str(country)+"' and id = any(select farmer_id from farmer_crop_info where crop_id::text = any(string_to_array('"+str(crop)+"',','))) group by zone_id"
        query_land = "select(select name from geo_zone where id = zone_id)division_name,sum(land_size::numeric) land_size from farmer_crop_info where unit_id = 2 and crop_id::text = any(string_to_array('"+str(crop)+"',',')) and farmer_id = any(select id from farmer where organization_id::text like '"+str(organization)+"' and program_id::text like '"+str(program)+"' and country_id::text like '"+str(country)+"') group by zone_id"

    print(query_farmer,query_land)

    df = pandas.DataFrame()
    df = pandas.read_sql(query_farmer,connection)
    farmer_categories = df.division_name.tolist()
    farmer_count  = df.farmer_count.tolist()
    total_farmer = sum(farmer_count)
    df = pandas.DataFrame()
    df = pandas.read_sql(query_land, connection)
    land_categories = df.division_name.tolist()
    land_count = df.land_size.tolist()
    total_land = sum(land_count)

    data = json.dumps({'farmer_categories':farmer_categories,
            'farmer_count':farmer_count,
            'land_categories':land_categories,
            'land_count':land_count,
            'total_farmer':total_farmer,
            'total_land':total_land
            })
    print(data)
    return HttpResponse(data)



def bulk_upload(request):
    response = {}
    if request.method == 'POST':
        try:
            myfile = request.FILES['fileToUpload']
        except Exception, e:
            return render(request, 'lt_bulk_upload.html', {
                'error_msg': 'You have not provided any file'
            })
        f_s = FileSystemStorage()
        filename = f_s.save(myfile.name, myfile)
        uploaded_file_url = f_s.url(filename)
        rejected_file_name = process_bulk_data(filename)

        if rejected_file_name:
            response['rejected_file_name'] = rejected_file_name
    return render(request, 'ifcmodule/lt_bulk_upload.html', {
        'response': response
    })



def check_input_validaity(inp_loc, level, parent_loc=None):
    if level == 'District':
        chk = __db_fetch_single_value("select count(*) from geo_district where name = '" + str(
            inp_loc) + "' and geo_zone_id = (select id from geo_zone where name = '" + str(parent_loc) + "')")
        if chk > 0:
            return True
    elif level == 'Upazilla':
        chk = __db_fetch_single_value("select count(*) from geo_upazilla where name = '" + str(
            inp_loc) + "' and geo_district_id = (select id from geo_district where name = '" + str(parent_loc) + "')")
        if chk > 0:
            return True
    elif level == 'Union':
        chk = __db_fetch_single_value("select count(*) from geo_union where name = '" + str(
            inp_loc) + "' and geo_upazilla_id = (select id from geo_upazilla where name = '" + str(parent_loc) + "')")
        if chk > 0:
            return True
    elif level == 'Country':
        chk = __db_fetch_single_value("select count(*) from geo_country where name = '" + str(inp_loc) + "'")
        if chk > 0:
            return True
    elif level == 'Zone':
        chk = __db_fetch_single_value("select count(*) from geo_zone where name = '" + str(
            inp_loc) + "' and geo_country_id = (select id from geo_country where name = '" + str(parent_loc) + "')")
        if chk > 0:
            return True
    elif level == 'Organization':
        chk = __db_fetch_single_value("select count(*) from usermodule_organizations where organization = '" + str(
            inp_loc) + "'")
        if chk > 0:
            return True
    elif level == 'Program':
        chk = __db_fetch_single_value("select count(*) from usermodule_programs where program_name = '" + str(
            inp_loc) + "' and org_id = (select id from usermodule_organizations where organization = '" + str(
            parent_loc) + "')")
        if chk > 0:
            return True
    elif level == 'Season':
        chk = __db_fetch_single_value("select count(*) from cropping_season where season_name = '" + str(
            inp_loc) + "'")
        if chk > 0:
            return True
    elif level == 'Crop':
        chk = __db_fetch_single_value("select count(*) from crop where crop_name = '" + str(
            inp_loc) + "'")
        if chk > 0:
            return True
    elif level == 'Variety':
        chk = __db_fetch_single_value("select count(*) from crop_variety where variety_name = '" + str(
            inp_loc) + "' and crop_id = (select id from crop where crop_name = '" + str(parent_loc) + "')")
        if chk > 0:
            return True
    elif level == 'Land Unit':
        chk = __db_fetch_single_value("select count(*) from land_units where unit_name = '" + str(
            inp_loc) + "'")
        if chk > 0:
            return True
    elif level == 'Sowing Date':
        if len(inp_loc) == 10:
            if "-" in inp_loc:
                date_parts = inp_loc.split('-')
                if len(date_parts) == 3:
                    if len(date_parts[0]) == 4 and len(date_parts[1]) == 2 and len(date_parts[2]) == 2:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
    return False


def check_crop_has_different_valid_geolocation(crop_zone, crop_district, crop_upazilla, crop_union):
    if crop_district != 'nan' and crop_upazilla != 'nan' and crop_union != 'nan':
        if check_input_validaity(crop_district, 'District', crop_zone):
            district_id = __db_fetch_single_value("select id from geo_district where name = '" + str(
                crop_district) + "' and geo_zone_id = " + str(zone_id))
            if check_input_validaity(crop_upazilla, 'Upazilla', crop_district):
                upazilla_id = __db_fetch_single_value("select id from geo_upazilla where name = '" + str(
                    crop_upazilla) + "' and geo_district_id = " + str(district_id))
                if check_input_validaity(crop_union, 'Union', crop_upazilla):
                    union_id = __db_fetch_single_value("select id from geo_union where name = '" + str(
                        crop_union) + "' and geo_upazilla_id = " + str(upazilla_id))
                    return (district_id, upazilla_id, union_id)
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return 'Not Present'



def check_crop_combination_exists(zone_id, crop_district_id, crop_upazilla_id, crop_union_id, fid, crop_id, season_id,
                                  variety_id, sowing_date, land_size):
    return __db_fetch_single_value(
        "select count(*) as c from farmer_crop_info where farmer_id = " + str(fid) + " and crop_id = " + str(
            crop_id) + " and season_id = " + str(season_id) + " and crop_variety_id = " + str(
            variety_id) + " and sowing_date = '" + str(sowing_date) + "' and land_size = '" + str(
            land_size) + "' and zone_id = " + str(zone_id) + " and district_id = " + str(
            crop_district_id) + " and upazila_id = " + str(crop_upazilla_id) + " and union_id = " + str(crop_union_id))


def check_farmer_already_exists(country_id, zone_id, district_id, upazilla_id, union_id, organization_id, program_id,
                                farmer_name, mobile_no):
    return __db_fetch_single_value(
        "select count(*) as c from farmer where farmer_name = '" + str(farmer_name) + "' and district_id = " + str(
            district_id) + " and upazila_id = " + str(upazilla_id) + " and union_id = " + str(
            union_id) + " and mobile_number = '" + str(mobile_no) + "' and zone_id = " + str(
            zone_id) + " and country_id = " + str(country_id) + " and organization_id = " + str(
            organization_id) + " and program_id = " + str(program_id))



def get_farmer_already_exists(country_id, zone_id, district_id, upazilla_id, union_id, organization_id, program_id,
                                farmer_name, mobile_no):
    return __db_fetch_single_value(
        "select id from farmer where farmer_name = '" + str(farmer_name) + "' and district_id = " + str(
            district_id) + " and upazila_id = " + str(upazilla_id) + " and union_id = " + str(
            union_id) + " and mobile_number = '" + str(mobile_no) + "' and zone_id = " + str(
            zone_id) + " and country_id = " + str(country_id) + " and organization_id = " + str(
            organization_id) + " and program_id = " + str(program_id)+" limit 1")



def process_bulk_data(file_url):
    df = pandas.read_excel('onadata/media/' + str(file_url),
                       sheet_name=0, index_col=None,
                       header=0, na_values=['NaN'],
                       usecols="A:S", dtype=str)

    invalid_df = pandas.DataFrame(index=None,
                              columns=[u'Farmer Name', u'Mobile No', u'Country', u'Zone', u'District',
                                       u'Upazilla', u'', u'Union', u'Organization', u'Program', u'Season', u'Crop',
                                       u'Variety', u'Sowing Date', u'Land Size', u'Crop District', u'Crop Upazilla',
                                       u'Crop Union', u'Problem Field'])

    for index, row in df.iterrows():
        if check_input_validaity(row['Country'].strip(), 'Country'):
            country_id = __db_fetch_single_value(
                "select id from geo_country where name = '" + str(row['Country'].strip()) + "'")
            if check_input_validaity(row['Zone'].strip(), 'Zone', row['Country'].strip()):
                zone_id = __db_fetch_single_value("select id from geo_zone where name = '" + str(
                    row['Zone'].strip()) + "' and geo_country_id = " + str(country_id))
                if check_input_validaity(row['District'].strip(), 'District', row['Zone'].strip()):
                    district_id = __db_fetch_single_value("select id from geo_district where name = '" + str(
                        row['District'].strip()) + "' and geo_zone_id = " + str(zone_id))
                    if check_input_validaity(row['Upazilla'].strip(), 'Upazilla', row['District'].strip()):
                        upazilla_id = __db_fetch_single_value("select id from geo_upazilla where name = '" + str(
                            row['Upazilla'].strip()) + "' and geo_district_id = " + str(district_id))
                        if check_input_validaity(row['Union'].strip(), 'Union', row['Upazilla'].strip()):
                            union_id = __db_fetch_single_value("select id from geo_union where name = '" + str(
                                row['Union'].strip()) + "' and geo_upazilla_id = " + str(upazilla_id))
                            if check_input_validaity(row['Organization'].strip(), 'Organization'):
                                organization_id = __db_fetch_single_value(
                                    "select id from usermodule_organizations where organization = '" + str(
                                        row['Organization'].strip()) + "'")
                                if check_input_validaity(row['Program'].strip(), 'Program',
                                                         row['Organization'].strip()):
                                    program_id = __db_fetch_single_value(
                                        "select id from usermodule_programs where program_name = '" + str(
                                            row['Program'].strip()) + "' and org_id = " + str(organization_id))
                                    if check_input_validaity(row['Season'].strip(), 'Season'):
                                        season_id = __db_fetch_single_value(
                                            "select id from cropping_season where season_name = '" + str(
                                                row['Season'].strip()) + "'")
                                        if check_input_validaity(row['Crop'].strip(), 'Crop'):
                                            crop_id = __db_fetch_single_value(
                                                "select id from crop where crop_name = '" + str(
                                                    row['Crop'].strip()) + "'")
                                            if check_input_validaity(row['Variety'].strip(), 'Variety',
                                                                     row['Crop'].strip()):
                                                variety_id = __db_fetch_single_value(
                                                    "select id from crop_variety where variety_name = '" + str(
                                                        row['Variety'].strip()) + "' and crop_id=" + str(crop_id))
                                                if check_input_validaity(row['Sowing Date'].strip(), 'Sowing Date'):
                                                    sowing_date = row['Sowing Date'].strip()
                                                    if check_input_validaity(row['Land Unit'].strip(), 'Land Unit'):
                                                        land_unit = __db_fetch_single_value(
                                                            "select id from land_units where unit_name = '" + str(
                                                                row['Land Unit'].strip()) + "'")
                                                        crop_geo_locations = check_crop_has_different_valid_geolocation(
                                                            row['Zone'].strip(), row['Crop District'].strip(),
                                                            row['Crop Upazilla'].strip(), row['Crop Union'].strip())
                                                        if crop_geo_locations != False:
                                                            if crop_geo_locations == 'Not Present':
                                                                crop_district_id = district_id
                                                                crop_upazila_id = upazilla_id
                                                                crop_union_id = union_id
                                                            else:
                                                                crop_district_id = crop_geo_locations[0]
                                                                crop_upazila_id = crop_geo_locations[1]
                                                                crop_union_id = crop_geo_locations[2]
                                                            ########################################################
                                                            fc = check_farmer_already_exists(country_id, zone_id,
                                                                                             district_id,
                                                                                             upazilla_id, union_id,
                                                                                             organization_id,
                                                                                             program_id,
                                                                                             row['Farmer Name'].strip(),
                                                                                             row['Mobile No'].strip())
                                                            if fc == 0:
                                                                fid = __db_run_query(
                                                                    "INSERT INTO public.farmer (farmer_name, district_id, upazila_id, union_id, village_name, mobile_number, created_at, created_by, updated_at, updated_by, organization_id, program_id, status, zone_id, country_id) VALUES('" + str(
                                                                        row['Farmer Name'].strip()) + "', " + str(
                                                                        district_id) + ", " + str(
                                                                        upazilla_id) + ", " + str(
                                                                        union_id) + ", '" + str(
                                                                        row['Village'].strip()) + "', '" + str(
                                                                        row[
                                                                            'Mobile No'].strip()) + "', now(), 'ifc', now(), 'ifc', " + str(
                                                                        organization_id) + ", " + str(
                                                                        program_id) + ", 1, " + str(
                                                                        zone_id) + ", " + str(
                                                                        country_id) + ") returning id")
                                                                if fid:
                                                                    cc = check_crop_combination_exists(zone_id,
                                                                                                       crop_district_id,
                                                                                                       crop_upazila_id,
                                                                                                       crop_union_id,
                                                                                                       fid,
                                                                                                       crop_id,
                                                                                                       season_id,
                                                                                                       variety_id,
                                                                                                       sowing_date, row[
                                                                                                           'Land Size'].strip())
                                                                    if cc == 0:
                                                                        cid = __db_run_query(
                                                                            "INSERT INTO public.farmer_crop_info (farmer_id, crop_id, season_id, crop_variety_id, sowing_date, unit_id, land_size, created_at, created_by, updated_at, updated_by, zone_id, district_id, upazila_id, union_id) VALUES(" + str(
                                                                                fid) + ", " + str(crop_id) + ", " + str(
                                                                                season_id) + ", " + str(
                                                                                variety_id) + ", '" + str(
                                                                                sowing_date) + "', " + str(
                                                                                land_unit) + ", '" + str(
                                                                                row[
                                                                                    'Land Size']) + "', now(), 84, now(), 84, " + str(
                                                                                zone_id) + ", " + str(
                                                                                crop_district_id) + ", " + str(
                                                                                crop_upazila_id) + ", " + str(
                                                                                crop_union_id) + ") returning id")
                                                                    else:
                                                                        row['Problem Field'] = 'Crop Combination Already Exists'
                                                                        invalid_df = invalid_df.append(row,
                                                                                                       ignore_index=True)
                                                            else:
                                                                fid = get_farmer_already_exists(country_id, zone_id,
                                                                                             district_id,
                                                                                             upazilla_id, union_id,
                                                                                             organization_id,
                                                                                             program_id,
                                                                                             row['Farmer Name'].strip(),
                                                                                             row['Mobile No'].strip())
                                                                if fid:
                                                                    cc = check_crop_combination_exists(zone_id,
                                                                                                       crop_district_id,
                                                                                                       crop_upazila_id,
                                                                                                       crop_union_id,
                                                                                                       fid,
                                                                                                       crop_id,
                                                                                                       season_id,
                                                                                                       variety_id,
                                                                                                       sowing_date, row[
                                                                                                           'Land Size'].strip())
                                                                    if cc == 0:
                                                                        cid = __db_run_query(
                                                                            "INSERT INTO public.farmer_crop_info (farmer_id, crop_id, season_id, crop_variety_id, sowing_date, unit_id, land_size, created_at, created_by, updated_at, updated_by, zone_id, district_id, upazila_id, union_id) VALUES(" + str(
                                                                                fid) + ", " + str(crop_id) + ", " + str(
                                                                                season_id) + ", " + str(
                                                                                variety_id) + ", '" + str(
                                                                                sowing_date) + "', " + str(
                                                                                land_unit) + ", '" + str(
                                                                                row[
                                                                                    'Land Size']) + "', now(), 84, now(), 84, " + str(
                                                                                zone_id) + ", " + str(
                                                                                crop_district_id) + ", " + str(
                                                                                crop_upazila_id) + ", " + str(
                                                                                crop_union_id) + ") returning id")
                                                                    else:
                                                                        row['Problem Field'] = 'Crop Combination already exists'
                                                                        invalid_df = invalid_df.append(row, ignore_index=True)
                                                    else:
                                                        row['Problem Field'] = 'Invalid Crop Geolocations'
                                                        invalid_df = invalid_df.append(row, ignore_index=True)
                                                else:
                                                    row['Problem Field'] = 'Invalid Sowing Date'
                                                    invalid_df = invalid_df.append(row, ignore_index=True)
                                            else:
                                                row['Problem Field'] = 'Invalid Variety Name'
                                                invalid_df = invalid_df.append(row, ignore_index=True)
                                        else:
                                            row['Problem Field'] = 'Invalid Crop Name'
                                            invalid_df = invalid_df.append(row, ignore_index=True)
                                    else:
                                        row['Problem Field'] = 'Invalid Season Name'
                                        invalid_df = invalid_df.append(row, ignore_index=True)
                                else:
                                    row['Problem Field'] = 'Invalid Program Name'
                                    invalid_df = invalid_df.append(row, ignore_index=True)
                            else:
                                row['Problem Field'] = 'Invalid Organization Name'
                                invalid_df = invalid_df.append(row, ignore_index=True)
                        else:
                            row['Problem Field'] = 'Invalid Union Name'
                            invalid_df = invalid_df.append(row, ignore_index=True)
                    else:
                        row['Problem Field'] = 'Invalid Upazilla Name'
                        invalid_df = invalid_df.append(row, ignore_index=True)
                else:
                    row['Problem Field'] = 'Invalid District Name'
                    invalid_df = invalid_df.append(row, ignore_index=True)
            else:
                row['Problem Field'] = 'Invalid Zone Name'
                invalid_df = invalid_df.append(row, ignore_index=True)
        else:
            row['Problem Field'] = 'Invalid Country Name'
            invalid_df = invalid_df.append(row, ignore_index=True)

    if not invalid_df.empty:
        writer = pandas.ExcelWriter('onadata/media/rejected_data.xlsx')
        invalid_df.to_excel(writer, 'Sheet1')
        writer.save()
        return '/media/rejected_data.xlsx'
    else:
        return None


"""
DASHBOARD

"""

@login_required
def get_dashboard(request):
    org_list = getOrgList(request)
    org_list_text = []
    for row in org_list:
        org_list_text.append(str(row))

    sent_sms_count = __db_fetch_single_value_excption("with t1 as (select id from management_sms_que where organization_id = any('{"+str(org_list).strip('[]')+" }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'text' union select id from weather_sms_rule_queue where org_id in ("+str(org_list_text).strip('[]')+") and weather_sms_rule_queue.status = 'Sent' and weather_sms_rule_queue.content_type = 'text' union select  promotional_sms.id from promotional_sms inner join sms_que on sms_que.alertlog_id = promotional_sms.id where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'text' and organization_id in ("+str(org_list_text).strip('[]')+")) select count(*) over() from t1 limit 1")

    sent_voice_sms_count = __db_fetch_single_value_excption("with t1 as (select id from management_sms_que where organization_id = any('{"+str(org_list).strip('[]')+" }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'audio' union select id from weather_sms_rule_queue where org_id in ("+str(org_list_text).strip('[]')+") and weather_sms_rule_queue.status = 'Sent' and weather_sms_rule_queue.content_type = 'audio' union select  promotional_sms.id from promotional_sms inner join sms_que on sms_que.alertlog_id = promotional_sms.id where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'audio' and organization_id in ("+str(org_list_text).strip('[]')+")) select count(*) over() from t1 limit 1")

    farmer_count = __db_fetch_single_value_excption("select count (*) from farmer where organization_id = any('{"+str(org_list).strip('[]')+" }')")

    program_count = __db_fetch_single_value_excption("select count (*) from usermodule_programs where org_id = any('{"+str(org_list).strip('[]')+" }')")

    crop_count = __db_fetch_single_value_excption("select count(*) over() from farmer, farmer_crop_info where farmer.organization_id = any('{"+str(org_list).strip('[]')+" }') and farmer.id = farmer_crop_info.farmer_id group by farmer_crop_info.crop_id limit 1")

    area_count = __db_fetch_single_value_excption("with t1 as (select case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end processed_land_size,farmer_id from farmer_crop_info inner join farmer on farmer_crop_info.farmer_id = farmer.id and farmer.organization_id = any('{"+str(org_list).strip('[]')+" }') ) select sum (t1.processed_land_size) total_land from t1 where processed_land_size != 'NaN'")
    area_count_hector = float(float(area_count)/247.157686604)
    print area_count_hector
    return render(request, 'ifcmodule/dashboard.html',{
        'farmer_count':farmer_count,
        'program_count':program_count,
        'crop_count':crop_count,
        'sent_sms_count':sent_sms_count,
        'sent_voice_sms_count':sent_voice_sms_count,
        'area_count':area_count_hector
    })


@login_required
def get_program_graph(request):
    categories = []
    farmer_data = []
    acre_data = []
    crop_data = []
    org_list = getOrgList(request)
    org_list_text = []

    for row in org_list:
        org_list_text.append(str(row))

    print org_list

    program_list = __db_fetch_values_dict("select id,program_name from usermodule_programs where org_id = any('{"+str(org_list).strip('[]')+" }')")
    org_list_data = __db_fetch_values_dict("select id,organization from usermodule_organizations where id = any('{"+str(org_list).strip('[]')+" }')")

    # end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.datetime.now().replace(day=1)
    start_date = current_date.strftime("%Y-%m-%d")
    end_date = datetime.datetime(current_date.year, (current_date + relativedelta(months=1)).month,1) - datetime.timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")

    graph_program_id = '%'
    if request.method == 'POST':
        graph_program_id = request.POST.get('graph_prog_id')
        if graph_program_id is None:
            graph_program_id = '%'

        if request.POST.get('start_date') != '':
            if request.POST.get('start_date'):
                start_date = request.POST.get('start_date')
                print start_date

        if request.POST.get('end_date') != '':
            if request.POST.get('end_date'):
                end_date = request.POST.get('end_date')
                print end_date

    total_management_sms = __db_fetch_single_value_excption("select count(*) OVER () from management_sms_que where organization_id = any('{"+str(org_list).strip('[]')+" }') and status = 'Sent' and program_id::text LIKE '"+str(graph_program_id)+"' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id limit 1")
    farmer_data.append(int(total_management_sms))

    print '-------total management sms--------'
    print total_management_sms

    total_promotional_sms = __db_fetch_single_value_excption("select count(*) OVER () from promotional_sms where id in (select alertlog_id from sms_que where sms_que.sms_source = 'promotional_sms' and status = 'Sent' ) and program_id::text LIKE '"+str(graph_program_id)+"' and organization_id in ("+str(org_list_text).strip('[]')+") and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id limit 1 ")
    farmer_data.append(int(total_promotional_sms))

    if request.user.is_superuser:
        total_weather_sms = __db_fetch_single_value_excption("select count(*) OVER () from weather_sms_rule_queue where org_id in ("+str(org_list_text).strip('[]')+") and status = 'Sent' and program_id::text LIKE '"+str(graph_program_id)+"' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id limit 1")

        farmer_data.append(int(total_weather_sms))

    total_acre_management_sms = __db_fetch_single_value_excption("select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size from farmer_crop_info where farmer_id in (select farmer_id from management_sms_que where status = 'Sent' and organization_id = any('{"+str(org_list).strip('[]')+" }') and program_id::text LIKE '"+str(graph_program_id)+"' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id )")
    acre_data.append(float(total_acre_management_sms))

    print '-------total_acre_management_sms---------'
    print total_acre_management_sms

    total_acre_promotional_sms = __db_fetch_single_value_excption("select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size from farmer_crop_info where farmer_id in (select farmer_id::int from promotional_sms where id in (select alertlog_id from sms_que where sms_que.sms_source = 'promotional_sms' and status = 'Sent') and organization_id in ("+str(org_list_text).strip('[]')+") and program_id::text LIKE '"+str(graph_program_id)+"' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id )")
    acre_data.append(float(total_acre_promotional_sms))
    #acre_data.append(float(10))

    if request.user.is_superuser:
        total_acre_weather_sms = __db_fetch_single_value_excption("select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size from farmer_crop_info where farmer_id in (select farmer_id::int from weather_sms_rule_queue where status = 'Sent' and org_id in ("+str(org_list_text).strip('[]')+") and program_id::text LIKE '"+str(graph_program_id)+"' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id )")

        acre_data.append(float(total_acre_weather_sms))

    total_crop_management_sms = __db_fetch_single_value_excption("select count(*) OVER () from management_sms_que where organization_id = any('{"+str(org_list).strip('[]')+" }') and status = 'Sent' and program_id::text LIKE '"+str(graph_program_id)+"' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' limit 1")
    crop_data.append(int(total_crop_management_sms))

    total_crop_promotional_sms = __db_fetch_single_value_excption("select count(*) OVER () from promotional_sms where id in (select alertlog_id from sms_que where sms_que.sms_source = 'promotional_sms' and status = 'Sent' ) and program_id::text LIKE '"+str(graph_program_id)+"' and organization_id in ("+str(org_list_text).strip('[]')+") and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' limit 1 ")
    crop_data.append(int(total_crop_promotional_sms))

    if request.user.is_superuser:
        total_crop_weather_sms = __db_fetch_single_value_excption("select count(*) OVER () from weather_sms_rule_queue where org_id in ("+str(org_list_text).strip('[]')+") and status = 'Sent' and program_id::text LIKE '"+str(graph_program_id)+"' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' limit 1")
        crop_data.append(int(total_crop_weather_sms))

    print farmer_data
    print acre_data
    print crop_data

    if graph_program_id is None or graph_program_id == '%':
        graph_program_id_for_template = 0
    else:
        graph_program_id_for_template = int(graph_program_id)

    if request.user.is_superuser:
        super_user = 1
        categories = ['Management', 'Promotional', 'Weather']
    else:
        super_user = 0
        categories = ['Management', 'Promotional']

    return render(request, 'ifcmodule/dashboard_program_graph.html',{
        'farmer_data': json.dumps(farmer_data),
        'acre_data': json.dumps(acre_data),
        'crop_data': json.dumps(crop_data),
        'program_list':program_list,
        'org_list':org_list_data,
        'graph_program_id': graph_program_id_for_template,
        'start_date':start_date,
        'end_date':end_date,
        'super_user':super_user,
        'categories':categories
    })


@login_required
def get_program_table(request):
    org_list = getOrgList(request)
    program_id = '%'
    if request.method == 'POST':
        program_id = request.POST.get('prog_id')
        if program_id is None:
            program_id = '%'

    print '-----------prog id table---------'
    print program_id

    program_list = __db_fetch_values_dict("select id,program_name from usermodule_programs where org_id = any('{"+str(org_list).strip('[]')+" }')")
    org_list_data = __db_fetch_values_dict("select id,organization from usermodule_organizations where id = any('{"+str(org_list).strip('[]')+" }')")

    properties = {"serial_no": {"align": "center"}, "org_name": {"align": "right"}, "program_name": {"align": "right"},
                  "no_of_farmer": {"align": "right"}, "no_of_crop": {"align": "right"}, "total_arc": {"align": "right"},
                  "management": {"align": "right"}, "promotional": {"align": "right"}, "weather": {"align": "right"}}

    custom_header = [[{"column": "serial_no", "col_span": "1", "row_span": "2", "display_name": "S. No",
                       "background-color": "#ef528c", "color": "#fff", "align": "center"},
                      {"column": "org_name", "col_span": "1", "row_span": "2", "background-color": "#ef528c",
                       "color": "#fff", "display_name": "Organization Name", "align": "center"},
                      {"column": "program_name", "col_span": "1", "row_span": "2", "background-color": "#ef528c",
                       "color": "#fff", "display_name": "Program Name", "align": "center"},
                      {"column": "no_of_farmer", "col_span": "1", "row_span": "2", "background-color": "#ef528c",
                       "color": "#fff", "display_name": "No Of Farmer", "align": "center"},
                      {"column": "no_of_crop", "col_span": "1", "row_span": "2", "background-color": "#ef528c",
                       "color": "#fff", "display_name": "No of Crop", "align": "center"},
                      {"column": "total_arc", "col_span": "1", "row_span": "2", "background-color": "#ef528c",
                       "color": "#fff", "display_name": "Total Arc (Decimal)", "align": "center"},
                      {"column": "Total Advisory Send", "col_span": "3", "row_span": "1", "background-color": "#ef528c",
                       "color": "#fff", "display_name": "Total Advisory Send", "align": "center"}], [
                         {"column": "management", "col_span": "1", "row_span": "1", "align": "left",
                          "background-color": "#ef528c", "color": "#fff", "display_name": "Management"},
                         {"column": "promotional", "col_span": "1", "row_span": "1", "align": "left",
                          "background-color": "#ef528c", "color": "#fff", "display_name": "Promotional"},
                         {"column": "weather", "col_span": "1", "row_span": "1", "align": "right",
                          "background-color": "#ef528c", "color": "#fff", "display_name": "Weather"}]]

    new_html = parser_table(
        "with t as (select id as program_id, program_name, org_id from usermodule_programs where id::text like '" + str(program_id) + "' and org_id = any('{"+str(org_list).strip('[]')+" }') ) select row_number() OVER () AS serial_no, (select organization from usermodule_organizations where usermodule_organizations.id = t.org_id)org_name, t.program_name as program_name, (select count(*) from farmer where program_id = t.program_id) as no_of_farmer, (select COUNT(*) OVER () as ct from farmer_crop_info where farmer_id in ((select id from farmer where program_id = t.program_id )) group by crop_id limit 1) as no_of_crop, (select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) from farmer_crop_info where farmer_id in (select id from farmer where program_id = t.program_id )) as total_arc, (select count(*) from management_sms_que where program_id = t.program_id and status = 'Sent' ) as management, (select count(*) from sms_que where sms_source = 'promotional_sms' and status = 'Sent' and alertlog_id in (select id from promotional_sms where program_id = t.program_id::text)) as promotional, (select count(*) from weather_sms_rule_queue where program_id = t.program_id::text and status = 'Sent' ) as weather from t",
        properties, custom_header)

    if program_id is None or program_id == '%':
        program_id_for_template = 0
    else:
        program_id_for_template = int(program_id)

    if request.user.is_superuser:
        super_user = 1
    else:
        super_user = 0

    return render(request, 'ifcmodule/dashboard_program_table.html', {
        'new_html': new_html,
        'program_list': program_list,
        'org_list': org_list_data,
        'program_id': program_id_for_template,
        'super_user':super_user
    })

@login_required
def get_farmer_map(request):
    org_list = getOrgList(request)
    processed_dist_dict = {}
    range_list = []
    store_range_list = []
    farmer_crop_list = []

    crop = '%'
    sub_query = ''
    # end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.datetime.now().replace(day=1)
    start_date = current_date.strftime("%Y-%m-%d")
    end_date = datetime.datetime(current_date.year, (current_date + relativedelta(months=1)).month,1) - datetime.timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")

    if request.method == 'POST':
        if request.POST.get('start_date') != '' and request.POST.get('end_date') != '':
            if request.POST.get('start_date') and request.POST.get('end_date'):
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')

        crop = request.POST.get('crop')

        if crop != '%':
            crop_result_list = __db_fetch_values_dict("select id from farmer where id in (select distinct farmer_id from farmer_crop_info where crop_id ="+str(crop)+") and organization_id = any('{"+str(org_list).strip('[]')+" }') ")

            print crop_result_list

            for row in crop_result_list:
                farmer_crop_list.append(int(row['id']))

            print '-----farmer crop list ------'
            print farmer_crop_list
            sub_query = "and id = any('{" + str(farmer_crop_list).strip('[]') + " }')"

    sub_query_date = " and created_at::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "'"

    dist_list = __db_fetch_values_dict("select (select name from vwdistrict where id = district_id ) dist_name, count(district_id) as total_no_of_farmer from farmer where organization_id = any('{"+str(org_list).strip('[]')+" }') and country_id = 1 "+sub_query + sub_query_date+"  group by district_id")

    print '----dist list----'
    print dist_list

    if not dist_list:
        processed_dist_dict.update({str("Dhaka"): 0})
        total_no_of_farmer = 0
    else:
        for dist in dist_list:
            processed_dist_dict.update({str(dist['dist_name']): int(dist['total_no_of_farmer'])})
            store_range_list.append(int(dist['total_no_of_farmer']))

        total_no_of_farmer = __db_fetch_single_value("select count(*) from farmer where organization_id = any('{" + str(org_list).strip('[]') + " }') and country_id = 1 " + sub_query + sub_query_date + " ")

    print '------processed_dist_dict---------'
    print processed_dist_dict

    print '------total farmer-------------'
    print total_no_of_farmer

    if total_no_of_farmer < 100:
        range_value = 1000
    else:
        range_value = max(store_range_list)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    p1 = (range_value * 10)/100
    p2 = (range_value * 25)/100
    p3 = (range_value * 50)/100
    p4 = (range_value * 75)/100

    range_list.append(0)
    range_list.append(int(p1))
    range_list.append(int(p1+1))
    range_list.append(int(p2))
    range_list.append(int(p2+1))
    range_list.append(int(p3))
    range_list.append(int(p3+1))
    range_list.append(int(p4))
    range_list.append(int(p4+1))
    range_list.append(int(range_value))

    processed_range_list = json.dumps(range_list)

    b = json.dumps(processed_dist_dict)

    if crop is None or crop == '%':
        crop_id_for_template = 0
    else:
        crop_id_for_template = int(crop)

    return render(request, 'ifcmodule/dashboard_farmer_map.html', {
        'dist_dict':b,
        'processed_range_list':processed_range_list,
        'crop_list': crop_list,
        'total_farmer_no': total_no_of_farmer,
        'crop_id_for_template': crop_id_for_template,
        'end_date':end_date,
        'start_date':start_date
    })

@login_required
def get_farmer_bar(request):
    org_list = getOrgList(request)
    category = []
    drilldown = []
    dist_upazila_dict = {}

    _org = '%'
    _program = '%'
    _crop = '%'
    _variety_crop = '%'
    _season = '%'
    _district_status = '%'
    _district_range = ''

    # end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.datetime.now().replace(day=1)
    start_date = current_date.strftime("%Y-%m-%d")
    end_date = datetime.datetime(current_date.year, (current_date + relativedelta(months=1)).month,1) - datetime.timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")

    sub_query = "DESC"

    if request.method == 'POST':
        _org = request.POST.get('organization')
        _program = request.POST.get('program')
        _crop = request.POST.get('crop')
        _variety_crop = request.POST.get('crop_variety')
        _season = request.POST.get('season')
        _district_status = request.POST.get('dis_status')
        _district_range = request.POST.get('dis_range')

        if request.POST.get('dis_status') != '%' and request.POST.get('dis_range') != '':
            if _district_status == '1':
                sub_query = "DESC limit "+str(_district_range)
            if _district_status == '2':
                sub_query = "ASC limit "+str(_district_range)

        if request.POST.get('dis_status') == '%' and request.POST.get('dis_range') != '':
            sub_query = "DESC limit "+str(_district_range)

        if request.POST.get('dis_status') != '%' and request.POST.get('dis_range') == '':
            if _district_status == '1':
                sub_query = "DESC"
            if _district_status == '2':
                sub_query = "ASC"

        if request.POST.get('from_date') != '':
            if request.POST.get('from_date'):
                start_date = request.POST.get('from_date')
                print start_date

        if request.POST.get('to_date') != '':
            if request.POST.get('to_date'):
                end_date = request.POST.get('to_date')
                print end_date

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    query = "select id,group_name from group_details"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    group_name = df.group_name.tolist()
    group = zip(id, group_name)

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    # drilldown_data_model = {
    #       "Khulna": [['a', 1],['b', 2],['c', 3]],
    #       "Barishal": [['b', 2]],
    #       "Barguna": [['c', 3]]
    #     }

    #upazila_list = __db_fetch_values_dict("with t1 as ( select count(upazila_id) as total_no_of_farmer_upazila,district_id,upazila_id,(select name from vwupazila where id = upazila_id ) upazila_name,(select name from vwdistrict where id = district_id ) dist_name from farmer where organization_id = any('{" + str(org_list).strip('[]') + " }') group by upazila_id,district_id) select * from t1 ")

    upazila_list = __db_fetch_values_dict("with t1 as(select farmer.district_id district_id, farmer.upazila_id upazila_id,farmer.organization_id organization_id, farmer.program_id program_id, farmer.created_at created_at from farmer,farmer_crop_info where farmer.id = farmer_crop_info.farmer_id and farmer_crop_info.crop_id::text like '"+str(_crop)+"' and farmer_crop_info.season_id::text like '"+str(_season)+"' and farmer_crop_info.crop_variety_id::text like '"+str(_variety_crop)+"' and farmer.program_id::text LIKE '" + str(_program) + "' and farmer.created_at::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer.id) select (select name from vwdistrict where id = t1.district_id ) as dist_name, (select name from vwupazila where id = t1.upazila_id ) as upazila_name, count(t1.upazila_id) as total_no_of_farmer_upazila from t1 where t1.organization_id = any('{" + str(org_list).strip('[]') + " }') group by t1.upazila_id, t1.district_id order by total_no_of_farmer_upazila ")

    print upazila_list

    for row in upazila_list:
        dist_upazila_dict.update({str(row['dist_name']) : []})

    for row in upazila_list:
        dist_upazila_dict[str(row['dist_name'])].append([str(row['upazila_name']),int(row['total_no_of_farmer_upazila']) ])

    # dist_list = __db_fetch_values_dict("select (select name from vwdistrict where id = district_id ) dist_name, count(district_id) as total_no_of_farmer from farmer where organization_id = any('{" + str(org_list).strip('[]') + " }') and program_id::text LIKE '"+str(_program)+"' group by district_id order by total_no_of_farmer DESC")

    dist_list = __db_fetch_values_dict("with t1 as(select farmer.district_id district_id, farmer.organization_id organization_id, farmer.program_id program_id, farmer.created_at created_at from farmer,farmer_crop_info where farmer.id = farmer_crop_info.farmer_id and farmer_crop_info.crop_id::text like '"+str(_crop)+"' and farmer_crop_info.season_id::text like '"+str(_season)+"' and farmer_crop_info.crop_variety_id::text like '"+str(_variety_crop)+"' and farmer.program_id::text LIKE '" + str(_program) + "' and farmer.created_at::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer.id) select (select name from vwdistrict where id = t1.district_id ) as dist_name, count(t1.district_id) as total_no_of_farmer from t1 where t1.organization_id = any('{" + str(org_list).strip('[]') + " }') group by t1.district_id order by total_no_of_farmer "+sub_query)

    print dist_list

    for row in dist_list:
        category.append({'name': str(row['dist_name']) , 'y': int(row['total_no_of_farmer']) , 'drilldown':str(row['dist_name'])})
        drilldown.append({'name': str(row['dist_name']) ,'id': str(row['dist_name']), 'data': dist_upazila_dict.get(row['dist_name'],['No data',0])})

    #drilldown data model output
    print drilldown

    if _org is None or _org == '%':
        org_for_template = 0
    else:
        org_for_template = int(_org)

    if _program is None or _program == '%':
        program_for_template = 0
    else:
        program_for_template = int(_program)

    if _crop is None or _crop == '%':
        crop_for_template = 0
    else:
        crop_for_template = int(_crop)

    if _season is None or _season == '%':
        season_for_template = 0
    else:
        season_for_template = int(_season)

    if _variety_crop is None or _variety_crop == '%':
        variety_crop_for_template = 0
    else:
        variety_crop_for_template = int(_variety_crop)

    if _district_status is None or _district_status == '%':
        district_status_for_template = 0
    else:
        district_status_for_template = int(_district_status)


    return render(request, 'ifcmodule/dashboard_farmer_bar.html', {
        'bar_data': category,
        'drilldown_data':drilldown,
        'crop_list': crop_list,
        'season': season,
        'group': group,
        'organization': organization,
        'start_date':start_date,
        'end_date':end_date,
        'org_for_template':org_for_template,
        'program_for_template':program_for_template,
        'crop_for_template':crop_for_template,
        'season_for_template':season_for_template,
        'variety_crop_for_template':variety_crop_for_template,
        'district_status':district_status_for_template,
        'district_range': _district_range
    })

@login_required
def get_farmer_table(request):

    countryQuery = "select id,name from public.geo_country"
    country_List = makeTableList(countryQuery)

    # disQuery = "select id,name from public.geo_district"
    # dist_List = makeTableList(disQuery)

    org_list = getOrgList(request)

    ##  Get Organization  List
    organizationQuery = "select id,organization from public.usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')"
    organization_List = makeTableList(organizationQuery)

    # jsonFarmerInfoList = json.dumps({'farmerInfoList': farmerInfoList}, default=decimal_date_default)
    query = "select distinct geo_country_id,country_name from vwunion"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    country_id = df.geo_country_id.tolist()
    country_name = df.country_name.tolist()
    country = zip(country_id, country_name)

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip(
        '[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    query = "select id,group_name from group_details"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    group_name = df.group_name.tolist()
    group = zip(id, group_name)

    content = {
        'country_List': country_List,
        'organization_List': organization_List,
        'country': country,
        'organization': organization,
        'crop_list': crop_list,
        'season': season,
        'group': group
    }

    return render(request, 'ifcmodule/dashboard_farmer_table.html', content)


def get_farmer_table_activity_history(request):
    org_list = getOrgList(request)
    activity_history = __db_fetch_values_dict("select string_agg(id::text,'_') as ids, updated_at::timestamp::date activity_date, count(id) as t_farmer, count(distinct organization_id) as t_org, count(distinct country_id) as t_country,count(distinct zone_id) as t_zone,count(distinct district_id) as t_district,count(distinct upazila_id) as t_upazila, count(distinct union_id) as t_union , count(distinct union_id) as t_union from farmer where organization_id =  any('{" + str(org_list).strip('[]') + " }') and status = 0 group by activity_date")

    return render(request, 'ifcmodule/dashboard_farmer_table_activity_history.html',{
        'activity_history':activity_history
    })


@login_required
def get_crop(request):
    categories =[]
    farmer_data = []
    acre_data = []
    crop_data = []
    org_list = getOrgList(request)
    org_list_text = []
    for row in org_list:
        org_list_text.append(str(row))

    crop_list = __db_fetch_values_dict("select id,crop_name from crop")
    org_list_data = __db_fetch_values_dict("select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip('[]') + " }')")

    # end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.datetime.now().replace(day=1)
    start_date = current_date.strftime("%Y-%m-%d")
    end_date = datetime.datetime(current_date.year, (current_date + relativedelta(months=1)).month,1) - datetime.timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")

    crop_id = '%'
    if request.method == 'POST':
        crop_id = request.POST.get('crop_id')
        if crop_id is None:
            crop_id = '%'

        if request.POST.get('start_date') != '':
            if request.POST.get('start_date'):
                start_date = request.POST.get('start_date')
                print start_date

        if request.POST.get('end_date') != '':
            if request.POST.get('end_date'):
                end_date = request.POST.get('end_date')
                print end_date

    total_management_sms = __db_fetch_single_value_excption("select count(*) OVER () from management_sms_que where organization_id = any('{" + str(org_list).strip('[]') + " }') and status = 'Sent' and crop_id::text LIKE '" + str(crop_id) + "' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id limit 1")
    farmer_data.append(int(total_management_sms))

    print '-------total management sms--------'
    print total_management_sms

    total_promotional_sms = __db_fetch_single_value_excption("select count(*) OVER () from promotional_sms where id in (select alertlog_id from sms_que where sms_que.sms_source = 'promotional_sms' and status = 'Sent' ) and crop_id::text LIKE '" + str(crop_id) + "' and organization_id in ("+str(org_list_text).strip('[]')+") and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id limit 1 ")
    farmer_data.append(int(total_promotional_sms))

    if request.user.is_superuser:
        total_weather_sms = __db_fetch_single_value_excption("select count(*) OVER () from weather_sms_rule_queue where org_id in ("+str(org_list_text).strip('[]')+") and status = 'Sent' and crop_id::text LIKE '" + str(crop_id) + "' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by farmer_id limit 1")

        farmer_data.append(int(total_weather_sms))

    total_acre_management_sms = __db_fetch_single_value_excption("select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size from farmer_crop_info where farmer_id in (select farmer_id from management_sms_que where status = 'Sent' and organization_id = any('{" + str(
            org_list).strip('[]') + " }') and crop_id::text LIKE '" + str(
            crop_id) + "' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(
            start_date) + "' AND '" + str(end_date) + "' group by farmer_id )")
    acre_data.append(float(total_acre_management_sms))

    print '-------total_acre_management_sms---------'
    print total_acre_management_sms

    # this query slows down
    total_acre_promotional_sms = __db_fetch_single_value_excption("select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size from farmer_crop_info where farmer_id in (select farmer_id::int from promotional_sms where id in (select alertlog_id from sms_que where sms_que.sms_source = 'promotional_sms' and status = 'Sent') and organization_id in ("+str(org_list_text).strip('[]')+") and crop_id::text LIKE '" + str(
            crop_id) + "' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(
            start_date) + "' AND '" + str(end_date) + "' group by farmer_id )")
    acre_data.append(float(total_acre_promotional_sms))
    # acre_data.append(float(10))

    if request.user.is_superuser:
        total_acre_weather_sms = __db_fetch_single_value_excption("select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size from farmer_crop_info where farmer_id in (select farmer_id::int from weather_sms_rule_queue where status = 'Sent' and org_id in ("+str(org_list_text).strip('[]')+") and crop_id::text LIKE '" + str(
            crop_id) + "' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(
            start_date) + "' AND '" + str(end_date) + "' group by farmer_id )")

        acre_data.append(float(total_acre_weather_sms))

    total_crop_management_sms = __db_fetch_single_value_excption("select count(*) OVER () from management_sms_que where organization_id = any('{" + str(org_list).strip('[]') + " }') and status = 'Sent' and crop_id::text LIKE '" + str(crop_id) + "' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "' group by program_id limit 1")
    crop_data.append(int(total_crop_management_sms))

    total_crop_promotional_sms = __db_fetch_single_value_excption(
        "select count(*) OVER () from promotional_sms where id in (select alertlog_id from sms_que where sms_que.sms_source = 'promotional_sms' and status = 'Sent' ) and crop_id::text LIKE '" + str(
            crop_id) + "' and organization_id in ("+str(org_list_text).strip('[]')+") and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(
            end_date) + "' group by program_id limit 1 ")
    crop_data.append(int(total_crop_promotional_sms))

    if request.user.is_superuser:
        total_crop_weather_sms = __db_fetch_single_value_excption(
        "select count(*) OVER () from weather_sms_rule_queue where org_id in ("+str(org_list_text).strip('[]')+") and status = 'Sent' and crop_id::text LIKE '" + str(
            crop_id) + "' and schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(
            start_date) + "' AND '" + str(end_date) + "' group by program_id limit 1")

        crop_data.append(int(total_crop_weather_sms))


    print farmer_data
    print acre_data
    print crop_data

    if crop_id is None or crop_id == '%':
        crop_id_for_template = 0
    else:
        crop_id_for_template = int(crop_id)

    if request.user.is_superuser:
        super_user = 1
        categories = ['Management', 'Promotional', 'Weather']
    else:
        super_user = 0
        categories = ['Management', 'Promotional']

    return render(request, 'ifcmodule/dashboard_crop.html', {
        'farmer_data': json.dumps(farmer_data),
        'acre_data': json.dumps(acre_data),
        'crop_data': json.dumps(crop_data),
        'crop_list': crop_list,
        'org_list': org_list_data,
        'graph_crop_id': crop_id_for_template,
        'start_date': start_date,
        'end_date': end_date,
        'super_user':super_user,
        'categories':categories
    })


@login_required
def get_sms_map(request):
    org_list = getOrgList(request)
    org_list_text = []
    for row in org_list:
        org_list_text.append(str(row))
    processed_dist_dict = {}
    range_list = []
    store_range_list = []
    total_no_of_farmer = 0

    sub_query = ''

    _crop = '%'
    _variety_crop = '%'
    _season = '%'
    _country = '%'
    _division = '%'
    _district = '%'
    _upazilla = '%'
    _advisory_type = '%'
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # current_date = datetime.datetime.now().replace(day=1)
    # start_date = current_date.strftime("%Y-%m-%d")
    # end_date = datetime.datetime(current_date.year, (current_date + relativedelta(months=1)).month,
    #                              1) - datetime.timedelta(days=1)
    # end_date = end_date.strftime("%Y-%m-%d")

    if request.method == 'POST':
        if request.POST.get('start_date') != '' and request.POST.get('end_date') != '':
            if request.POST.get('start_date') and request.POST.get('end_date'):
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')

        _crop = request.POST.get('crop')
        _variety_crop = request.POST.get('crop_variety')
        _season = request.POST.get('season')
        _country = request.POST.get('country_id')
        _division = request.POST.get('division')
        _district = request.POST.get('district')
        _upazilla = request.POST.get('upazilla')
        _advisory_type = request.POST.get('advisory_type')

    sub_query_date = "schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "'"

    #dist_list = []
    print '------processing--------'
    dist_list = __db_fetch_values_dict("with t3 as( with t2 as (with t1 as (select farmer_id, crop_id, variety_id,season_id,stage_id,'weather' as sms_type from weather_sms_rule_queue where org_id = any('{" + str(org_list).strip('[]') + " }') and weather_sms_rule_queue.status = 'Sent' and weather_sms_rule_queue.content_type = 'text' and "+sub_query_date+" union select farmer_id::text,crop_id::text, variety_id::text,season_id::text, stage_id::text,'management' as sms_type from management_sms_que where organization_id = any('{" + str(org_list).strip('[]') + " }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'text' and "+sub_query_date+" union (select promotional_sms.farmer_id,crop_id, variety_id,season_id, '100' as stage_id,'promotional' as sms_type from promotional_sms, sms_que where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'text' and promotional_sms."+sub_query_date+" and organization_id in ("+str(org_list_text).strip('[]')+") and sms_que.alertlog_id = promotional_sms.id )) select farmer_id,crop_id, variety_id,season_id,stage_id,sms_type, (select name from vwdistrict where id = (select district_id from farmer where farmer.id = t1.farmer_id::int)) district_name, (select district_id from farmer where farmer.id = t1.farmer_id::int) district_id, (select zone_id from farmer where farmer.id = t1.farmer_id::int) zone_id,(select country_id from farmer where farmer.id = t1.farmer_id::int) country_id,(select upazila_id from farmer where farmer.id = t1.farmer_id::int) upazila_id from t1 ) select * from t2 where t2.district_id::text LIKE '"+str(_district)+"' and t2.zone_id::text LIKE '"+str(_division)+"' and t2.upazila_id::text LIKE '"+str(_upazilla)+"' and t2.country_id::text LIKE '"+str(_country)+"' and t2.crop_id::text LIKE '"+str(_crop)+"' and t2.variety_id::text LIKE '"+str(_variety_crop)+"' and t2.season_id::text LIKE '"+str(_season)+"' and t2.sms_type::text LIKE '"+str(_advisory_type)+"') select t3.district_name, count(t3.district_name) as total_no_of_farmer from t3 group by t3.district_name")
    print '----dist list----'
    print dist_list

    if not dist_list:
        processed_dist_dict.update({str("Dhaka"): 0})
        total_no_of_farmer = 0
    else:
        for dist in dist_list:
            processed_dist_dict.update({str(dist['district_name']): int(dist['total_no_of_farmer'])})
            store_range_list.append(int(dist['total_no_of_farmer']))
            total_no_of_farmer += int(dist['total_no_of_farmer'])

    print '------processed_dist_dict---------'
    print processed_dist_dict

    print '------total farmer-------------'
    print total_no_of_farmer

    if total_no_of_farmer < 100:
        range_value = 1000
    else:
        range_value = max(store_range_list)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    p1 = (range_value * 10)/100
    p2 = (range_value * 25)/100
    p3 = (range_value * 50)/100
    p4 = (range_value * 75)/100

    range_list.append(0)
    range_list.append(int(p1))
    range_list.append(int(p1+1))
    range_list.append(int(p2))
    range_list.append(int(p2+1))
    range_list.append(int(p3))
    range_list.append(int(p3+1))
    range_list.append(int(p4))
    range_list.append(int(p4+1))
    range_list.append(int(range_value))

    processed_range_list = json.dumps(range_list)

    b = json.dumps(processed_dist_dict)

    if _season is None or _season == '%':
        season_id_for_template = 0
    else:
        season_id_for_template = int(_season)

    if _advisory_type is None or _advisory_type == '%':
        advisory_id_for_template = 0
    else:
        if _advisory_type == 'management':
            advisory_id_for_template = 1
        if _advisory_type == 'promotional':
            advisory_id_for_template = 2
        if _advisory_type == 'weather':
            advisory_id_for_template = 3

    sent_sms_count = __db_fetch_single_value_excption("with t1 as (select id from management_sms_que where organization_id = any('{"+str(org_list).strip('[]')+" }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'text' union select id from weather_sms_rule_queue where org_id in ("+str(org_list_text).strip('[]')+") and weather_sms_rule_queue.status = 'Sent' and weather_sms_rule_queue.content_type = 'text' union select  promotional_sms.id from promotional_sms inner join sms_que on sms_que.alertlog_id = promotional_sms.id where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'text' and organization_id in ("+str(org_list_text).strip('[]')+")) select count(*) over() from t1 limit 1")

    return render(request, 'ifcmodule/dashboard_sms_map.html', {
        'dist_dict':b,
        'processed_range_list':processed_range_list,
        'crop_list': crop_list,
        'total_farmer_no': total_no_of_farmer,
        'end_date':end_date,
        'start_date':start_date,
        'season':season,
        'season_id_for_template':season_id_for_template,
        'advisory_id_for_template':advisory_id_for_template,
        'country':_country,
        'division':_division,
        'district':_district,
        'upazilla':_upazilla,
        'total_sms_sent':sent_sms_count
    })

@login_required
def get_sms_bar(request):
    org_list = getOrgList(request)
    org_list_text = []
    for row in org_list:
        org_list_text.append(str(row))
    category = []
    drilldown = []
    year_month_dict = {}

    sub_query = ''

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    _crop = '%'
    _variety_crop = '%'
    _season = '%'
    _country = '%'
    _division = '%'
    _district = '%'
    _upazilla = '%'
    _advisory_type = '%'
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # current_date = datetime.datetime.now().replace(day=1)
    # start_date = current_date.strftime("%Y-%m-%d")
    # end_date = datetime.datetime(current_date.year, (current_date + relativedelta(months=1)).month,
    #                              1) - datetime.timedelta(days=1)
    # end_date = end_date.strftime("%Y-%m-%d")


    if request.method == 'POST':
        if request.POST.get('start_date') != '' and request.POST.get('end_date') != '':
            if request.POST.get('start_date') and request.POST.get('end_date'):
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')

        _crop = request.POST.get('crop')
        _variety_crop = request.POST.get('crop_variety')
        _season = request.POST.get('season')
        _country = request.POST.get('country_id')
        _division = request.POST.get('division')
        _district = request.POST.get('district')
        _upazilla = request.POST.get('upazilla')
        _advisory_type = request.POST.get('advisory_type')

    sub_query_date = "schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(
        end_date) + "'"

    print _country
    print _division
    print _district


    print '--------------processing---------//'

    month_list = __db_fetch_values_dict("with t3 as( with t2 as (with t1 as (select farmer_id, crop_id, variety_id,season_id,stage_id,'weather' as sms_type, date_part('year',schedule_time)::text as sent_year, to_char(to_timestamp (date_part('month', schedule_time)::text, 'MM'), 'Month') as sent_month from weather_sms_rule_queue where org_id = any('{" + str(org_list).strip('[]') + " }') and weather_sms_rule_queue.status = 'Sent' and farmer_id is not null and weather_sms_rule_queue.content_type = 'text' and " + sub_query_date + " union all select farmer_id::text,crop_id::text, variety_id::text,season_id::text, stage_id::text,'management' as sms_type, date_part('year',schedule_time)::text as sent_year, to_char(to_timestamp (date_part('month', schedule_time)::text, 'MM'), 'Month') as sent_month from management_sms_que where organization_id = any('{" + str(org_list).strip('[]') + " }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'text' and farmer_id is not null and " + sub_query_date + " union all (select promotional_sms.farmer_id,crop_id, variety_id,season_id, '100' as stage_id,'promotional' as sms_type, date_part('year',promotional_sms.schedule_time)::text as sent_year, to_char(to_timestamp (date_part('month', promotional_sms.schedule_time)::text, 'MM'), 'Month') as sent_month from promotional_sms, sms_que where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'text' and farmer_id is not null and promotional_sms." + sub_query_date + " and organization_id in ("+str(org_list_text).strip('[]')+") and sms_que.alertlog_id = promotional_sms.id )) select farmer_id,crop_id, variety_id,season_id,stage_id,sms_type,sent_year,sent_month, (select name from vwdistrict where id = (select district_id from farmer where farmer.id = t1.farmer_id::int)) district_name, (select district_id from farmer where farmer.id = t1.farmer_id::int) district_id, (select zone_id from farmer where farmer.id = t1.farmer_id::int) zone_id,(select country_id from farmer where farmer.id = t1.farmer_id::int) country_id,(select upazila_id from farmer where farmer.id = t1.farmer_id::int) upazila_id from t1 ) select * from t2 where t2.district_id::text LIKE '" + str(_district) + "' and t2.zone_id::text LIKE '" + str(_division) + "' and t2.upazila_id::text LIKE '" + str(_upazilla) + "' and t2.country_id::text LIKE '" + str(_country) + "' and t2.crop_id::text LIKE '" + str(_crop) + "' and t2.variety_id::text LIKE '" + str(_variety_crop) + "' and t2.season_id::text LIKE '" + str(_season) + "' and t2.sms_type::text LIKE '" + str(_advisory_type) + "') select t3.sent_month, t3.sent_year, count(t3.sent_month) as total_no_of_sms_month from t3 group by t3.sent_year,t3.sent_month")

    print month_list

    for row in month_list:
        year_month_dict.update({str(row['sent_year']): []})

    for row in month_list:
        year_month_dict[str(row['sent_year'])].append(
            [str(row['sent_month']), int(row['total_no_of_sms_month'])])

    print year_month_dict

    year_list = __db_fetch_values_dict("with t3 as( with t2 as (with t1 as (select farmer_id, crop_id, variety_id,season_id,stage_id,'weather' as sms_type, date_part('year',schedule_time)::text as sent_year from weather_sms_rule_queue where org_id = any('{" + str(org_list).strip('[]') + " }') and weather_sms_rule_queue.status = 'Sent' and weather_sms_rule_queue.content_type = 'text' and farmer_id is not null and " + sub_query_date + " union all select farmer_id::text,crop_id::text, variety_id::text,season_id::text, stage_id::text,'management' as sms_type, date_part('year',schedule_time)::text as sent_year from management_sms_que where organization_id = any('{" + str(org_list).strip('[]') + " }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'text' and farmer_id is not null and " + sub_query_date + " union all (select promotional_sms.farmer_id,crop_id, variety_id,season_id, '100' as stage_id,'promotional' as sms_type, date_part('year',promotional_sms.schedule_time)::text as sent_year from promotional_sms, sms_que where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'text' and farmer_id is not null and promotional_sms." + sub_query_date + " and organization_id in ("+str(org_list_text).strip('[]')+") and sms_que.alertlog_id = promotional_sms.id )) select farmer_id,crop_id, variety_id,season_id,stage_id,sms_type, sent_year,(select name from vwdistrict where id = (select district_id from farmer where farmer.id = t1.farmer_id::int)) district_name, (select district_id from farmer where farmer.id = t1.farmer_id::int) district_id, (select zone_id from farmer where farmer.id = t1.farmer_id::int) zone_id,(select country_id from farmer where farmer.id = t1.farmer_id::int) country_id,(select upazila_id from farmer where farmer.id = t1.farmer_id::int) upazila_id from t1 ) select * from t2 where t2.district_id::text LIKE '" + str(_district) + "' and t2.zone_id::text LIKE '" + str(_division) + "' and t2.upazila_id::text LIKE '" + str(_upazilla) + "' and t2.country_id::text LIKE '" + str(_country) + "' and t2.crop_id::text LIKE '" + str(_crop) + "' and t2.variety_id::text LIKE '" + str(_variety_crop) + "' and t2.season_id::text LIKE '" + str(_season) + "' and t2.sms_type::text LIKE '" + str(_advisory_type) + "') select t3.sent_year, count(t3.sent_year) as total_no_of_farmer from t3 group by t3.sent_year")

    print year_list

    for row in year_list:
        category.append({'name': str(row['sent_year']) , 'y': int(row['total_no_of_farmer']) , 'drilldown':str(row['sent_year'])})
        drilldown.append({'name': str(row['sent_year']), 'id': str(row['sent_year']),'data': year_month_dict.get(row['sent_year'], ['No data', 0])})

    # drilldown data model output
    print drilldown

    if _season is None or _season == '%':
        season_id_for_template = 0
    else:
        season_id_for_template = int(_season)

    if _advisory_type is None or _advisory_type == '%':
        advisory_id_for_template = 0
    else:
        if _advisory_type == 'management':
            advisory_id_for_template = 1
        if _advisory_type == 'promotional':
            advisory_id_for_template = 2
        if _advisory_type == 'weather':
            advisory_id_for_template = 3

    return render(request, 'ifcmodule/dashboard_sms_bar.html', {
        'bar_data':category,
        'drilldown_data': drilldown,
        'end_date': end_date,
        'start_date': start_date,
        'season': season,
        'season_id_for_template': season_id_for_template,
        'advisory_id_for_template': advisory_id_for_template,
        'country': _country,
        'division': _division,
        'district': _district,
        'upazilla': _upazilla
    })


@login_required
def get_voice_sms_map(request):
    org_list = getOrgList(request)
    org_list_text = []
    for row in org_list:
        org_list_text.append(str(row))
    processed_dist_dict = {}
    range_list = []
    store_range_list = []
    total_no_of_farmer = 0

    sub_query = ''

    _crop = '%'
    _variety_crop = '%'
    _season = '%'
    _country = '%'
    _division = '%'
    _district = '%'
    _upazilla = '%'
    _advisory_type = '%'
    # end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.datetime.now().replace(day=1)
    start_date = current_date.strftime("%Y-%m-%d")
    end_date = datetime.datetime(current_date.year, (current_date + relativedelta(months=1)).month,
                                 1) - datetime.timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")

    if request.method == 'POST':
        if request.POST.get('start_date') != '' and request.POST.get('end_date') != '':
            if request.POST.get('start_date') and request.POST.get('end_date'):
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')

        _crop = request.POST.get('crop')
        _variety_crop = request.POST.get('crop_variety')
        _season = request.POST.get('season')
        _country = request.POST.get('country_id')
        _division = request.POST.get('division')
        _district = request.POST.get('district')
        _upazilla = request.POST.get('upazilla')
        _advisory_type = request.POST.get('advisory_type')

    sub_query_date = "schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(end_date) + "'"

    #dist_list = []
    print '---voice sms process----'
    dist_list = __db_fetch_values_dict("with t3 as( with t2 as (with t1 as (select farmer_id, crop_id, variety_id,season_id,stage_id,'weather' as sms_type from weather_sms_rule_queue where org_id = any('{" + str(org_list).strip('[]') + " }') and weather_sms_rule_queue.status = 'Sent' and weather_sms_rule_queue.content_type = 'audio' and farmer_id is not null and "+sub_query_date+" union select farmer_id::text,crop_id::text, variety_id::text,season_id::text, stage_id::text,'management' as sms_type from management_sms_que where organization_id = any('{" + str(org_list).strip('[]') + " }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'audio' and farmer_id is not null and "+sub_query_date+" union (select promotional_sms.farmer_id,crop_id, variety_id,season_id, '100' as stage_id,'promotional' as sms_type from promotional_sms, sms_que where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'audio' and farmer_id is not null and promotional_sms."+sub_query_date+" and organization_id in ("+str(org_list_text).strip('[]')+") and sms_que.alertlog_id = promotional_sms.id )) select farmer_id,crop_id, variety_id,season_id,stage_id,sms_type, (select name from vwdistrict where id = (select district_id from farmer where farmer.id = t1.farmer_id::int)) district_name, (select district_id from farmer where farmer.id = t1.farmer_id::int) district_id, (select zone_id from farmer where farmer.id = t1.farmer_id::int) zone_id,(select country_id from farmer where farmer.id = t1.farmer_id::int) country_id,(select upazila_id from farmer where farmer.id = t1.farmer_id::int) upazila_id from t1 ) select * from t2 where t2.district_id::text LIKE '"+str(_district)+"' and t2.zone_id::text LIKE '"+str(_division)+"' and t2.upazila_id::text LIKE '"+str(_upazilla)+"' and t2.country_id::text LIKE '"+str(_country)+"' and t2.crop_id::text LIKE '"+str(_crop)+"' and t2.variety_id::text LIKE '"+str(_variety_crop)+"' and t2.season_id::text LIKE '"+str(_season)+"' and t2.sms_type::text LIKE '"+str(_advisory_type)+"') select t3.district_name, count(t3.district_name) as total_no_of_farmer from t3 group by t3.district_name")

    print '----dist list----'
    print dist_list

    if not dist_list:
        processed_dist_dict.update({str("Dhaka"): 0})
        total_no_of_farmer = 0
    else:
        for dist in dist_list:
            processed_dist_dict.update({str(dist['district_name']): int(dist['total_no_of_farmer'])})
            store_range_list.append(int(dist['total_no_of_farmer']))
            total_no_of_farmer += int(dist['total_no_of_farmer'])

    print '------processed_dist_dict---------'
    print processed_dist_dict

    print '------total farmer-------------'
    print total_no_of_farmer

    if total_no_of_farmer < 100:
        range_value = 1000
    else:
        range_value = max(store_range_list)

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    p1 = (range_value * 10)/100
    p2 = (range_value * 25)/100
    p3 = (range_value * 50)/100
    p4 = (range_value * 75)/100

    range_list.append(0)
    range_list.append(int(p1))
    range_list.append(int(p1+1))
    range_list.append(int(p2))
    range_list.append(int(p2+1))
    range_list.append(int(p3))
    range_list.append(int(p3+1))
    range_list.append(int(p4))
    range_list.append(int(p4+1))
    range_list.append(int(range_value))

    processed_range_list = json.dumps(range_list)

    b = json.dumps(processed_dist_dict)

    if _season is None or _season == '%':
        season_id_for_template = 0
    else:
        season_id_for_template = int(_season)

    if _advisory_type is None or _advisory_type == '%':
        advisory_id_for_template = 0
    else:
        if _advisory_type == 'management':
            advisory_id_for_template = 1
        if _advisory_type == 'promotional':
            advisory_id_for_template = 2
        if _advisory_type == 'weather':
            advisory_id_for_template = 3

    return render(request, 'ifcmodule/dashboard_voice_sms_map.html', {
        'dist_dict':b,
        'processed_range_list':processed_range_list,
        'crop_list': crop_list,
        'total_farmer_no': total_no_of_farmer,
        'end_date':end_date,
        'start_date':start_date,
        'season':season,
        'season_id_for_template':season_id_for_template,
        'advisory_id_for_template':advisory_id_for_template,
        'country':_country,
        'division':_division,
        'district':_district,
        'upazilla':_upazilla
    })


@login_required
def get_voice_sms_bar(request):
    org_list = getOrgList(request)
    org_list_text = []
    for row in org_list:
        org_list_text.append(str(row))
    category = []
    drilldown = []
    year_month_dict = {}

    sub_query = ''

    query = "select id,crop_name from crop"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    crop_id = df.id.tolist()
    crop_name = df.crop_name.tolist()
    crop_list = zip(crop_id, crop_name)

    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    _crop = '%'
    _variety_crop = '%'
    _season = '%'
    _country = '%'
    _division = '%'
    _district = '%'
    _upazilla = '%'
    _advisory_type = '%'
    # end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.datetime.now().replace(day=1)
    start_date = current_date.strftime("%Y-%m-%d")
    end_date = datetime.datetime(current_date.year, (current_date + relativedelta(months=1)).month,1) - datetime.timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")


    if request.method == 'POST':
        if request.POST.get('start_date') != '' and request.POST.get('end_date') != '':
            if request.POST.get('start_date') and request.POST.get('end_date'):
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')

        _crop = request.POST.get('crop')
        _variety_crop = request.POST.get('crop_variety')
        _season = request.POST.get('season')
        _country = request.POST.get('country_id')
        _division = request.POST.get('division')
        _district = request.POST.get('district')
        _upazilla = request.POST.get('upazilla')
        _advisory_type = request.POST.get('advisory_type')

    sub_query_date = "schedule_time::timestamp::date BETWEEN SYMMETRIC '" + str(start_date) + "' AND '" + str(
        end_date) + "'"

    print _country
    print _division
    print _district

    print '-----process bar------'

    month_list = __db_fetch_values_dict("with t3 as( with t2 as (with t1 as (select farmer_id, crop_id, variety_id,season_id,stage_id,'weather' as sms_type, date_part('year',schedule_time)::text as sent_year, to_char(to_timestamp (date_part('month', schedule_time)::text, 'MM'), 'Month') as sent_month from weather_sms_rule_queue where org_id = any('{" + str(org_list).strip('[]') + " }') and weather_sms_rule_queue.status = 'Sent' and weather_sms_rule_queue.content_type = 'audio' and farmer_id is not null and " + sub_query_date + " union all select farmer_id::text,crop_id::text, variety_id::text,season_id::text, stage_id::text,'management' as sms_type, date_part('year',schedule_time)::text as sent_year, to_char(to_timestamp (date_part('month', schedule_time)::text, 'MM'), 'Month') as sent_month from management_sms_que where organization_id = any('{" + str(org_list).strip('[]') + " }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'audio' and farmer_id is not null and " + sub_query_date + " union all (select promotional_sms.farmer_id,crop_id, variety_id,season_id, '100' as stage_id,'promotional' as sms_type, date_part('year',promotional_sms.schedule_time)::text as sent_year, to_char(to_timestamp (date_part('month', promotional_sms.schedule_time)::text, 'MM'), 'Month') as sent_month from promotional_sms, sms_que where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'audio' and farmer_id is not null and promotional_sms." + sub_query_date + " and organization_id in ("+str(org_list_text).strip('[]')+") and sms_que.alertlog_id = promotional_sms.id )) select farmer_id,crop_id, variety_id,season_id,stage_id,sms_type,sent_year,sent_month, (select name from vwdistrict where id = (select district_id from farmer where farmer.id = t1.farmer_id::int)) district_name, (select district_id from farmer where farmer.id = t1.farmer_id::int) district_id, (select zone_id from farmer where farmer.id = t1.farmer_id::int) zone_id,(select country_id from farmer where farmer.id = t1.farmer_id::int) country_id,(select upazila_id from farmer where farmer.id = t1.farmer_id::int) upazila_id from t1 ) select * from t2 where t2.district_id::text LIKE '" + str(_district) + "' and t2.zone_id::text LIKE '" + str(_division) + "' and t2.upazila_id::text LIKE '" + str(_upazilla) + "' and t2.country_id::text LIKE '" + str(_country) + "' and t2.crop_id::text LIKE '" + str(_crop) + "' and t2.variety_id::text LIKE '" + str(_variety_crop) + "' and t2.season_id::text LIKE '" + str(_season) + "' and t2.sms_type::text LIKE '" + str(_advisory_type) + "') select t3.sent_month, t3.sent_year, count(t3.sent_month) as total_no_of_sms_month from t3 group by t3.sent_year,t3.sent_month")

    print month_list

    for row in month_list:
        year_month_dict.update({str(row['sent_year']): []})

    for row in month_list:
        year_month_dict[str(row['sent_year'])].append(
            [str(row['sent_month']), int(row['total_no_of_sms_month'])])

    print year_month_dict

    year_list = __db_fetch_values_dict("with t3 as( with t2 as (with t1 as (select farmer_id, crop_id, variety_id,season_id,stage_id,'weather' as sms_type, date_part('year',schedule_time)::text as sent_year from weather_sms_rule_queue where org_id = any('{" + str(org_list).strip('[]') + " }') and weather_sms_rule_queue.status = 'Sent' and weather_sms_rule_queue.content_type = 'audio' and farmer_id is not null and " + sub_query_date + " union all select farmer_id::text,crop_id::text, variety_id::text,season_id::text, stage_id::text,'management' as sms_type, date_part('year',schedule_time)::text as sent_year from management_sms_que where organization_id = any('{" + str(org_list).strip('[]') + " }') and management_sms_que.status = 'Sent' and management_sms_que.content_type = 'audio' and farmer_id is not null and " + sub_query_date + " union all (select promotional_sms.farmer_id,crop_id, variety_id,season_id, '100' as stage_id,'promotional' as sms_type, date_part('year',promotional_sms.schedule_time)::text as sent_year from promotional_sms, sms_que where sms_que.sms_source = 'promotional_sms' and sms_que.status = 'Sent' and  promotional_sms.content_type = 'audio' and farmer_id is not null and promotional_sms." + sub_query_date + " and organization_id in ("+str(org_list_text).strip('[]')+") and sms_que.alertlog_id = promotional_sms.id )) select farmer_id,crop_id, variety_id,season_id,stage_id,sms_type,sent_year, (select name from vwdistrict where id = (select district_id from farmer where farmer.id = t1.farmer_id::int)) district_name, (select district_id from farmer where farmer.id = t1.farmer_id::int) district_id, (select zone_id from farmer where farmer.id = t1.farmer_id::int) zone_id,(select country_id from farmer where farmer.id = t1.farmer_id::int) country_id,(select upazila_id from farmer where farmer.id = t1.farmer_id::int) upazila_id from t1 ) select * from t2 where t2.district_id::text LIKE '" + str(_district) + "' and t2.zone_id::text LIKE '" + str(_division) + "' and t2.upazila_id::text LIKE '" + str(_upazilla) + "' and t2.country_id::text LIKE '" + str(_country) + "' and t2.crop_id::text LIKE '" + str(_crop) + "' and t2.variety_id::text LIKE '" + str(_variety_crop) + "' and t2.season_id::text LIKE '" + str(_season) + "' and t2.sms_type::text LIKE '" + str(_advisory_type) + "') select t3.sent_year, count(t3.sent_year) as total_no_of_farmer from t3 group by t3.sent_year")

    print year_list

    for row in year_list:
        category.append({'name': str(row['sent_year']) , 'y': int(row['total_no_of_farmer']) , 'drilldown':str(row['sent_year'])})
        drilldown.append({'name': str(row['sent_year']), 'id': str(row['sent_year']),'data': year_month_dict.get(row['sent_year'], ['No data', 0])})

    # drilldown data model output
    print drilldown

    if _season is None or _season == '%':
        season_id_for_template = 0
    else:
        season_id_for_template = int(_season)

    if _advisory_type is None or _advisory_type == '%':
        advisory_id_for_template = 0
    else:
        if _advisory_type == 'management':
            advisory_id_for_template = 1
        if _advisory_type == 'promotional':
            advisory_id_for_template = 2
        if _advisory_type == 'weather':
            advisory_id_for_template = 3

    return render(request, 'ifcmodule/dashboard_voice_sms_bar.html', {
        'bar_data':category,
        'drilldown_data': drilldown,
        'end_date': end_date,
        'start_date': start_date,
        'season': season,
        'season_id_for_template': season_id_for_template,
        'advisory_id_for_template': advisory_id_for_template,
        'country': _country,
        'division': _division,
        'district': _district,
        'upazilla': _upazilla
    })

@login_required
def get_area(request):
    org_list = getOrgList(request)
    org_list_text = []
    for row in org_list:
        org_list_text.append(str(row))
    processed_dist_dict = {}
    range_list = []
    dist_list = []
    store_range_list = []
    total_no_of_farmer = 0

    if request.POST.get('filter_id') == '1':
        dist_list = __db_fetch_values_dict("with t1 as (select case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end processed_land_size, farmer.district_id, farmer_id from farmer_crop_info inner join farmer on farmer_crop_info.farmer_id = farmer.id and farmer.organization_id = any('{"+str(org_list).strip('[]')+" }')) select sum (t1.processed_land_size) total_land,(select name from vwdistrict where id = t1.district_id) district_name from t1 group by t1.district_id")
    if request.POST.get('filter_id') == '2':
        dist_list = __db_fetch_values_dict("with t1 as (select case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end processed_land_size, farmer.district_id, crop_id from farmer_crop_info inner join farmer on farmer_crop_info.farmer_id = farmer.id and farmer.organization_id = any('{"+str(org_list).strip('[]')+" }')) select sum (t1.processed_land_size) total_land,(select name from vwdistrict where id = t1.district_id) district_name from t1 group by t1.district_id")
    if request.POST.get('filter_id') == '3':
        dist_list = __db_fetch_values_dict("with t1 as (select case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end processed_land_size, farmer.district_id, farmer.program_id from farmer_crop_info inner join farmer on farmer_crop_info.farmer_id = farmer.id and farmer.organization_id = any('{"+str(org_list).strip('[]')+" }')) select sum (t1.processed_land_size) total_land,(select name from vwdistrict where id = t1.district_id) district_name from t1 group by t1.district_id")
    if request.POST.get('filter_id') == '4':
        dist_list = __db_fetch_values_dict("with n as ((with t2 as (with t1 as (select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size,farmer_id,district_id from farmer_crop_info group by farmer_id,district_id) select * from t1 where farmer_id in (select farmer_id::int from weather_sms_rule_queue where status = 'Sent' and org_id in ("+str(org_list_text).strip('[]')+") and content_type = 'text' group by farmer_id )) select sum(processed_land_size) land_size, (select name from vwdistrict where id = t2.district_id) district_name from t2 group by t2.district_id)union all (with t4 as (with t3 as (select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size,farmer_id,district_id from farmer_crop_info group by farmer_id,district_id) select * from t3 where farmer_id in (select farmer_id::int from management_sms_que where status = 'Sent' and organization_id = any('{"+str(org_list).strip('[]')+" }') and content_type = 'text' group by farmer_id )) select sum(processed_land_size) land_size, (select name from vwdistrict where id = t4.district_id) district_name from t4 group by t4.district_id) union all (with t6 as (with t5 as (select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size, farmer_id, district_id from farmer_crop_info where farmer_id in (select farmer_id::int from promotional_sms where id in (select alertlog_id from sms_que where sms_que.sms_source = 'promotional_sms' and status = 'Sent') and content_type = 'text') group by farmer_id,district_id) select * from t5 where farmer_id in (select farmer_id::int from management_sms_que where status = 'Sent' and organization_id = any('{"+str(org_list).strip('[]')+" }') and content_type = 'text' group by farmer_id )) select sum(processed_land_size) land_size, (select name from vwdistrict where id = t6.district_id) district_name from t6 group by t6.district_id)) select sum(land_size) as total_land, district_name from n group by district_name")
    if request.POST.get('filter_id') == '5':
        dist_list = __db_fetch_values_dict("with n as ((with t2 as (with t1 as (select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size,farmer_id,district_id from farmer_crop_info group by farmer_id,district_id) select * from t1 where farmer_id in (select farmer_id::int from weather_sms_rule_queue where status = 'Sent' and org_id in ("+str(org_list_text).strip('[]')+") and content_type = 'audio' group by farmer_id )) select sum(processed_land_size) land_size, (select name from vwdistrict where id = t2.district_id) district_name from t2 group by t2.district_id)union all (with t4 as (with t3 as (select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size,farmer_id,district_id from farmer_crop_info group by farmer_id,district_id) select * from t3 where farmer_id in (select farmer_id::int from management_sms_que where status = 'Sent' and organization_id = any('{"+str(org_list).strip('[]')+" }') and content_type = 'audio' group by farmer_id )) select sum(processed_land_size) land_size, (select name from vwdistrict where id = t4.district_id) district_name from t4 group by t4.district_id) union all (with t6 as (with t5 as (select sum(case when unit_id = 4 then (land_size::decimal) when unit_id = 3 then (land_size::decimal * 33.058) when unit_id = 2 then (land_size::decimal * 100) when unit_id = 1 then (land_size::decimal * 247.105) end) processed_land_size, farmer_id, district_id from farmer_crop_info where farmer_id in (select farmer_id::int from promotional_sms where id in (select alertlog_id from sms_que where sms_que.sms_source = 'promotional_sms' and status = 'Sent') and content_type = 'audio') group by farmer_id,district_id) select * from t5 where farmer_id in (select farmer_id::int from management_sms_que where status = 'Sent' and organization_id = any('{"+str(org_list).strip('[]')+" }') and content_type = 'text' group by farmer_id )) select sum(processed_land_size) land_size, (select name from vwdistrict where id = t6.district_id) district_name from t6 group by t6.district_id)) select sum(land_size) as total_land, district_name from n group by district_name")

    if not dist_list:
        processed_dist_dict.update({str("Dhaka"): 0})
        total_no_of_farmer = 0
    else:
        for dist in dist_list:
            processed_dist_dict.update({str(dist['district_name']): int(dist['total_land'])})
            store_range_list.append(int(dist['total_land']))
            total_no_of_farmer += int(dist['total_land'])

    print '------processed_dist_dict---------'
    print processed_dist_dict

    print '------total farmer-------------'
    print total_no_of_farmer

    if total_no_of_farmer < 100:
        range_value = 1000
    else:
        range_value = max(store_range_list)

    p1 = (range_value * 10)/100
    p2 = (range_value * 25)/100
    p3 = (range_value * 50)/100
    p4 = (range_value * 75)/100

    range_list.append(0)
    range_list.append(int(p1))
    range_list.append(int(p1+1))
    range_list.append(int(p2))
    range_list.append(int(p2+1))
    range_list.append(int(p3))
    range_list.append(int(p3+1))
    range_list.append(int(p4))
    range_list.append(int(p4+1))
    range_list.append(int(range_value))

    processed_range_list = json.dumps(range_list)

    b = json.dumps(processed_dist_dict)

    return render(request, 'ifcmodule/dashboard_area.html', {
        'dist_dict': b,
        'processed_range_list': processed_range_list,
        'total_farmer_no': total_no_of_farmer,
    })


@login_required
def content_library(request):
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

    crop_id = '%'
    variety_id = '%'
    season_id = '%'

    if request.POST:
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')

    content_list = __db_fetch_values_dict("with t1 as (select *,(select crop_name from crop where id::text = crop limit 1) crop_name, (select variety_name from crop_variety where id::text = crop_variety limit 1) variety_name, (select season_name from cropping_season where id::text = season limit 1) season_name from content where crop LIKE '"+str(crop_id)+"' and season LIKE '"+str(season_id)+"' and crop_variety LIKE '"+str(variety_id)+"' ) select *,case when content_type = 'audio' then voice_sms_file_path else sms_description end info from t1")

    if season_id is None or season_id == '%':
        season_id_for_template = 0
    else:
        season_id_for_template = int(season_id)

    if crop_id is None or crop_id == '%':
        crop_id_for_template = 0
    else:
        crop_id_for_template = int(crop_id)

    return render(request, 'ifcmodule/content_library.html', {
        'crop': crop,
        'season': season,
        'content_list':content_list,
        'season_id_for_template':season_id_for_template,
        'crop_id_for_template':crop_id_for_template
    })


@login_required
def create_content(request):
    org_list = getOrgList(request)

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip(
        '[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

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

    return render(request, 'ifcmodule/content_create.html', {
        'crop': crop,
        'season': season,
        'organization': organization,
    })


@login_required
def edit_content_library(request,id):
    org_list = getOrgList(request)

    query = "select id,organization from usermodule_organizations where id = any('{" + str(org_list).strip(
        '[]') + " }')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id, org_name)

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

    data = __db_fetch_values_dict("select * from content where id = "+str(id))
    season_id = data[0]['season']
    crop_id = data[0]['crop']
    crop_variety_id = data[0]['crop_variety']
    sms_type = data[0]['content_type']
    sms = data[0]['sms_description']
    org_id = data[0]['org_id']

    print season_id
    print crop_id

    if crop_variety_id is None or crop_variety_id == '%':
        crop_variety_id_for_template = 0
    else:
        crop_variety_id_for_template = int(crop_variety_id)

    return render(request, 'ifcmodule/content_edit.html', {
        'crop': crop,
        'season': season,
        'organization': organization,
        'crop_id':int(crop_id),
        'season_id':int(season_id),
        'crop_variety_id':crop_variety_id_for_template,
        'sms_type':sms_type,
        'sms':sms,
        'org_id_':int (org_id),
        'id':id

    })


def insert_content_form(request):
    if request.POST:
        sms_description = request.POST.get('sms_description')
        sms_description = sms_description.encode('utf-8').strip()
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')
        sms_type = request.POST.get('sms_type')
        input_type = request.POST.get('input_type')
        org_id = request.POST.get('organization')

        voice_sms_file_path = ""
        if "voice_sms" in request.FILES:
            myfile = request.FILES['voice_sms']
            url = "onadata/media/uploaded_files/"
            userName = request.user
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            voice_sms_file_path = "onadata/media/uploaded_files/" + myfile.name
            sms_type = "audio"

        insert_query = "INSERT INTO public.content ( season,crop,crop_variety,sms_description,input_type, content_type, voice_sms_file_path ,org_id) VALUES('" + str(season_id) + "', '" + str(crop_id) + "', '" + str(variety_id) + "', '" + str(sms_description) + "', '" +str(input_type) +"', '" +str(sms_type)+ "', '"+ str(voice_sms_file_path) +"', '"+str(org_id) + "')"

        __db_commit_query(insert_query)

    messages.success(request, '<i class="fa fa-check-circle"></i>New Content has been added successfully!', extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/content_library/")


def update_content_form(request,id):
    if request.POST:
        sms_description = request.POST.get('sms_description')
        sms_description = sms_description.encode('utf-8').strip()
        crop_id = request.POST.get('crop')
        variety_id = request.POST.get('crop_variety')
        season_id = request.POST.get('season')
        sms_type = request.POST.get('sms_type')
        input_type = request.POST.get('input_type')
        org_id = request.POST.get('organization')

        voice_sms_file_path = ""
        if "voice_sms" in request.FILES:
            myfile = request.FILES['voice_sms']
            url = "onadata/media/uploaded_files/"
            userName = request.user
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            voice_sms_file_path = "onadata/media/uploaded_files/" + myfile.name
            sms_type = "audio"

        query = "update content set season = '" + str(season_id) + "' , crop = '" + str(crop_id) + "' ,crop_variety = '" + str(variety_id) + "' ,sms_description = '" + str(sms_description) +  "' ,input_type = '" + str(input_type) + "' ,content_type = '" + str(sms_type) + "' ,voice_sms_file_path = '" + str(voice_sms_file_path) + "' ,org_id = '" + str(org_id) + "'  where id = "+str(id)

        __db_commit_query(query)

    messages.success(request, '<i class="fa fa-check-circle"></i>Content has been edited successfully!', extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/ifcmodule/content_library/")



@login_required
def weather_observed_info(request):

    return render(request, 'ifcmodule/weather_observed_info.html', {

    })


@login_required
def weather_forecast_info(request):
    query = "select distinct place_name from weather_forecast"
    df = pandas.read_sql(query, connection)
    place_name = df.place_name.tolist()

    return render(request, 'ifcmodule/weather_forecast_info.html', {
        'place_name':place_name
    })


def parser_table(query, properties, custom_header):
    head = """"""

    for c in custom_header:
        temp_row = """<tr>"""
        for i in c:
            # print i
            if i.has_key('display_name'):
                colname = i['display_name']
            else:
                colname = i['column']

            style = ''
            if 'align' in i:
                style += 'text-align:' + i['align'] + ';'
            if 'background-color' in i:
                style += 'background-color:' + i['background-color'] + ';'
            if 'color' in i:
                style += 'color:' + i['color'] + ';'
            temp_col = '<th style = "' + style + '" rowspan="' + i['row_span'] + '" colspan="' + i[
                'col_span'] + '" >' + colname + '</th>'
            temp_row += temp_col
        temp_row += '</tr>'
        head += temp_row

    data = __db_fetch_values_dict(query)

    parser = AdvancedHTMLParser.AdvancedHTMLParser()

    all_row = """"""

    for d in data:
        # print d
        row_data = """<tr>"""
        for k, v in d.items():
            style = ''
            prefix = ''
            suffix = ''
            class_data = ''
            # print k
            if k in properties:
                prop = properties[k]
            else:
                prop = {}
            # print prop
            class_data = ''
            if 'align' in prop:
                style += 'text-align:' + prop['align'] + ';'
            if 'background-color' in prop:
                class_data += ' '
            if 'prefix' in prop:
                prefix = prop['prefix']
                # print prop['prefix']
            if 'suffix' in prop:
                suffix = prop['suffix']
            row_data += '<td style = "' + style + '">' + prefix + str(check_null(v)).encode('utf-8') + suffix + '</td>'

        row_data += """</tr>"""
        all_row += row_data

    main_string = """
            <div id="parent_body" class="portlet-body">
                <table id="main_table" class="custom-table table table-hover table-bordered" CELLSPACING="4" CELLPADDING="4" BORDER="1 solid black">{header_string}{all_row}</table>
            </div>
            """.format(header_string=head, all_row=all_row)
    parser.parseStr(main_string)
    # print parser.getHTML()
    return parser.getHTML()

def check_null(data):
    if data is None:
        return ''
    else:
        return data
