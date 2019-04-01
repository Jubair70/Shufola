import simplejson
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404, render
from django.forms.formsets import formset_factory
from django.db.models import ProtectedError
from django.db import connection
from onadata.apps.maxmodule.models import *
from onadata.apps.bgmodule import views
import json
from django.forms.models import inlineformset_factory
from collections import OrderedDict
import pandas as pd
from onadata.apps.logger.models import XForm, Attachment
from django.contrib.auth.models import User
import decimal
from django.contrib.auth.models import User
from onadata.libs.utils.user_auth import has_permission, get_xform_and_perms, \
    helper_auth_helper, has_edit_permission
import os
from onadata.apps.usermodule.views_project import custom_project_window
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import pandas
import datetime


##  General Few Function for Work *** (Start)***********




def __db_commit_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def singleValuedQuryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchone()
    cursor.close()
    return value


def multipleValuedQuryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchall()
    cursor.close()
    return value

def __db_fetch_values_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = dictfetchall(cursor)
    cursor.close()
    return fetchVal

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


##  General Few Function for Work *** (End)***********


"""
@@ Add Geo Location (Start)
"""

##************ Zone (Start) ***********

@login_required
def add_geo_zone(request):
    queryCountryList = 'SELECT id, name , code  FROM public.geo_country order by id asc '
    countryList = multipleValuedQuryExecution(queryCountryList)

    queryZoneInfoList = 'SELECT id , country_name, name  , code FROM public.vwdivision order by id asc'
    zoneInfoList = multipleValuedQuryExecution(queryZoneInfoList)

    jsonZoneInfoList = json.dumps({'zoneInfoList': zoneInfoList}, default=decimal_date_default)
    content = {
        'countryList': countryList,
        'jsonZoneInfoList': jsonZoneInfoList
    }


    return render(request, 'cais_module/add_geolocation/add_geo_zone.html', content)

@login_required
def geo_zone_Create(request):
    username = request.user.username
    country_id = request.POST.get('country_id', '')
    zone_name = request.POST.get('zone_name', '')
    zone_code = request.POST.get('zone_code', '')
    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        queryEditZone = "UPDATE public.geo_zone SET geo_country_id = " + str(country_id) + ", name='" + str(zone_name) + "' , code = '"+str(zone_code)+"'  WHERE id= " + str(isEdit)
        __db_commit_query(queryEditZone)  ## Query Execution Function
    else:
        queryCreateZone = "INSERT INTO public.geo_zone(geo_country_id, name,code) VALUES( " + str(
            country_id) + ", '" + str(zone_name) + "' , '"+str(zone_code)+"') "
        __db_commit_query(queryCreateZone)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/add_geolocation/add_geo_zone/')


@login_required
def geo_zone_Edit(request):
    id = request.POST.get('id')
    queryFetchSelectedZone = "SELECT id, geo_country_id, name , code  FROM public.vwdivision where id = " + str(id)
    getFetchSelectedZone = singleValuedQuryExecution(queryFetchSelectedZone)

    jsonFetchSelectedZone = json.dumps({'getFetchSelectedZone': getFetchSelectedZone},
                                             default=decimal_date_default)
    return HttpResponse(jsonFetchSelectedZone)

##************ Zone (End) **************



##************ District (Start) ***********

@login_required
def add_geo_district(request):
    queryCountryList = 'SELECT id, name , code  FROM public.geo_country order by id asc '
    countryList = makeTableList(queryCountryList)

    queryZoneList = 'SELECT id, name , code  FROM public.geo_zone order by id asc '
    zoneList = makeTableList(queryZoneList)

    queryDistrictInfoList = 'SELECT id , country_name, division_name , name  , code FROM public.vwdistrict order by id asc'
    districtInfoList = makeTableList(queryDistrictInfoList)

    jsonDistrictInfoList = json.dumps({'districtInfoList': districtInfoList}, default=decimal_date_default)
    content = {
        'countryList': countryList,
        'zoneList': zoneList ,
        'jsonDistrictInfoList': jsonDistrictInfoList
    }


    return render(request, 'cais_module/add_geolocation/add_geo_district.html', content)

@login_required
def geo_district_Create(request):
    username = request.user.username
    zone_id = request.POST.get('zone_id', '')
    district_name = request.POST.get('district_name', '')
    district_code = request.POST.get('district_code', '')
    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        queryEditDistrict = "UPDATE public.geo_district SET geo_zone_id = " + str(zone_id) + ", name='" + str(district_name) + "' , code = '"+str(district_code)+"'  WHERE id= " + str(isEdit)
        __db_commit_query(queryEditDistrict)  ## Query Execution Function
    else:
        queryCreateDistrict = "INSERT INTO public.geo_district(geo_zone_id, name,code) VALUES( " + str(
            zone_id) + ", '" + str(district_name) + "' , '"+str(district_code)+"') "
        __db_commit_query(queryCreateDistrict)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/add_geolocation/add_geo_district/')


@login_required
def geo_district_Edit(request):
    id = request.POST.get('id')
    queryFetchSelectedDistrict = "SELECT id, geo_country_id, geo_zone_id ,  name , code  FROM public.vwdistrict where id = " + str(id)
    getFetchSelectedDistrict = singleValuedQuryExecution(queryFetchSelectedDistrict)

    zoneQuery = "select id,name from geo_zone where geo_country_id =" + str(getFetchSelectedDistrict[1])
    zone_List = makeTableList(zoneQuery)


    jsonFetchSelectedDistrict = json.dumps({'getFetchSelectedDistrict': getFetchSelectedDistrict, 'zone_List':zone_List},
                                             default=decimal_date_default)
    return HttpResponse(jsonFetchSelectedDistrict)

##************ District (End) **************



##************ Upazila (Start) ***********

@login_required
def add_geo_upazila(request):
    queryCountryList = 'SELECT id, name , code  FROM public.geo_country order by id asc '
    countryList = multipleValuedQuryExecution(queryCountryList)

    queryUpazilaInfoList = 'SELECT id , country_name, division_name , district_name , name  , code FROM public.vwupazila order by id asc'
    upazilaInfoList = multipleValuedQuryExecution(queryUpazilaInfoList)

    jsonUpazilaInfoList = json.dumps({'upazilaInfoList': upazilaInfoList}, default=decimal_date_default)
    content = {
        'countryList': countryList,
        'jsonUpazilaInfoList': jsonUpazilaInfoList
    }


    return render(request, 'cais_module/add_geolocation/add_geo_upazila.html', content)

@login_required
def geo_upazila_Create(request):
    username = request.user.username
    district_id = request.POST.get('district_id', '')
    upazila_name = request.POST.get('upazila_name', '')
    upazila_code = request.POST.get('upazila_code', '')
    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        queryEditUpazila = " UPDATE public.geo_upazilla SET geo_district_id = " + str(district_id) + ", name='" + str(upazila_name) + "' , code = '"+str(upazila_code)+"'  WHERE id= " + str(isEdit)
        __db_commit_query(queryEditUpazila)  ## Query Execution Function
    else:
        queryCreateUpazila = "INSERT INTO public.geo_upazilla(geo_district_id, name,code) VALUES( " + str(
            district_id) + ", '" + str(upazila_name) + "' , '"+str(upazila_code)+"') "
        __db_commit_query(queryCreateUpazila)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/add_geolocation/add_geo_upazila/')


@login_required
def geo_upazila_Edit(request):
    id = request.POST.get('id')
    queryFetchSelectedUpazila = "SELECT id, geo_country_id, geo_zone_id , geo_district_id ,  name , code  FROM public.vwupazila where id = " + str(id)
    getFetchSelectedUpazila = singleValuedQuryExecution(queryFetchSelectedUpazila)

    zoneQuery = "select id,name from geo_zone where geo_country_id =" + str(getFetchSelectedUpazila[1])
    zone_List = makeTableList(zoneQuery)

    districtQuery = "select id,name from geo_district where geo_zone_id =" + str(getFetchSelectedUpazila[2])
    district_List = makeTableList(districtQuery)

    jsonFetchSelectedUpazila = json.dumps({'getFetchSelectedUpazila': getFetchSelectedUpazila, 'zone_List':zone_List , 'district_List': district_List },
                                             default=decimal_date_default)
    return HttpResponse(jsonFetchSelectedUpazila)

