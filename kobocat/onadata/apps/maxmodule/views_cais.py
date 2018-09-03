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
    value = list(cursor.fetchone())
    cursor.close()
    return value


def multipleValuedQuryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchall()
    cursor.close()
    return value


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
@@ **************  Crop (Start)
"""
@login_required
def crop(request):

    queryCropNameList = 'SELECT id, crop_name FROM public.crop order by id'
    cropNameList = multipleValuedQuryExecution(queryCropNameList)
    jsonCropNameList = json.dumps({'cropNameList':cropNameList},default=decimal_date_default)

    content = {

        'jsonCropNameList':jsonCropNameList
    }

    return render(request,'cais_module/crop.html',content)

@login_required
def cropCreate(request):
    username = request.user.username
    cropName = request.POST.get('crop_name', '')
    isEdit = request.POST.get('isEdit')

    if isEdit !='':
        queryEditCropName = "UPDATE public.crop SET crop_name='"+cropName+"' WHERE id= "+isEdit
        __db_commit_query(queryEditCropName)  ## Query Execution Function
    else:
        queryCreateCropName = "INSERT INTO public.crop (id, crop_name, created_at, created_by, updated_at, updated_by)VALUES(nextval('crop_id_seq'::regclass),'"+str(cropName)+"', now(), '"+str(username)+"', now(), '"+str(username)+"')"
        __db_commit_query(queryCreateCropName) ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/crop/')


@login_required
def crop_Edit(request):
    id = request.POST.get('id')
    queryFetchSpecificCrop = " SELECT id,crop_name FROM public.crop where id = "+str(id)
    getFetchSpecificCrop = singleValuedQuryExecution(queryFetchSpecificCrop)

    jsonFetchSpecificCrop = json.dumps({'getFetchSpecificCrop':getFetchSpecificCrop},default=decimal_date_default)

    return HttpResponse(jsonFetchSpecificCrop)

"""
@@ **************  Crop (End)
"""

"""
@@ **************  Crop Stage (Start) ***********@@
"""

@login_required
def crop_Stage (request):

    queryCropNameList = 'SELECT id, crop_name FROM public.crop order by id'
    cropNameList = multipleValuedQuryExecution(queryCropNameList)

    queryCropStageInfoList = 'SELECT id, (select crop_name from public.crop where id = crop_id )crop_name, stage_name, start_day, end_day FROM public.crop_stage order by id'
    cropStageInfoList = multipleValuedQuryExecution(queryCropStageInfoList)

    jsonCropStageInfoList = json.dumps({'cropStageInfoList':cropStageInfoList},default=decimal_date_default)
    content = {
        'cropNameList':cropNameList,
        'jsonCropStageInfoList':jsonCropStageInfoList
    }
    return render(request,'cais_module/crop_Stage.html',content)


@login_required
def cropStageCreate(request):
    username = request.user.username
    crop_id = request.POST.get('crop_id', '')
    stage_name = request.POST.get('stage_name', '')
    start_day = request.POST.get('start_day', '')
    end_day = request.POST.get('end_day', '')
    isEdit = request.POST.get('isEdit')

    if isEdit !='':
        queryEditCropStage = "UPDATE public.crop_stage SET crop_id= "+str(crop_id)+", stage_name='"+str(stage_name)+"', start_day= "+str(start_day)+", end_day= "+str(end_day)+"  WHERE id= "+str(isEdit)
        __db_commit_query(queryEditCropStage)  ## Query Execution Function
    else:
        queryCreateCropStage =  "INSERT INTO public.crop_stage (id, crop_id, stage_name, start_day, end_day, created_at, created_by, updated_at, updated_by) VALUES(nextval('crop_stage_id_seq'::regclass), "+str(crop_id)+", '"+str(stage_name)+"', "+str(start_day)+", "+str(end_day)+", now(), '"+str(username)+"', now(), '"+str(username)+"'); "
        __db_commit_query(queryCreateCropStage) ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/crop_Stage/')

@login_required
def crop_Stage_Edit(request):

    id = request.POST.get('id')


    queryFetchSelecteCropStage = "SELECT id, crop_id, stage_name, start_day, end_day  FROM public.crop_stage where id = "+str(id)
    getFetchSelecteCropStage = singleValuedQuryExecution(queryFetchSelecteCropStage)

    jsonFetchSelecteCropStage = json.dumps({'getFetchSelecteCropStage': getFetchSelecteCropStage}, default=decimal_date_default)
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

    jsonCropVarietyInfoList = json.dumps({'cropVarietyInfoList':cropVarietyInfoList},default=decimal_date_default)
    content = {
        'cropNameList':cropNameList,
        'jsonCropVarietyInfoList':jsonCropVarietyInfoList
    }
    return render(request,'cais_module/crop_variety.html',content)


@login_required
def cropVarietyCreate(request):
    username = request.user.username
    crop_id = request.POST.get('crop_id', '')
    variety_name = request.POST.get('variety_name', '')
    isEdit = request.POST.get('isEdit')

    if isEdit !='':
        queryEditCropStage = "UPDATE public.crop_variety SET crop_id= "+str(crop_id)+", variety_name='"+str(variety_name)+"'  WHERE id= "+str(isEdit)
        __db_commit_query(queryEditCropStage)  ## Query Execution Function
    else:
        queryCreateCropVariety =  "INSERT INTO public.crop_variety (id, crop_id, variety_name, created_at, created_by, updated_at, updated_by) VALUES(nextval('crop_variety_id_seq'::regclass), "+str(crop_id)+", '"+str(variety_name)+"', now(), '"+str(username)+"', now(), '"+str(username)+"'); "
        __db_commit_query(queryCreateCropVariety) ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/crop_variety/')

@login_required
def crop_variety_Edit(request):

    id = request.POST.get('id')


    queryFetchSelecteCropVariety = "SELECT id, crop_id, variety_name  FROM public.crop_variety where id = "+str(id)
    getFetchSelecteCropVariety = singleValuedQuryExecution(queryFetchSelecteCropVariety)

    jsonFetchSelecteCropVariety = json.dumps({'getFetchSelecteCropVariety': getFetchSelecteCropVariety}, default=decimal_date_default)
    return HttpResponse(jsonFetchSelecteCropVariety)


"""
@@ **************  Crop Variety (End) ***********@@
"""




"""
@@ **************  Crop Stage Alert(End) ***********@@
"""

@login_required
def crop_stage_alert (request):


    queryCropNameList = "SELECT id, crop_name FROM public.crop"
    cropNameList = multipleValuedQuryExecution(queryCropNameList)

    queryCropStageAletrInfoList = 'SELECT id, (select crop_name from public.crop where id =  (select crop_id from public.crop_stage where id = crop_stage_id) )crop , (select stage_name from public.crop_stage where id = crop_stage_id )crop_stage, alert_name, alert_sms FROM public.crop_stage_alert order by id'

    cropStageAlertInfoList = multipleValuedQuryExecution(queryCropStageAletrInfoList)

    jsonCropStageAlertInfoList = json.dumps({'cropStageAlertInfoList':cropStageAlertInfoList},default=decimal_date_default)
    content = {
        'cropNameList':cropNameList,
        'jsonCropStageAlertInfoList':jsonCropStageAlertInfoList
    }
    return render(request,'cais_module/crop_stage_alert.html',content)

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
        queryEditCropStageAlert = "UPDATE public.crop_stage_alert SET crop_stage_id= "+crop_stage_id+", alert_name='"+alert_name+"', alert_sms='"+alert_sms+"' WHERE id= "+ str(isEdit)
        __db_commit_query(queryEditCropStageAlert)  ## Query Execution Function
    else:
        queryCreateCropStageAlert =  "INSERT INTO public.crop_stage_alert (id, crop_stage_id, alert_name, alert_sms, created_at, created_by, updated_at, updated_by) VALUES(nextval('crop_stage_alert_id_seq'::regclass), "+str(crop_stage_id)+", '"+str(alert_name)+"', '"+str(alert_sms)+"', now(), '"+str(username)+"', now(), '"+str(username)+"') "
        __db_commit_query(queryCreateCropStageAlert) ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/crop_stage_alert/')

@login_required
def alert_sms_stage_list(request):
    crop = request.POST.get('crop', '')
    queryCropStageList = 'SELECT id, stage_name FROM public.crop_stage where crop_id = '+str(crop)
    cropStageList = multipleValuedQuryExecution(queryCropStageList)
    jsonCropStageList = json.dumps({'cropStageList':cropStageList},default=decimal_date_default)
    return HttpResponse(jsonCropStageList)


@login_required
def crop_stage_alert_Edit(request):
    id = request.POST.get('id')

    queryFetchSelecteCropStageAlert = "SELECT id, (select crop_id from public.crop_stage where id = crop_stage_id )crop_name_selected_id , crop_stage_id, alert_name, alert_sms FROM public.crop_stage_alert where id = "+id
    getFetchSelecteCropStageAlert = singleValuedQuryExecution(queryFetchSelecteCropStageAlert)

    jsonFetchSelecteCropStageAlert = json.dumps({'getFetchSelecteCropStageAlert':getFetchSelecteCropStageAlert},default=decimal_date_default)
    return HttpResponse(jsonFetchSelecteCropStageAlert)

"""
@@ **************  Crop Stage Alert(End) ***********@@
"""

"""
@@ **************  Group (Start)
"""

@login_required
def group_details(request):

    queryGroupNameList = 'SELECT id, group_name FROM public.group_details order by id'
    groupNameList = multipleValuedQuryExecution(queryGroupNameList)
    jsonGroupNameList = json.dumps({'groupNameList':groupNameList},default=decimal_date_default)

    content = {

        'jsonGroupNameList':jsonGroupNameList
    }

    return render(request,'cais_module/group_details.html',content)

@login_required
def groupCreate(request):
    username = request.user.username
    groupName = request.POST.get('group_name', '')
    isEdit = request.POST.get('isEdit')
    if isEdit !='':
        queryEditGroupName = "UPDATE public.group_details SET group_name='"+groupName+"' WHERE id= "+str(isEdit)
        __db_commit_query(queryEditGroupName)  ## Query Execution Function
    else:
        queryCreateGroupName = "INSERT INTO public.group_details (group_name, created_at, created_by, updated_at, updated_by) VALUES('"+str(groupName)+"', now(), '"+str(username)+"', now(), '"+str(username)+"')"
        __db_commit_query(queryCreateGroupName) ## Query Execution Function

    return HttpResponseRedirect('/maxmodule/cais_module/group_details/')

@login_required
def group_details_Edit(request):
    id = request.POST.get('id')
    queryFetchSpecificGroup = " SELECT id, group_name FROM public.group_details where id = "+str(id)
    getFetchSpecificGroup = singleValuedQuryExecution(queryFetchSpecificGroup)

    jsonFetchSpecificGroup = json.dumps({'getFetchSpecificGroup':getFetchSpecificGroup},default=decimal_date_default)

    return HttpResponse(jsonFetchSpecificGroup)

"""
@@ **************  Group (End)
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

    jsonCropGroupInfoList = json.dumps({'cropGroupInfoList':cropGroupInfoList},default=decimal_date_default)
    content = {
        'groupNameList':groupNameList,
        'cropNameList':cropNameList,
        'seasonList':seasonList,
        'jsonCropGroupInfoList':jsonCropGroupInfoList
    }

    return render(request,'cais_module/crop_group.html',content)