##************ Upazila (End) **************



##************ Union (Start) ***********

@login_required
def add_geo_union(request):
    queryCountryList = 'SELECT id, name , code  FROM public.geo_country order by id asc '
    countryList = multipleValuedQuryExecution(queryCountryList)

    queryUnionInfoList = 'SELECT id , country_name, division_name , district_name , upazilla_name ,  name  , code FROM public.vwunion order by id asc'
    unionInfoList = multipleValuedQuryExecution(queryUnionInfoList)

    jsonUnionInfoList = json.dumps({'unionInfoList': unionInfoList}, default=decimal_date_default)
    content = {
        'countryList': countryList,
        'jsonUnionInfoList': jsonUnionInfoList
    }


    return render(request, 'cais_module/add_geolocation/add_geo_union.html', content)

@login_required
def geo_union_Create(request):
    username = request.user.username
    upazila_id = request.POST.get('upazila_id', '')
    union_name = request.POST.get('union_name', '')
    union_code = request.POST.get('union_code', '')
    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        queryEditUnion = "UPDATE public.geo_union SET geo_upazilla_id = " + str(upazila_id) + ", name='" + str(union_name) + "' , code = '"+str(union_code)+"'  WHERE id= " + str(isEdit)
        __db_commit_query(queryEditUnion)  ## Query Execution Function
    else:
        queryCreateUnion = "INSERT INTO public.geo_union(geo_upazilla_id, name,code) VALUES( " + str(
            upazila_id) + ", '" + str(union_name) + "' , '"+str(union_code)+"') "
        __db_commit_query(queryCreateUnion)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/add_geolocation/add_geo_union/')


@login_required
def geo_union_Edit(request):
    id = request.POST.get('id')
    queryFetchSelectedUnion = "SELECT id, geo_country_id, geo_zone_id , geo_district_id , geo_upazilla_id ,  name , code  FROM public.vwunion where id = " + str(id)
    getFetchSelectedUnion = singleValuedQuryExecution(queryFetchSelectedUnion)

    zoneQuery = "select id,name from geo_zone where geo_country_id =" + str(getFetchSelectedUnion[1])
    zone_List = makeTableList(zoneQuery)

    districtQuery = "select id,name from geo_district where geo_zone_id =" + str(getFetchSelectedUnion[2])
    district_List = makeTableList(districtQuery)

    upazilaQuery = "select id,name from geo_upazilla where geo_district_id =" + str(getFetchSelectedUnion[3])
    upazila_List = makeTableList(upazilaQuery)

    jsonFetchSelectedUnion = json.dumps({'getFetchSelectedUnion': getFetchSelectedUnion,
                                            'zone_List':zone_List ,
                                            'district_List': district_List ,
                                            'upazila_List':upazila_List},
                                             default=decimal_date_default)
    return HttpResponse(jsonFetchSelectedUnion)

##************ Union (End) **************



"""
@@ Add Geo Location (End)
"""




"""
@@ **************  Crop (Start)
"""


@login_required
def crop(request):
    queryCropNameList = 'SELECT id, crop_name FROM public.crop order by id'
    cropNameList = multipleValuedQuryExecution(queryCropNameList)
    jsonCropNameList = json.dumps({'cropNameList': cropNameList}, default=decimal_date_default)

    content = {

        'jsonCropNameList': jsonCropNameList
    }

    return render(request, 'cais_module/crop.html', content)


@login_required
def cropCreate(request):
    username = request.user.username
    cropName = request.POST.get('crop_name', '')
    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        queryEditCropName = "UPDATE public.crop SET crop_name='" + cropName + "' WHERE id= " + isEdit
        __db_commit_query(queryEditCropName)  ## Query Execution Function
    else:
        queryCreateCropName = "INSERT INTO public.crop (id, crop_name, created_at, created_by, updated_at, updated_by)VALUES(nextval('crop_id_seq'::regclass),'" + str(
            cropName) + "', now(), '" + str(username) + "', now(), '" + str(username) + "')"
        __db_commit_query(queryCreateCropName)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/crop/')


@login_required
def crop_Edit(request):
    id = request.POST.get('id')
    queryFetchSpecificCrop = " SELECT id,crop_name FROM public.crop where id = " + str(id)
    getFetchSpecificCrop = singleValuedQuryExecution(queryFetchSpecificCrop)

    jsonFetchSpecificCrop = json.dumps({'getFetchSpecificCrop': getFetchSpecificCrop}, default=decimal_date_default)

    return HttpResponse(jsonFetchSpecificCrop)


"""
@@ **************  Crop (End)
"""

"""
@@ **************  Crop Stage (Start) ***********@@
"""


@login_required
def crop_Stage(request):
    query = "select id,season_name from cropping_season"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    season_id = df.id.tolist()
    season_name = df.season_name.tolist()
    season = zip(season_id, season_name)

    queryCropNameList = 'SELECT id, crop_name FROM public.crop order by id'
    cropNameList = multipleValuedQuryExecution(queryCropNameList)

    queryCropStageInfoList = "SELECT id, (select crop_name from public.crop where id = crop_id )crop_name, stage_name,case when crop_variety_id::int = 0 then 'ALL' else (select variety_name from crop_variety where id = crop_variety_id::int) end variety_name,case when season_id::int = 0 then 'ALL' else (select season_name from cropping_season where id = season_id::int) end season, start_day, end_day FROM public.crop_stage order by id"
    cropStageInfoList = multipleValuedQuryExecution(queryCropStageInfoList)

    jsonCropStageInfoList = json.dumps({'cropStageInfoList': cropStageInfoList}, default=decimal_date_default)
    content = {
        'cropNameList': cropNameList,
        'jsonCropStageInfoList': jsonCropStageInfoList,
        'season': season
    }
    return render(request, 'cais_module/crop_Stage.html', content)


@login_required
def cropStageCreate(request):
    username = request.user.username
    crop_id = request.POST.get('crop_id', '')
    stage_name = request.POST.get('stage_name', '')
    start_day = request.POST.get('start_day', '')
    end_day = request.POST.get('end_day', '')
    season = request.POST.get('season', '')
    crop_variety = request.POST.get('crop_variety', '')
    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        queryEditCropStage = "UPDATE public.crop_stage SET crop_id= " + str(crop_id) + ", stage_name='" + str(
            stage_name) + "', start_day= " + str(start_day) + ", end_day= " + str(end_day) + "  WHERE id= " + str(
            isEdit)
        __db_commit_query(queryEditCropStage)  ## Query Execution Function
    else:
        queryCreateCropStage = "INSERT INTO public.crop_stage (id, crop_id, stage_name, start_day, end_day, created_at, created_by, updated_at, updated_by,crop_variety_id,season_id) VALUES(nextval('crop_stage_id_seq'::regclass), " + str(
            crop_id) + ", '" + str(stage_name) + "', " + str(start_day) + ", " + str(end_day) + ", now(), '" + str(
            username) + "', now(), '" + str(username) + "', '" + str(crop_variety) + "', '" + str(season) + "'); "
        __db_commit_query(queryCreateCropStage)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/crop_Stage/')


@login_required
def crop_Stage_Edit(request):
    id = request.POST.get('id')

    queryFetchSelecteCropStage = "SELECT id, crop_id, stage_name, start_day, end_day,season_id,crop_variety_id  FROM public.crop_stage where id = " + str(
        id)
    getFetchSelecteCropStage = singleValuedQuryExecution(queryFetchSelecteCropStage)

    jsonFetchSelecteCropStage = json.dumps({'getFetchSelecteCropStage': getFetchSelecteCropStage},
                                           default=decimal_date_default)
    return HttpResponse(jsonFetchSelecteCropStage)


"""
@@ **************  Crop Stage (End) ***********@@
"""

"""
@@ **************  Crop Variety (Start) ***********@@
"""


@login_required
def crop_variety(request):
    queryCropNameList = 'SELECT id, crop_name FROM public.crop order by id'
    cropNameList = multipleValuedQuryExecution(queryCropNameList)

    queryCropVarietyInfoList = 'SELECT id, (select crop_name from public.crop where id = crop_id )crop_name, variety_name FROM public.crop_variety order by id'
    cropVarietyInfoList = multipleValuedQuryExecution(queryCropVarietyInfoList)

    jsonCropVarietyInfoList = json.dumps({'cropVarietyInfoList': cropVarietyInfoList}, default=decimal_date_default)
    content = {
        'cropNameList': cropNameList,
        'jsonCropVarietyInfoList': jsonCropVarietyInfoList
    }
    return render(request, 'cais_module/crop_variety.html', content)


@login_required
def cropVarietyCreate(request):
    username = request.user.username
    crop_id = request.POST.get('crop_id', '')
    variety_name = request.POST.get('variety_name', '')
    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        queryEditCropStage = "UPDATE public.crop_variety SET crop_id= " + str(crop_id) + ", variety_name='" + str(
            variety_name) + "'  WHERE id= " + str(isEdit)
        __db_commit_query(queryEditCropStage)  ## Query Execution Function
    else:
        queryCreateCropVariety = "INSERT INTO public.crop_variety (id, crop_id, variety_name, created_at, created_by, updated_at, updated_by) VALUES(nextval('crop_variety_id_seq'::regclass), " + str(
            crop_id) + ", '" + str(variety_name) + "', now(), '" + str(username) + "', now(), '" + str(
            username) + "'); "
        __db_commit_query(queryCreateCropVariety)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/crop_variety/')


@login_required
def crop_variety_Edit(request):
    id = request.POST.get('id')

    queryFetchSelecteCropVariety = "SELECT id, crop_id, variety_name  FROM public.crop_variety where id = " + str(id)
    getFetchSelecteCropVariety = singleValuedQuryExecution(queryFetchSelecteCropVariety)

    jsonFetchSelecteCropVariety = json.dumps({'getFetchSelecteCropVariety': getFetchSelecteCropVariety},
                                             default=decimal_date_default)
    return HttpResponse(jsonFetchSelecteCropVariety)


"""
@@ **************  Crop Variety (End) ***********@@
"""

"""
@@ **************  Crop Stage Alert(End) ***********@@
"""


@login_required
def crop_stage_alert(request):
    queryCropNameList = "SELECT id, crop_name FROM public.crop"
    cropNameList = multipleValuedQuryExecution(queryCropNameList)

    queryCropStageAletrInfoList = 'SELECT id, (select crop_name from public.crop where id =  (select crop_id from public.crop_stage where id = crop_stage_id) )crop , (select stage_name from public.crop_stage where id = crop_stage_id )crop_stage, alert_name, alert_sms FROM public.crop_stage_alert order by id'

    cropStageAlertInfoList = multipleValuedQuryExecution(queryCropStageAletrInfoList)

    jsonCropStageAlertInfoList = json.dumps({'cropStageAlertInfoList': cropStageAlertInfoList},
                                            default=decimal_date_default)
    content = {
        'cropNameList': cropNameList,
        'jsonCropStageAlertInfoList': jsonCropStageAlertInfoList
    }
    return render(request, 'cais_module/crop_stage_alert.html', content)


@login_required
def cropStageAlertCreate(request):
    username = request.user.username
    crop_stage_id = request.POST.get('crop_stage_id', '')
    alert_name = request.POST.get('alert_name', '')
    alert_sms = request.POST.get('alert_sms', '')
    alert_sms = alert_sms.encode("utf-8")

    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        alert_sms = alert_sms.decode("utf-8")
        queryEditCropStageAlert = "UPDATE public.crop_stage_alert SET crop_stage_id= " + crop_stage_id + ", alert_name='" + alert_name + "', alert_sms='" + alert_sms + "' WHERE id= " + str(
            isEdit)
        __db_commit_query(queryEditCropStageAlert)  ## Query Execution Function
    else:
        queryCreateCropStageAlert = "INSERT INTO public.crop_stage_alert (id, crop_stage_id, alert_name, alert_sms, created_at, created_by, updated_at, updated_by) VALUES(nextval('crop_stage_alert_id_seq'::regclass), " + str(
            crop_stage_id) + ", '" + str(alert_name) + "', '" + str(alert_sms) + "', now(), '" + str(
            username) + "', now(), '" + str(username) + "') "
        __db_commit_query(queryCreateCropStageAlert)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/crop_stage_alert/')


@login_required
def alert_sms_stage_list(request):
    crop = request.POST.get('crop', '')
    queryCropStageList = 'SELECT id, stage_name FROM public.crop_stage where crop_id = ' + str(crop)
    cropStageList = multipleValuedQuryExecution(queryCropStageList)
    jsonCropStageList = json.dumps({'cropStageList': cropStageList}, default=decimal_date_default)
    return HttpResponse(jsonCropStageList)


@login_required
def crop_stage_alert_Edit(request):
    id = request.POST.get('id')

    queryFetchSelecteCropStageAlert = "SELECT id, (select crop_id from public.crop_stage where id = crop_stage_id )crop_name_selected_id , crop_stage_id, alert_name, alert_sms FROM public.crop_stage_alert where id = " + id
    getFetchSelecteCropStageAlert = singleValuedQuryExecution(queryFetchSelecteCropStageAlert)

    jsonFetchSelecteCropStageAlert = json.dumps({'getFetchSelecteCropStageAlert': getFetchSelecteCropStageAlert},
                                                default=decimal_date_default)
    return HttpResponse(jsonFetchSelecteCropStageAlert)


"""
@@ **************  Crop Stage Alert(End) ***********@@
"""

"""
@@ **************  Group (Start)
"""


@login_required
def group_details(request):
    queryGroupNameList = 'SELECT id, group_name FROM public.group_details order by id desc'
    groupNameList = multipleValuedQuryExecution(queryGroupNameList)
    jsonGroupNameList = json.dumps({'groupNameList': groupNameList}, default=decimal_date_default)

    content = {

        'jsonGroupNameList': jsonGroupNameList
    }

    return render(request, 'cais_module/group_details.html', content)


@login_required
def groupCreate(request):
    username = request.user.username
    groupName = request.POST.get('group_name', '')
    isEdit = request.POST.get('isEdit')
    if isEdit != '':
        queryEditGroupName = "UPDATE public.group_details SET group_name='" + groupName + "' WHERE id= " + str(isEdit)
        __db_commit_query(queryEditGroupName)  ## Query Execution Function
    else:
        queryCreateGroupName = "INSERT INTO public.group_details (group_name, created_at, created_by, updated_at, updated_by) VALUES('" + str(
            groupName) + "', now(), '" + str(username) + "', now(), '" + str(username) + "')"
        __db_commit_query(queryCreateGroupName)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/group_details/')


@login_required
def group_details_Edit(request):
    id = request.POST.get('id')
    queryFetchSpecificGroup = " SELECT id, group_name FROM public.group_details where id = " + str(id)
    getFetchSpecificGroup = singleValuedQuryExecution(queryFetchSpecificGroup)

    jsonFetchSpecificGroup = json.dumps({'getFetchSpecificGroup': getFetchSpecificGroup}, default=decimal_date_default)

    return HttpResponse(jsonFetchSpecificGroup)


"""
@@ **************  Group (End)
"""

"""
@@ **************  Season (Start)
"""