@login_required
def cropGroupCreate(request):

    username = request.user.username
    group_id = request.POST.get('group_id', '')
    crop_id = request.POST.get('crop_id', '')
    sowing_data = request.POST.get('sowing_data', '')
    season_id = request.POST.get('season_id', '')
    isEdit = request.POST.get('isEdit')
    if isEdit != '':
        queryEditCropGroup = "UPDATE public.crop_group SET group_id= "+group_id+", crop_id= "+crop_id+", sowing_date='"+sowing_data+"', season_id="+season_id+" WHERE id= "+ str(isEdit)
        __db_commit_query(queryEditCropGroup)  ## Query Execution Function
    else:
        queryCreateCropGroup = "INSERT INTO public.crop_group (id, group_id, crop_id, sowing_date, season_id, created_at, created_by, updated_at, updated_by) VALUES(nextval('crop_group_id_seq'::regclass), "+str(group_id)+", "+str(crop_id)+", '"+str(sowing_data)+"', "+str(season_id)+", now(), '"+str(username)+"', now(), '"+str(username)+"');"
        __db_commit_query(queryCreateCropGroup)

    return HttpResponseRedirect('/maxmodule/cais_module/crop_group/')

@login_required
def crop_group_Edit(request):
    id = request.POST.get('id')

    queryFetchSelectedCropGroup = "SELECT id, group_id, crop_id, sowing_date, season_id  FROM public.crop_group where id = "+str(id);
    getFetchSelectedCropGroup = singleValuedQuryExecution(queryFetchSelectedCropGroup)

    jsonFetchSelectedCropGroup = json.dumps({'getFetchSelectedCropGroup':getFetchSelectedCropGroup},default=decimal_date_default)
    return HttpResponse(jsonFetchSelectedCropGroup)

"""
@@ ************** Crop Group (End)
"""


"""
@@ ************** Farmer (Start)
"""

@login_required
def farmer(request):

    print("Enter ")

    queryCreateFarmer = 'SELECT id, farmer_name, mobile_number, ' \
                        '(SELECT "name" FROM public.geo_district where id = district_id )district_name, (SELECT "name" FROM public.geo_upazilla where id = upazila_id )upazila_name, ' \
                        '(SELECT "name" FROM public.geo_union where id = union_id )union_name, (SELECT organization FROM public.usermodule_organizations where id = organization_id )organization_name , ' \
                        ' (SELECT program_name FROM public.usermodule_programs where id = program_id) program_name  FROM public.farmer order by id desc '
    farmerInfoList = multipleValuedQuryExecution(queryCreateFarmer)

##  Get Geo District List
    disQuery = "select id,name from public.geo_district"
    dist_List = makeTableList(disQuery)

    ##  Get Organization  List
    organizationQuery = "select id,organization from public.usermodule_organizations"
    organization_List = makeTableList(organizationQuery)

    jsonFarmerInfoList = json.dumps({'farmerInfoList':farmerInfoList},default=decimal_date_default)

    content = {
      'jsonFarmerInfoList':jsonFarmerInfoList,
      'dist_List':dist_List,
      'organization_List':organization_List
    }


    return render(request,'cais_module/farmer.html',content)