@login_required
def season(request):
    querySeasonNameList = 'SELECT id, season_name FROM public.cropping_season order by id desc'
    seasonNameList = multipleValuedQuryExecution(querySeasonNameList)
    jsonSeasonNameList = json.dumps({'seasonNameList': seasonNameList}, default=decimal_date_default)

    content = {

        'jsonSeasonNameList': jsonSeasonNameList
    }

    return render(request, 'cais_module/crop_season.html', content)


@login_required
def seasonCreate(request):
    username = request.user.username
    seasonName = request.POST.get('season_name', '')
    isEdit = request.POST.get('isEdit')
    if isEdit != '':
        queryEditSeasonName = "UPDATE public.cropping_season SET season_name='" + seasonName + "' WHERE id= " + str(isEdit)
        __db_commit_query(queryEditSeasonName)  ## Query Execution Function
    else:
        queryCreateSeasonName = "INSERT INTO public.cropping_season (season_name) VALUES('" + str(
            seasonName) + "')"
        __db_commit_query(queryCreateSeasonName)  ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/season/')


@login_required
def season_details_Edit(request):
    id = request.POST.get('id')
    queryFetchSpecificSeason = " SELECT id, season_name FROM public.cropping_season where id = " + str(id)
    getFetchSpecificSeason = singleValuedQuryExecution(queryFetchSpecificSeason)

    jsonFetchSpecificSeason = json.dumps({'getFetchSpecificSeason': getFetchSpecificSeason}, default=decimal_date_default)

    return HttpResponse(jsonFetchSpecificSeason)


"""
@@ **************  Season (End)
"""

"""
@@ **************  Crop Group (Start)
"""


@login_required
def crop_group(request):
    queryGroupNameList = "SELECT id, group_name FROM public.group_details"
    groupNameList = multipleValuedQuryExecution(queryGroupNameList)

    queryCropNameList = 'SELECT id, crop_name FROM public.crop'
    cropNameList = multipleValuedQuryExecution(queryCropNameList)

    querySeasonList = 'SELECT id, season_name FROM public.season'
    seasonList = multipleValuedQuryExecution(querySeasonList)

    queryCropGroupInfoList = "SELECT id, (select group_name FROM public.group_details where id = group_id )group_name, (SELECT crop_name FROM public.crop where id = crop_id)crop_name, sowing_date, (SELECT season_name FROM public.season where id = season_id )season_name FROM public.crop_group order by id"
    cropGroupInfoList = multipleValuedQuryExecution(queryCropGroupInfoList)

    jsonCropGroupInfoList = json.dumps({'cropGroupInfoList': cropGroupInfoList}, default=decimal_date_default)
    content = {
        'groupNameList': groupNameList,
        'cropNameList': cropNameList,
        'seasonList': seasonList,
        'jsonCropGroupInfoList': jsonCropGroupInfoList
    }

    return render(request, 'cais_module/crop_group.html', content)


@login_required
def cropGroupCreate(request):
    username = request.user.username
    group_id = request.POST.get('group_id', '')
    crop_id = request.POST.get('crop_id', '')
    sowing_data = request.POST.get('sowing_data', '')
    season_id = request.POST.get('season_id', '')
    isEdit = request.POST.get('isEdit')
    if isEdit != '':
        queryEditCropGroup = "UPDATE public.crop_group SET group_id= " + group_id + ", crop_id= " + crop_id + ", sowing_date='" + sowing_data + "', season_id=" + season_id + " WHERE id= " + str(
            isEdit)
        __db_commit_query(queryEditCropGroup)  ## Query Execution Function
    else:
        queryCreateCropGroup = "INSERT INTO public.crop_group (id, group_id, crop_id, sowing_date, season_id, created_at, created_by, updated_at, updated_by) VALUES(nextval('crop_group_id_seq'::regclass), " + str(
            group_id) + ", " + str(crop_id) + ", '" + str(sowing_data) + "', " + str(season_id) + ", now(), '" + str(
            username) + "', now(), '" + str(username) + "');"
        __db_commit_query(queryCreateCropGroup)

    return HttpResponseRedirect('/maxmodule/cais_module/crop_group/')


@login_required
def crop_group_Edit(request):
    id = request.POST.get('id')

    queryFetchSelectedCropGroup = "SELECT id, group_id, crop_id, sowing_date, season_id  FROM public.crop_group where id = " + str(
        id);
    getFetchSelectedCropGroup = singleValuedQuryExecution(queryFetchSelectedCropGroup)

    jsonFetchSelectedCropGroup = json.dumps({'getFetchSelectedCropGroup': getFetchSelectedCropGroup},
                                            default=decimal_date_default)
    return HttpResponse(jsonFetchSelectedCropGroup)


"""
@@ ************** Crop Group (End)
"""