@login_required
def farmerCreate(request):

    username = request.user.username
    farmer_name = request.POST.get('farmer_name', '')
    mobile_num = request.POST.get('mobile_num', '')
    district_id = request.POST.get('district_id', '')
    upazila_id = request.POST.get('upazila_id', '')
    union_id = request.POST.get('union_id', '')
    organization_id = request.POST.get('organization_id', '')
    program_id = request.POST.get('program_id', '')

    isEdit = request.POST.get('isEdit')
    if isEdit != '':
        queryEditFarmer = "UPDATE public.farmer SET farmer_name='"+farmer_name+"', district_id= "+district_id+", upazila_id= "+upazila_id+", union_id="+union_id+", program_id="+program_id+", organization_id = "+ organization_id +" , mobile_number='"+mobile_num+"' WHERE id= "+str(isEdit)
        __db_commit_query(queryEditFarmer)
    else:
        queryCreateCropGroup = "INSERT INTO public.farmer(id, farmer_name, district_id, upazila_id, union_id,  organization_id , program_id , mobile_number, created_at, created_by, updated_at, updated_by) VALUES(nextval('farmer_id_seq'::regclass), '"+str(farmer_name)+"', "+str(district_id)+", "+str(upazila_id)+", "+str(union_id)+", "+str(organization_id)+","+str(program_id)+", '"+str(mobile_num)+"', now(), '"+str(username)+"', now(), '"+str(username)+"');"
        __db_commit_query(queryCreateCropGroup)

    return HttpResponseRedirect('/maxmodule/cais_module/farmer/')

@login_required
def farmer_Edit(request):
    id = request.POST.get('id')

    queryFetchSelectedFarmer = "SELECT id, farmer_name, district_id, upazila_id, union_id, organization_id, program_id , mobile_number FROM public.farmer where id = "+str(id) ;
    getFetchSelectedFarmer = singleValuedQuryExecution(queryFetchSelectedFarmer)

    upazilaQuery = "select id,name from geo_upazilla where geo_district_id =" + str(getFetchSelectedFarmer[2])
    upazila_List = makeTableList(upazilaQuery)
    #jsonUpaList = json.dumps({'upazila_List': upazila_List}, default=decimal_date_default)

    unionQuery = "select id,name from geo_union where geo_upazilla_id = " + str(getFetchSelectedFarmer[3])
    union_List = makeTableList(unionQuery)
    #jsonUnionList = json.dumps({'union_List': union_List}, default=decimal_date_default)

    programQuery = "select id, program_name from usermodule_programs where org_id =" + str(getFetchSelectedFarmer[5])
    program_List = makeTableList(programQuery)
    #jsonProgramList = json.dumps({'program_List': program_List}, default=decimal_date_default)


    jsonFetchSelectedFarmer = json.dumps({'getFetchSelectedFarmer':getFetchSelectedFarmer,
                                          'upazila_List':upazila_List,
                                          'union_List':union_List,
                                          'program_List':program_List
                                          },default=decimal_date_default)
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

    queryCropGroupList = "SELECT id FROM public.crop_group"
    getCropGroupList = makeTableList(queryCropGroupList)

    queryIncludedGroupListInCropGroup = "SELECT distinct(group_id) , (select group_name FROM public.group_details where id = group_id ) group_id_name FROM public.crop_group"
    getIncludedGroupListInCropGroup = makeTableList(queryIncludedGroupListInCropGroup)


    queryCreateFarmerGroup = " SELECT id, (SELECT farmer_name FROM public.farmer where id =farmer_id)farmer_name," \
                             "(select group_name FROM public.group_details where id = (SELECT group_id FROM public.crop_group where id = crop_group_id )) group_name, " \
                             "(select crop_name FROM public.crop where id = (SELECT crop_id FROM public.crop_group where id = crop_group_id )) crop, " \
                             "crop_group_id FROM public.farmer_group order by id "
    farmerGroupInfoList = multipleValuedQuryExecution(queryCreateFarmerGroup)




    jsonFarmerGroupInfoList = json.dumps({'farmerGroupInfoList':farmerGroupInfoList},default=decimal_date_default)


    content = {

        'getFarmerList':getFarmerList,
        'getCropGroupList':getCropGroupList,
        'jsonFarmerGroupInfoList':jsonFarmerGroupInfoList,
        'getIncludedGroupListInCropGroup':getIncludedGroupListInCropGroup
    }


    return render(request, 'cais_module/farmer_group.html',content)

@login_required
def includedGroupCropList(request):

    selectedGroup_name_id = request.POST.get('group_name_id')
    querySelectedGroupCropList = "SELECT id , group_id, (select crop_name FROM public.crop where id = crop_id)crop_id_name FROM public.crop_group where group_id = "+ str(selectedGroup_name_id)
    getSelectedGroupCropList = multipleValuedQuryExecution(querySelectedGroupCropList)
    jsonSelectedGroupCropList = json.dumps({'getSelectedGroupCropList':getSelectedGroupCropList},default=decimal_date_default)
    return HttpResponse(jsonSelectedGroupCropList)