"""
@@ ************** Farmer (Start)
"""
@csrf_exempt
def get_farmer_list(request):

    draw = request.POST['draw']
    start = int(request.POST['start'])
    length = int(request.POST['length'])
    search_val = str(request.POST['search[value]'])
    if not len(search_val):
        search_val = '%'
    else:  search_val = '%'+str(search_val)+'%'

    country = request.POST.get('country','%')
    division = request.POST.get('division','%')
    district = request.POST.get('district','%')
    upazilla = request.POST.get('upazilla','%')
    union = request.POST.get('union','%')
    organization = request.POST.get('organization','%')
    program = request.POST.get('program','%')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date', 'now()::date')
    crop = request.POST.get('crop', '%')
    crop_variety = request.POST.get('crop_variety', '%')
    season = request.POST.get('season', '%')
    group = request.POST.get('group', '%')

    farmer_list = []
    df_fcq = pandas.DataFrame()
    df_gr = pandas.DataFrame()
    stat_crop = 0
    stat_grp = 0
    if crop != '%' or from_date != '':
        stat_crop = 1
        if crop != '%' and from_date != '':
            farmer_crop_query = "select distinct farmer_id from farmer_crop_info where crop_id::text like '"+str(crop)+"' and crop_variety_id::text like '"+str(crop_variety)+"' and season_id::text like '"+str(season)+"' and sowing_date::date  between '" + str(from_date) + "' and '" + str(to_date)+"'"
            df_fcq = pandas.read_sql(farmer_crop_query,connection)
        elif crop != '%':
            farmer_crop_query = "select distinct farmer_id from farmer_crop_info where crop_id::text like '"+str(crop)+"' and crop_variety_id::text like '"+str(crop_variety)+"' and season_id::text like '"+str(season)+"'"
            df_fcq = pandas.read_sql(farmer_crop_query, connection)
        elif from_date != '':
            farmer_crop_query = " select distinct farmer_id from farmer_crop_info where sowing_date::date  between '" + str(from_date) + "' and '" + str(to_date)+"'"
            df_fcq = pandas.read_sql(farmer_crop_query, connection)
        print(farmer_crop_query)

    if group != '%':
        stat_grp = 1
        group_query = "select distinct farmer_id from farmer_group where group_id::text like '"+str(group)+"'"
        df_gr = pandas.read_sql(group_query, connection)

    if not df_fcq.empty and not df_gr.empty:
        final_df = pandas.merge(df_gr, df_fcq, on='farmer_id')
        farmer_list = final_df.farmer_id.tolist()
    else:
        if not df_fcq.empty:
            farmer_list = df_fcq.farmer_id.tolist()
        elif not df_gr.empty:
            farmer_list = df_gr.farmer_id.tolist()


    data = []
    if stat_crop or stat_grp:
        farmer_list = str(farmer_list).replace('[', '{').replace(']', '}')
        data_query = "SELECT farmer.id,case when status = 1 then '<a href=\"/ifcmodule/farmer_profile_view/'|| farmer.id ||'\">'|| farmer_name ||'</a>' else '<a style=\"color:red;\" href=\"/ifcmodule/farmer_profile_view/'|| farmer.id ||'\">'|| farmer_name ||'</a>' end , mobile_number,(SELECT name FROM public.geo_country WHERE id = country_id) country_name, (SELECT name FROM public.geo_zone WHERE id = zone_id) zone_name, (SELECT name FROM public.geo_district WHERE id = district_id) district_name, (SELECT name FROM public.geo_upazilla WHERE id = upazila_id) upazila_name, (SELECT name FROM public.geo_union WHERE id = union_id) union_name, (SELECT organization FROM public.usermodule_organizations WHERE id = organization_id)organization_name, (SELECT program_name FROM public.usermodule_programs WHERE id = program_id) program_name,coalesce((select group_name  from group_details where id = group_id ),'') group_name,'<button onclick=\"getEditId(' || farmer.id || ')\" class=\"btn btn-primary\" role=\"button\" >Edit</button>' FROM public.farmer left join farmer_group on farmer.id = farmer_group.farmer_id where farmer.id = any('"+str(farmer_list)+"') and LOWER(farmer_name) like '"+str(search_val)+"' and organization_id::text like '"+str(organization)+"' and program_id::text like '"+str(program)+"' and country_id::text like '"+str(country)+"' and zone_id::text like '"+str(division)+"' and district_id::text like '"+str(district)+"' and upazila_id::text like '"+str(upazilla)+"' and union_id::text like '"+str(union)+"' ORDER BY id DESC limit "+str(length)+" offset "+str(start)
        data = multipleValuedQuryExecution(data_query)
        total_count_query = "select count(*) total_farmer from farmer where farmer.id = any('"+str(farmer_list)+"') and LOWER(farmer_name) like '"+str(search_val)+"' and organization_id::text like '"+str(organization)+"' and program_id::text like '"+str(program)+"' and country_id::text like '"+str(country)+"' and zone_id::text like '"+str(division)+"' and district_id::text like '"+str(district)+"' and upazila_id::text like '"+str(upazilla)+"' and union_id::text like '"+str(union)+"'"
        df = pandas.DataFrame()
        df = pandas.read_sql(total_count_query, connection)
        total_count = df.total_farmer.tolist()[0]
    else:
        data_query = "SELECT farmer.id,case when status = 1 then '<a href=\"/ifcmodule/farmer_profile_view/'|| farmer.id ||'\">'|| farmer_name ||'</a>' else '<a style=\"color:red;\" href=\"/ifcmodule/farmer_profile_view/'|| farmer.id ||'\">'|| farmer_name ||'</a>' end , mobile_number,(SELECT name FROM public.geo_country WHERE id = country_id) country_name, (SELECT name FROM public.geo_zone WHERE id = zone_id) zone_name, (SELECT name FROM public.geo_district WHERE id = district_id) district_name, (SELECT name FROM public.geo_upazilla WHERE id = upazila_id) upazila_name, (SELECT name FROM public.geo_union WHERE id = union_id) union_name, (SELECT organization FROM public.usermodule_organizations WHERE id = organization_id)organization_name, (SELECT program_name FROM public.usermodule_programs WHERE id = program_id) program_name,coalesce((select group_name  from group_details where id = group_id ),'') group_name,'<button onclick=\"getEditId(' || farmer.id || ')\" class=\"btn btn-primary\" role=\"button\" >Edit</button>' FROM public.farmer left join farmer_group on farmer.id = farmer_group.farmer_id  where LOWER(farmer_name) like '"+str(search_val)+"' and organization_id::text like '"+str(organization)+"' and program_id::text like '"+str(program)+"' and country_id::text like '"+str(country)+"' and zone_id::text like '"+str(division)+"' and district_id::text like '"+str(district)+"' and upazila_id::text like '"+str(upazilla)+"' and union_id::text like '"+str(union)+"' ORDER BY id DESC limit "+str(length)+" offset "+str(start)
        data = multipleValuedQuryExecution(data_query)
        total_count_query = "select count(*) total_farmer from farmer where  LOWER(farmer_name) like '" + str(
            search_val) + "' and organization_id::text like '" + str(
            organization) + "' and program_id::text like '" + str(program) + "' and country_id::text like '" + str(
            country) + "' and zone_id::text like '" + str(division) + "' and district_id::text like '" + str(
            district) + "' and upazila_id::text like '" + str(upazilla) + "' and union_id::text like '" + str(
            union) + "'"
        df = pandas.DataFrame()
        df = pandas.read_sql(total_count_query, connection)
        total_count = df.total_farmer.tolist()[0]

    filtered_count = len(data)
    return HttpResponse(json.dumps({"draw": draw,
        "recordsTotal": total_count,
        "recordsFiltered": total_count,
        "data": data,
            }, default=decimal_date_default))