@login_required
def groupNameForEdit(request):

    selectedCrop_group_id = request.POST.get('crop_group_id')
    querySelectedGroup = "SELECT id , group_id FROM public.crop_group where id = "+ str(selectedCrop_group_id)
    getSelectedGroup = singleValuedQuryExecution(querySelectedGroup)
    jsonSelectedGroup = json.dumps({'getSelectedGroupList':getSelectedGroup},default=decimal_date_default)

    return HttpResponse(jsonSelectedGroup)

@login_required
def groupCropNameForEdit(request):

    selectedCrop_group_id = request.POST.get('crop_group_id')
    selectedGroupId = request.POST.get('group_name_id')
    querySelectedGroup = "SELECT id , group_id , (select crop_name FROM public.crop where id = crop_id)crop_id_name  FROM public.crop_group where id = "+ str(selectedCrop_group_id)+" and group_id = " + str(selectedGroupId)
    getSelectedCrop = singleValuedQuryExecution(querySelectedGroup)
    jsonSelectedCrop = json.dumps({'getSelectedCrop':getSelectedCrop},default=decimal_date_default)

    return HttpResponse(jsonSelectedCrop)

@login_required
def farmer_groupCreate(request):
    username = request.user.username
    farmer_id = request.POST.get('farmer_id')

    #crop_group_id = request.POST.get('crop_group_id')

    # Value of this field is Crop Group ID
    crop_group_id = request.POST.get('crop_id')
    isEdit = request.POST.get('isEdit')
    if isEdit != '':
        queryEditFarmerGroup = "UPDATE public.farmer_group SET farmer_id= "+farmer_id+", crop_group_id= "+crop_group_id+"  WHERE id= "+ str(isEdit)
        __db_commit_query(queryEditFarmerGroup)
    else:
        queryCreateFarmerGroup = "INSERT INTO public.farmer_group (id, farmer_id, crop_group_id, created_at, created_by, updated_at, updated_by) VALUES(nextval('farmer_group_id_seq'::regclass), "+str(farmer_id)+", "+str(crop_group_id)+", now(), '"+str(username)+"', now(), '"+str(username)+"')"
        __db_commit_query(queryCreateFarmerGroup)


    return HttpResponseRedirect('/maxmodule/cais_module/farmer_group/')

@login_required
def farmer_group_Edit(request):
    id = request.POST.get('id')

    queryFetchSelectedFarmerGroup = "SELECT id, farmer_id, crop_group_id  FROM public.farmer_group  where id = "+str(id)
    getFetchSelectedFarmerGroup = singleValuedQuryExecution(queryFetchSelectedFarmerGroup)

    jsonqueryFetchSelectedFarmerGroup = json.dumps({'getFetchSelectedFarmerGroup':getFetchSelectedFarmerGroup},default=decimal_date_default)

    return HttpResponse(jsonqueryFetchSelectedFarmerGroup)

"""
@@ ************** Farmer Group (End)
"""

"""
@@*************************** Get Geo Location (Start) **************************
"""
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
        'jsonCropList':jsonCropList

    }
    return render(request,'cais_module/alert_sms_process.html',content);

@login_required
def alert_sms_process_crop_list(request):
    selectedGroup = request.POST.get('group')
    cropQuery = "SELECT crop_id, (SELECT crop_name FROM public.crop where id = crop_id ) crop_name , date_part('day', date (sowing_date) )sowing_date FROM public.crop_group where group_id = " + str(selectedGroup)
    crop_List = makeTableList(cropQuery)
    jsonCropList = json.dumps({'crop_List': crop_List}, default=decimal_date_default)
    return HttpResponse(jsonCropList)