def export_farmer(request):
    country = request.POST.get('country', '%')
    division = request.POST.get('division', '%')
    district = request.POST.get('district', '%')
    upazilla = request.POST.get('upazilla', '%')
    union = request.POST.get('union', '%')
    organization = request.POST.get('organization', '%')
    program = request.POST.get('program', '%')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    crop = request.POST.get('crop')
    crop_variety = request.POST.get('crop_variety')
    season = request.POST.get('season')
    group = request.POST.get('group')

    farmer_list = []
    df_fcq = pandas.DataFrame()
    df_gr = pandas.DataFrame()
    stat_crop = 0
    stat_grp = 0

    if crop != '%' or from_date != '':
        stat_crop = 1
        if crop != '%' and from_date != '':
            farmer_crop_query = "select distinct farmer_id from farmer_crop_info where crop_id::text like '" + str(
                crop) + "' and crop_variety_id::text like '" + str(crop_variety) + "' and season_id::text like '" + str(
                season) + "' and sowing_date::date  between '" + str(from_date) + "' and '" + str(to_date) + "'"
            df_fcq = pandas.read_sql(farmer_crop_query, connection)
        elif crop != '%':
            farmer_crop_query = "select distinct farmer_id from farmer_crop_info where crop_id::text like '" + str(
                crop) + "' and crop_variety_id::text like '" + str(crop_variety) + "' and season_id::text like '" + str(
                season) + "'"
            df_fcq = pandas.read_sql(farmer_crop_query, connection)
        elif from_date != '':
            farmer_crop_query = " select distinct farmer_id from farmer_crop_info where sowing_date::date  between '" + str(
                from_date) + "' and '" + str(to_date) + "'"
            df_fcq = pandas.read_sql(farmer_crop_query, connection)

    if group != '%':
        stat_grp = 1
        group_query = "select distinct farmer_id from farmer_group where group_id::text like '" + str(group) + "'"
        df_gr = pandas.read_sql(group_query, connection)

    if not df_fcq.empty and not df_gr.empty:
        final_df = pandas.merge(df_gr, df_fcq, on='farmer_id')
        farmer_list = final_df.farmer_id.tolist()
    else:
        if not df_fcq.empty:
            farmer_list = df_fcq.farmer_id.tolist()
        elif not df_gr.empty:
            farmer_list = df_gr.farmer_id.tolist()

    df = pandas.DataFrame()
    if stat_crop or stat_grp:
        farmer_list = str(farmer_list).replace('[', '{').replace(']', '}')
        query = "with t as (SELECT farmer.id farmer_id,farmer_name, mobile_number,(SELECT name FROM public.geo_country WHERE id = country_id) country_name,(SELECT name FROM public.geo_zone WHERE id = zone_id) zone_name, (SELECT name FROM public.geo_district WHERE id = district_id) district_name, (SELECT name FROM public.geo_upazilla WHERE id = upazila_id) upazila_name, (SELECT name FROM public.geo_union WHERE id = union_id) union_name, (SELECT organization FROM public.usermodule_organizations WHERE id = organization_id)organization_name, (SELECT program_name FROM public.usermodule_programs WHERE id = program_id) program_name,coalesce((select group_name  from group_details where id = group_id ),'') group_name FROM public.farmer left join farmer_group on farmer.id = farmer_group.farmer_id where farmer.id = any('" + str(farmer_list) + "') and  organization_id::text like '" + str(
            organization) + "' and program_id::text like '" + str(program) + "' and country_id::text like '" + str(
            country) + "' and zone_id::text like '" + str(division) + "' and district_id::text like '" + str(
            district) + "' and upazila_id::text like '" + str(upazilla) + "' and union_id::text like '" + str(
            union) + "' ORDER BY farmer.id desc)select t.*,farmer_crop_info.crop_id,(select crop_name from crop where id = farmer_crop_info.crop_id),farmer_crop_info.crop_variety_id,(select variety_name from crop_variety where id = farmer_crop_info.crop_variety_id),farmer_crop_info.season_id,(select season_name from cropping_season where id = farmer_crop_info.season_id),farmer_crop_info.sowing_date from t left join farmer_crop_info on farmer_crop_info.farmer_id = t.farmer_id"
        df = pandas.read_sql(query, connection)

    else:
        query = " with t as (SELECT farmer.id farmer_id,farmer_name, mobile_number,(SELECT name FROM public.geo_country WHERE id = country_id) country_name,(SELECT name FROM public.geo_zone WHERE id = zone_id) zone_name, (SELECT name FROM public.geo_district WHERE id = district_id) district_name, (SELECT name FROM public.geo_upazilla WHERE id = upazila_id) upazila_name, (SELECT name FROM public.geo_union WHERE id = union_id) union_name, (SELECT organization FROM public.usermodule_organizations WHERE id = organization_id)organization_name, (SELECT program_name FROM public.usermodule_programs WHERE id = program_id) program_name,coalesce((select group_name  from group_details where id = group_id ),'') group_name FROM public.farmer left join farmer_group on farmer.id = farmer_group.farmer_id where organization_id::text like '" + str(
            organization) + "' and program_id::text like '" + str(program) + "' and country_id::text like '" + str(
            country) + "' and zone_id::text like '" + str(division) + "' and district_id::text like '" + str(
            district) + "' and upazila_id::text like '" + str(upazilla) + "' and union_id::text like '" + str(
            union) + "' ORDER BY farmer.id desc)select t.*,farmer_crop_info.crop_id,(select crop_name from crop where id = farmer_crop_info.crop_id),farmer_crop_info.crop_variety_id,(select variety_name from crop_variety where id = farmer_crop_info.crop_variety_id),farmer_crop_info.season_id,(select season_name from cropping_season where id = farmer_crop_info.season_id),farmer_crop_info.sowing_date from t left join farmer_crop_info on farmer_crop_info.farmer_id = t.farmer_id"
        df = pandas.read_sql(query, connection)

    writer = pandas.ExcelWriter("onadata/media/uploaded_files/output.xls")
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    f = open('onadata/media/uploaded_files/output.xls', 'r')
    response = HttpResponse(f, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Farmer.xls'
    return response

@login_required
def farmer(request):
    # queryCreateFarmer = 'SELECT id, farmer_name, mobile_number, ' \
    #                     '(SELECT name FROM public.geo_country where id = country_id ) country_name, ' \
    #                     '(SELECT name FROM public.geo_zone where id = zone_id )zone_name, ' \
    #                     '(SELECT name FROM public.geo_district where id = district_id )district_name,' \
    #                     ' (SELECT name FROM public.geo_upazilla where id = upazila_id )upazila_name, ' \
    #                     '(SELECT name FROM public.geo_union where id = union_id )union_name, (SELECT organization FROM public.usermodule_organizations where id = organization_id )organization_name , ' \
    #                     ' (SELECT program_name FROM public.usermodule_programs where id = program_id) program_name,status  FROM public.farmer order by id desc '

    # farmerInfoList = multipleValuedQuryExecution(queryCreateFarmer)

    # print(json.dumps({'farmerInfoList': farmerInfoList}, default=decimal_date_default))
    ##  Get Geo Country List
    countryQuery = "select id,name from public.geo_country"
    country_List = makeTableList(countryQuery)

    # disQuery = "select id,name from public.geo_district"
    # dist_List = makeTableList(disQuery)


    ##  Get Organization  List
    organizationQuery = "select id,organization from public.usermodule_organizations"
    organization_List = makeTableList(organizationQuery)

    # jsonFarmerInfoList = json.dumps({'farmerInfoList': farmerInfoList}, default=decimal_date_default)
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
        # 'jsonFarmerInfoList': jsonFarmerInfoList,
        'country_List': country_List,
        'organization_List': organization_List,'country':country,'organization':organization,'crop_list':crop_list,'season':season,'group':group
    }

    return render(request, 'cais_module/farmer.html', content)


@login_required
def farmerCreate(request):
    username = request.user.username
    farmer_name = request.POST.get('farmer_name', '')
    mobile_num = request.POST.get('mobile_num', '')
    country_id = request.POST.get('country_id', '')
    zone_id = request.POST.get('zone_id', '')
    district_id = request.POST.get('district_id', '')
    upazila_id = request.POST.get('upazila_id', '')
    union_id = request.POST.get('union_id', '')
    organization_id = request.POST.get('organization_id', '')
    program_id = request.POST.get('program_id', '')

    isEdit = request.POST.get('isEdit')
    if isEdit != '':
        queryEditFarmer = "UPDATE public.farmer SET farmer_name='" + str(farmer_name) + "', mobile_number = '"+str(mobile_num)+"', country_id = "+str(country_id)+" , zone_id = "+str(zone_id)+" , district_id= " + str(district_id) + ", upazila_id= " + str(upazila_id) + ", union_id=" + str(union_id) + ", program_id=" + str(program_id) + ", organization_id = " + str(organization_id) + "  WHERE id= " + str(
            isEdit)
        __db_commit_query(queryEditFarmer)
    else:
        queryCreateCropGroup = "INSERT INTO public.farmer(id, farmer_name, country_id , zone_id,  district_id, upazila_id, union_id,  organization_id , program_id , mobile_number, created_at, created_by, updated_at, updated_by ) VALUES(nextval('farmer_id_seq'::regclass), '" + str(
            farmer_name) + "',"+str(country_id)+" ,"+str(zone_id)+"," + str(district_id) + ", " + str(upazila_id) + ", " + str(union_id) + ", " + str(
            organization_id) + "," + str(program_id) + ", '" + str(mobile_num) + "', now(), '" + str(
            username) + "', now(), '" + str(username) + "');"
        __db_commit_query(queryCreateCropGroup)

    return HttpResponseRedirect('/maxmodule/cais_module/farmer/')


@login_required
def farmer_Edit(request):
    id = request.POST.get('id')

    queryFetchSelectedFarmer = "SELECT id, farmer_name, country_id  , zone_id, district_id, upazila_id, union_id, organization_id, program_id , mobile_number FROM public.farmer where id = " + str(id);
    getFetchSelectedFarmer = singleValuedQuryExecution(queryFetchSelectedFarmer)


    zoneQuery = "select id,name from geo_zone where geo_country_id =" + str(getFetchSelectedFarmer[2])
    zone_List = makeTableList(zoneQuery)


    districtQuery = "select id,name from geo_district where geo_zone_id =" + str(getFetchSelectedFarmer[3])
    district_List = makeTableList(districtQuery)

    upazilaQuery = "select id,name from geo_upazilla where geo_district_id =" + str(getFetchSelectedFarmer[4])
    upazila_List = makeTableList(upazilaQuery)
    # jsonUpaList = json.dumps({'upazila_List': upazila_List}, default=decimal_date_default)

    unionQuery = "select id,name from geo_union where geo_upazilla_id = " + str(getFetchSelectedFarmer[5])
    union_List = makeTableList(unionQuery)
    # jsonUnionList = json.dumps({'union_List': union_List}, default=decimal_date_default)

    programQuery = "select id, program_name from usermodule_programs where org_id =" + str(getFetchSelectedFarmer[7])
    program_List = makeTableList(programQuery)
    # jsonProgramList = json.dumps({'program_List': program_List}, default=decimal_date_default)


    jsonFetchSelectedFarmer = json.dumps({'getFetchSelectedFarmer': getFetchSelectedFarmer,
                                          'zone_List':zone_List,
                                          'district_List':district_List ,
                                          'upazila_List': upazila_List,
                                          'union_List': union_List,
                                          'program_List': program_List
                                          }, default=decimal_date_default)
    return HttpResponse(jsonFetchSelectedFarmer)


@login_required
def getProgramList(request):
    selectedOrganization = request.POST.get('organization')
    programQuery = "select id, program_name from usermodule_programs where org_id =" + selectedOrganization
    program_List = makeTableList(programQuery)
    jsonProgramList = json.dumps({'program_List': program_List}, default=decimal_date_default)

    return HttpResponse(jsonProgramList)


"""
@@ ************** Farmer  (End)
"""

"""
@@ ************** Farmer Group (Start)
"""


@login_required
def farmer_group(request):
    queryFarmerList = "SELECT id, farmer_name FROM public.farmer;"
    getFarmerList = makeTableList(queryFarmerList)

    queryCropGroupList = "SELECT id FROM public.group_details"
    getCropGroupList = makeTableList(queryCropGroupList)

    queryIncludedGroupListInCropGroup = "SELECT id group_id , group_name group_id_name FROM public.group_details"
    getIncludedGroupListInCropGroup = makeTableList(queryIncludedGroupListInCropGroup)

    queryCreateFarmerGroup = "select id,(select farmer_name from farmer where id = farmer_id )farmer_id,(select group_name from group_details where id = group_id)group_name from farmer_group"
    print(queryCreateFarmerGroup)
    farmerGroupInfoList = multipleValuedQuryExecution(queryCreateFarmerGroup)

    jsonFarmerGroupInfoList = json.dumps({'farmerGroupInfoList': farmerGroupInfoList}, default=decimal_date_default)

    content = {

        'getFarmerList': getFarmerList,
        'getCropGroupList': getCropGroupList,
        'jsonFarmerGroupInfoList': jsonFarmerGroupInfoList,
        'getIncludedGroupListInCropGroup': getIncludedGroupListInCropGroup
    }

    return render(request, 'cais_module/farmer_group.html', content)


@login_required
def includedGroupCropList(request):
    selectedGroup_name_id = request.POST.get('group_name_id')
    querySelectedGroupCropList = "SELECT id , group_id, (select crop_name FROM public.crop where id = crop_id)crop_id_name FROM public.crop_group where group_id = " + str(
        selectedGroup_name_id)
    getSelectedGroupCropList = multipleValuedQuryExecution(querySelectedGroupCropList)
    jsonSelectedGroupCropList = json.dumps({'getSelectedGroupCropList': getSelectedGroupCropList},
                                           default=decimal_date_default)
    return HttpResponse(jsonSelectedGroupCropList)


@login_required
def groupNameForEdit(request):
    selectedCrop_group_id = request.POST.get('crop_group_id')
    querySelectedGroup = "SELECT id , group_id FROM public.crop_group where id = " + str(selectedCrop_group_id)
    getSelectedGroup = singleValuedQuryExecution(querySelectedGroup)
    jsonSelectedGroup = json.dumps({'getSelectedGroupList': getSelectedGroup}, default=decimal_date_default)

    return HttpResponse(jsonSelectedGroup)


@login_required
def groupCropNameForEdit(request):
    selectedCrop_group_id = request.POST.get('crop_group_id')
    selectedGroupId = request.POST.get('group_name_id')
    querySelectedGroup = "SELECT id , group_id , (select crop_name FROM public.crop where id = crop_id)crop_id_name  FROM public.crop_group where id = " + str(
        selectedCrop_group_id) + " and group_id = " + str(selectedGroupId)
    getSelectedCrop = singleValuedQuryExecution(querySelectedGroup)
    jsonSelectedCrop = json.dumps({'getSelectedCrop': getSelectedCrop}, default=decimal_date_default)

    return HttpResponse(jsonSelectedCrop)


@login_required
def farmer_groupCreate(request):
    username = request.user.username
    farmer_id = request.POST.get('farmer_id')
    group_id = request.POST.get('group_id')
    isEdit = request.POST.get('isEdit')
    if isEdit != '':
        queryEditFarmerGroup = "UPDATE public.farmer_group SET farmer_id= " + farmer_id + ",group_id= " + group_id + "  WHERE id= " + str(
            isEdit)
        __db_commit_query(queryEditFarmerGroup)
    else:
        queryCreateFarmerGroup = "INSERT INTO public.farmer_group (farmer_id,group_id, created_at, created_by, updated_at, updated_by) VALUES(" + str(
            farmer_id) + ", " + str(group_id) + ", now(), '" + str(username) + "', now(), '" + str(username) + "')"
        __db_commit_query(queryCreateFarmerGroup)

    return HttpResponseRedirect('/maxmodule/cais_module/farmer_group/')


@login_required
def farmer_group_Edit(request):
    id = request.POST.get('id')

    queryFetchSelectedFarmerGroup = "SELECT id, farmer_id, group_id  FROM public.farmer_group  where id = " + str(
        id)
    getFetchSelectedFarmerGroup = singleValuedQuryExecution(queryFetchSelectedFarmerGroup)

    jsonqueryFetchSelectedFarmerGroup = json.dumps({'getFetchSelectedFarmerGroup': getFetchSelectedFarmerGroup},
                                                   default=decimal_date_default)

    return HttpResponse(jsonqueryFetchSelectedFarmerGroup)

def farmer_group_bulk_upload(request):
    if request.method == 'POST':
        myfile = request.FILES['fileToUpload']
        url = "onadata/media/uploaded_files/"
        fs = FileSystemStorage(location=url)
        filename = fs.save(myfile.name, myfile)
        full_file_path = "onadata/media/uploaded_files/" + filename
        xlsx = pandas.ExcelFile(full_file_path)
        df = xlsx.parse(0)
        for each in df.index:
            try:
                insert_query = "insert into farmer_group(farmer_id,group_id,created_by)values("+str(df.loc[each]['farmer_id'])+","+str(df.loc[each]['group_id'])+",'"+str(request.user.username)+"')"
                print(insert_query)
                __db_commit_query(insert_query)
            except e:
                print(e)
                continue
        return HttpResponseRedirect('/maxmodule/cais_module/farmer_group/')


"""
@@ ************** Farmer Group (End)
"""

"""
@@*************************** Get Geo Location (Start) **************************
"""


@login_required
def getZones(request):
    selectedCountry = request.POST.get('country')
    zoneQuery = "select id,name from geo_zone where geo_country_id =" + selectedCountry
    zone_List = makeTableList(zoneQuery)
    jsonZoneList = json.dumps({'zone_List': zone_List}, default=decimal_date_default)

    return HttpResponse(jsonZoneList)


@login_required
def getDistricts(request):
    selectedZone = request.POST.get('zone')
    districtQuery = "select id,name from geo_district where geo_zone_id =" + selectedZone
    district_List = makeTableList(districtQuery)
    jsonDisList = json.dumps({'district_List': district_List}, default=decimal_date_default)

    return HttpResponse(jsonDisList)


@login_required
def getUpazilas(request):
    selectedDistrict = request.POST.get('district')
    upazilaQuery = "select id,name from geo_upazilla where geo_district_id =" + selectedDistrict
    upazila_List = makeTableList(upazilaQuery)
    jsonUpaList = json.dumps({'upazila_List': upazila_List}, default=decimal_date_default)

    return HttpResponse(jsonUpaList)