@login_required
def alert_sms_process_stage_name(request):
    selectedGroup = request.POST.get('group')
    selectedCrop = request.POST.get('crop')

  #  stageQuery = "SELECT stage_name, start_day, end_day  FROM public.crop_stage where crop_id = "+ selectedCrop;

    #stageQuery ="with w as ( " \
     #           "with t as (" \
     #           "SELECT id, group_id, crop_id, date_part('day' , date(sowing_date)) sowing_date " \
     #           "FROM public.crop_group where group_id = "+str(selectedGroup)+" and crop_id = "+str(selectedCrop)+") " \
     #          "select t.* , s.stage_name , s.start_day, s.end_day from t left join public.crop_stage s on t.crop_id = s.crop_id )" \
     #           "select stage_name from w  where sowing_date between start_day and end_day"

    stageQuery ="with t as(SELECT (now()::date-sowing_date::date) age FROM crop_group where group_id="+str(selectedGroup)+" and crop_id="+str(selectedCrop)+"),t1 as(SELECT crop_id, stage_name, start_day, end_day FROM crop_stage where crop_id="+str(selectedCrop)+")select stage_name   from t1,t where t.age between start_day and end_day"


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

    print("selectedCrop")
    print(selectedCrop)

    alertQuery = "SELECT id, alert_name FROM public.crop_stage_alert where crop_stage_id = any(select id FROM public.crop_stage where stage_name::text like '"+str(selectedStage)+"' and crop_id::text like '"+str(selectedCrop)+"' )";
    print("alertQuery")
    print(alertQuery)

    alertList = makeTableList(alertQuery)
    jsonAlertList = json.dumps({'alertList': alertList}, default=decimal_date_default)


    print("Alert_List")
    print(jsonAlertList)

    return HttpResponse(jsonAlertList)

@login_required
def alert_sms_process_alert_sms(request):
    selectedAlert = request.POST.get('alert_name')
    alertSmsQuery = "SELECT id, alert_name,  alert_sms FROM public.crop_stage_alert where id = "+str(selectedAlert)+" " ;
    alertSMSList = makeTableList(alertSmsQuery)
    jsonAlertSMSList = json.dumps({'alertSMS': alertSMSList}, default=decimal_date_default)
    return HttpResponse(jsonAlertSMSList)

@login_required
def alert_sms_process_info_store(request):
    username = request.user.username

    selectedGroup = request.POST.get('group_id','')
    selectedCrop = request.POST.get('crop_id','')
    selectedStage = request.POST.get('stage_name','')
    selectedAlert = request.POST.get('alert_id','')
    selectedAlertSMS = request.POST.get('alert_sms','')

    isEdit = request.POST.get('isEdit')


    queryCropGroupID = "SELECT id, group_id, crop_id FROM public.crop_group where group_id = "+str(selectedGroup)+" and crop_id = "+str(selectedCrop) ;
    getCropGroupID  = singleValuedQuryExecution(queryCropGroupID)
    cropGroupID = getCropGroupID[0]


    if isEdit != '':
        queryEditAlertLog= "UPDATE public.alert_log SET crop_group_id= "+str(cropGroupID)+", crop_stage_alert_id= "+str(selectedAlert)+" WHERE id= "+ str(isEdit)
        __db_commit_query(queryEditAlertLog)
    else:
        queryCreateAlertLog = "INSERT INTO public.alert_log (id, crop_group_id, crop_stage_alert_id, created_by, created_at, updated_by, updated_at) VALUES(nextval('alert_log_id_seq'::regclass), "+str(cropGroupID)+", "+str(selectedAlert)+", '"+str(username)+"', now(), '"+str(username)+"', now());"
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

    jsonFetchSelectedAlertSMSProcess = json.dumps({'getFetchSelectedAlertSMSProcess':getFetchSelectedAlertSMSProcess},default=decimal_date_default)

    return HttpResponse(jsonFetchSelectedAlertSMSProcess)
"""
@@********************  Alert SMS Process (End) ********************
"""