@login_required
def getUnions(request):
    selectedUpazila = request.POST.get('upazila')
    unionQuery = "select id,name from geo_union where geo_upazilla_id = " + selectedUpazila
    union_List = makeTableList(unionQuery)
    jsonUnionList = json.dumps({'union_List': union_List}, default=decimal_date_default)
    return HttpResponse(jsonUnionList)


"""
@@*************************** Get Geo Location (End) **************************
"""

"""
@@********************  Alert SMS Process (Start) ********************
"""


@login_required
def alert_sms_process(request):
    queryGrouplist = "SELECT id, group_name FROM public.group_details"
    getGroupList = multipleValuedQuryExecution(queryGrouplist)

    queryAlertSMSInfo = "SELECT id, group_name_id, crop_name_id, crop_stage, alert_name_id, alert_sms_id FROM public.vwalert_sms_process order by id"
    getQueryAlertInfo = multipleValuedQuryExecution(queryAlertSMSInfo)

    jsonCropList = json.dumps({'getQueryAlertInfo': getQueryAlertInfo}, default=decimal_date_default)

    content = {

        'getGroupList': getGroupList,
        'jsonCropList': jsonCropList

    }
    return render(request, 'cais_module/alert_sms_process.html', content);


@login_required
def alert_sms_process_crop_list(request):
    selectedGroup = request.POST.get('group')
    cropQuery = "SELECT crop_id, (SELECT crop_name FROM public.crop where id = crop_id ) crop_name , date_part('day', date (sowing_date) )sowing_date FROM public.crop_group where group_id = " + str(
        selectedGroup)
    crop_List = makeTableList(cropQuery)
    jsonCropList = json.dumps({'crop_List': crop_List}, default=decimal_date_default)
    return HttpResponse(jsonCropList)


@login_required
def alert_sms_process_stage_name(request):
    selectedGroup = request.POST.get('group')
    selectedCrop = request.POST.get('crop')

    #  stageQuery = "SELECT stage_name, start_day, end_day  FROM public.crop_stage where crop_id = "+ selectedCrop;

    # stageQuery ="with w as ( " \
    #           "with t as (" \
    #           "SELECT id, group_id, crop_id, date_part('day' , date(sowing_date)) sowing_date " \
    #           "FROM public.crop_group where group_id = "+str(selectedGroup)+" and crop_id = "+str(selectedCrop)+") " \
    #          "select t.* , s.stage_name , s.start_day, s.end_day from t left join public.crop_stage s on t.crop_id = s.crop_id )" \
    #           "select stage_name from w  where sowing_date between start_day and end_day"

    stageQuery = "with t as(SELECT (now()::date-sowing_date::date) age FROM crop_group where group_id=" + str(
        selectedGroup) + " and crop_id=" + str(
        selectedCrop) + "),t1 as(SELECT crop_id, stage_name, start_day, end_day FROM crop_stage where crop_id=" + str(
        selectedCrop) + ")select stage_name   from t1,t where t.age between start_day and end_day"

    stage = makeTableList(stageQuery)

    jsonStageList = json.dumps({'stage': stage}, default=decimal_date_default)
    return HttpResponse(jsonStageList)


# def alert_sms_process_alert_list(request):
#     selectedStage = request.POST.get('stage')

#     alertQuery = "SELECT id, alert_name FROM public.crop_stage_alert where crop_stage_id = (select id FROM public.crop_stage where stage_name::text like '"+str(selectedStage)+"' )";

#     print("alertQuery")
#     print(alertQuery)
#     alertList = makeTableList(alertQuery)


#     jsonAlertList = json.dumps({'alertList': alertList}, default=decimal_date_default)

#     return HttpResponse(jsonAlertList)

@login_required
def alert_sms_process_alert_list(request):
    selectedStage = request.POST.get('stage')
    selectedCrop = request.POST.get('crop')


    alertQuery = "SELECT id, alert_name FROM public.crop_stage_alert where crop_stage_id = any(select id FROM public.crop_stage where stage_name::text like '" + str(
        selectedStage) + "' and crop_id::text like '" + str(selectedCrop) + "' )";


    alertList = makeTableList(alertQuery)
    jsonAlertList = json.dumps({'alertList': alertList}, default=decimal_date_default)


    return HttpResponse(jsonAlertList)


@login_required
def alert_sms_process_alert_sms(request):
    selectedAlert = request.POST.get('alert_name')
    alertSmsQuery = "SELECT id, alert_name,  alert_sms FROM public.crop_stage_alert where id = " + str(
        selectedAlert) + " ";
    alertSMSList = makeTableList(alertSmsQuery)
    jsonAlertSMSList = json.dumps({'alertSMS': alertSMSList}, default=decimal_date_default)
    return HttpResponse(jsonAlertSMSList)


@login_required
def alert_sms_process_info_store(request):
    username = request.user.username

    selectedGroup = request.POST.get('group_id', '')
    selectedCrop = request.POST.get('crop_id', '')
    selectedStage = request.POST.get('stage_name', '')
    selectedAlert = request.POST.get('alert_id', '')
    selectedAlertSMS = request.POST.get('alert_sms', '')

    isEdit = request.POST.get('isEdit')

    queryCropGroupID = "SELECT id, group_id, crop_id FROM public.crop_group where group_id = " + str(
        selectedGroup) + " and crop_id = " + str(selectedCrop);
    getCropGroupID = singleValuedQuryExecution(queryCropGroupID)
    cropGroupID = getCropGroupID[0]

    if isEdit != '':
        queryEditAlertLog = "UPDATE public.alert_log SET crop_group_id= " + str(
            cropGroupID) + ", crop_stage_alert_id= " + str(selectedAlert) + " WHERE id= " + str(isEdit)
        __db_commit_query(queryEditAlertLog)
    else:
        queryCreateAlertLog = "INSERT INTO public.alert_log (id, crop_group_id, crop_stage_alert_id, created_by, created_at, updated_by, updated_at) VALUES(nextval('alert_log_id_seq'::regclass), " + str(
            cropGroupID) + ", " + str(selectedAlert) + ", '" + str(username) + "', now(), '" + str(
            username) + "', now());"
        __db_commit_query(queryCreateAlertLog)

    """
    queryCropStageID = " SELECT id, crop_id, stage_name  FROM public.crop_stage where crop_id = "+selectedCrop+" and  stage_name::text like '"+selectedStage+"' "
    getCropStageID = singleValuedQuryExecution(queryCropStageID)
    cropStageID = getCropStageID[0]

    queryGetStageName = "SELECT  stage_name FROM public.crop_stage where  id::text like '"+str(cropStageID)+"'"
    getStageName = singleValuedQuryExecution(queryGetStageName)

    queryCropStageAlertID = "SELECT id FROM public.crop_stage_alert where crop_stage_id =(select id FROM public.crop_stage  where stage_name = '"+str(getStageName[0])+"') and "
    getCropStageAlertID = singleValuedQuryExecution(queryCropStageAlertID)
    """

    return HttpResponseRedirect('/maxmodule/cais_module/alert_sms_process/')


@login_required
def alert_sms_process_Edit(request):
    id = request.POST.get('id')

    queryFetchSelectedAlertSMSProcess = "SELECT id, crop_group_id, crop_stage_alert_id, " \
                                        "(SELECT id FROM public.group_details   where group_name = group_name_id )group_name," \
                                        " (SELECT id FROM public.crop where crop_name = crop_name_id )crop_name, crop_stage, crop_stage_alert_id as alert_name," \
                                        " alert_sms_id FROM public.vwalert_sms_process"

    getFetchSelectedAlertSMSProcess = singleValuedQuryExecution(queryFetchSelectedAlertSMSProcess)

    jsonFetchSelectedAlertSMSProcess = json.dumps({'getFetchSelectedAlertSMSProcess': getFetchSelectedAlertSMSProcess},
                                                  default=decimal_date_default)

    return HttpResponse(jsonFetchSelectedAlertSMSProcess)


"""
@@********************  Alert SMS Process (End) ********************
"""
