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


def batchlist(request,selectedBatchForm,selectedBatchID):
  #  id_string = 'hh_registration'
  #  query = "SELECT id, uuid  FROM logger_xform where id_string = 'hh_registration'"
 #   queryResult = singleValuedQuryExecution(query)

 #   batchDetailsQuery = "SELECT id, batch_id, instance_id,creation_date FROM public.batch_details;"
 #
 #    selectedBatchID = request.POST.get('selecteDbatchID')
 #
 #    print("SELECTED ID ")
 #    print(selectedBatchID)

    username = request.user.username

    queryBatchInfo = "SELECT id  batch_form , batch_form , selected_filter ,  total_data  FROM public.batch_creation where id = " + str(selectedBatchID)
    getBatchInfoList = makeTableList(queryBatchInfo)

    if selectedBatchForm == 'hh_registration':
        subContactPerson = "vwlogger_instance.json->>'respondent_name'Contact_Person"
    elif selectedBatchForm == 'school_registration_form':
        subContactPerson = "vwlogger_instance.json->>'headmaster_name'Contact_Person"


    batchDetailsQuery = "SELECT vwlogger_instance.id Uniqe_ID, "+subContactPerson+",  " \
                    "(select username from public.auth_user where id = vwlogger_instance.user_id) Sender_name , " \
                    "to_char(vwlogger_instance.date_created,'DD Mon YYYY') Collection_Date, app_inst.status Data_Status " \
                    "FROM vwlogger_instance LEFT JOIN approval_instanceapproval app_inst ON " \
                    "app_inst.instance_id = vwlogger_instance.id where xform_id = (select id FROM public.logger_xform where id_string = '"+str(selectedBatchForm)+"') " \
                    "and vwlogger_instance.id = any (SELECT instance_id " \
                    "FROM public.batch_details where batch_id = "+str(selectedBatchID)+" and batch_form =  '"+str(selectedBatchForm)+"')"


    batchDetails = multipleValuedQuryExecution(batchDetailsQuery)

    batchId = "'"+selectedBatchID+"'"
    callCenterbatchDetailsQuery = 'with t as ( select batch_id , batch_details.instance_id, contact_person,  (select username ' \
                    'from public.auth_user where id = sender_or_user_id) sender_or_user_name , creation_date, ' \
                    'batch_form,sender_or_user_id , app_inst.status Data_Status FROM public.batch_details LEFT JOIN public.approval_instanceapproval app_inst' \
                    ' ON batch_details.instance_id = app_inst.instance_id  )select t.* , upload_data.verification_status ' \
                    ' from t left join public."upload_data_CC_verification_store" upload_data' \
                    ' on t.instance_id = upload_data.unique_id  where t.instance_id = any (select unique_id ' \
                    'FROM public."upload_data_CC_verification_store") and ' \
                    't.batch_id::text like ' + batchId + ' '

    callCenterbatchDetails = multipleValuedQuryExecution(callCenterbatchDetailsQuery)

    jsonBatchDetails = json.dumps({'username': username,'batchDetails':batchDetails , 'getBatchInfoList':getBatchInfoList ,'callCenterbatchDetails': callCenterbatchDetails}, default=decimal_date_default)
  #  xform_id = queryResult[0]
  #  form_uuid = str(queryResult[1])

    content = {#'id_string': id_string,
               #'xform_id': xform_id,
               #'form_uuid': form_uuid,
               #'username': username,
               #'getBatchInfoList':getBatchInfoList,
               'jsonBatchDetails':jsonBatchDetails

                }

    return render(request, 'batchmodule/batchlist.html', content)


def batchDetails(request):
    return HttpResponse()

def creatingBatchAndBatchDetails(request):
    batchDataTotal = request.POST.get("dataLength")
    id_string = request.POST.get("id_string")
    pngo = request.POST.get("pngo")
    district = request.POST.get("district")
    upazila = request.POST.get("upazila")
    union = request.POST.get("union")
    ward = request.POST.get("ward")
    village = request.POST.get("village")
    sender = request.POST.get("sender")
    action = request.POST.get("action")
    status = request.POST.get("status")
    collection_from_date = request.POST.get("collecion_from_date")
    collection_to_date = request.POST.get("collecion_to_date")
    submission_from_date = request.POST.get("submission_from_date")
    submission_to_date = request.POST.get("submission_to_date")
    batchname = "BatchName"
    batchStatus = 'New'
    batchForm = id_string

    # *************    Filter for creating  Batch  (Start)***********

    sub_query_pngo = ""
    sub_query_district = ""
    sub_query_upazila = ""
    sub_query_union = ""
    sub_query_ward = ""
    sub_query_village = ""
    sub_query_sender = ""
    sub_query_action = ""
    sub_query_status = ""
    sub_collection_query_date_range = ""
    sub_submission_query_date_range = ""
    selectedFilter = ""

    if pngo != '%':
        sub_query_pngo += " AND vwlogger_instance.user_id = " + str(pngo)
        selectedFilter += "PNGO-"
    if district != '%':
        sub_query_district += " AND vwlogger_instance.json->>'district' = " + str(district)
        selectedFilter += "District-"
    if upazila != '%':
        sub_query_upazila += " AND vwlogger_instance.json->>'upazila' = " + str(upazila)
        selectedFilter += "Upazila-"
    if union != '%':
        sub_query_union += " AND vwlogger_instance.json->>'union_name' = " + str(union)
        selectedFilter += "Union-"
    if ward != '%':
        sub_query_ward += " AND vwlogger_instance.json->>'ward' = " + str(ward)
        selectedFilter += "Ward-"
    if village != '%':
        sub_query_village += " AND vwlogger_instance.json->>'village' = " + str(village)
        selectedFilter += "Village-"
    if sender != '%':
        sub_query_sender += " AND vwlogger_instance.user_id = " + str(sender)
        selectedFilter += "Sender-"
    if action != '%':
        sub_query_action += " AND vwlogger_instance.json->>'village' = " + str(action)
        selectedFilter += "Action-"
    if status != '%':
        sub_query_status += " AND app_inst.status = '" + str(status) + "'"
        selectedFilter += "Status-"

    if collection_from_date != '%' and collection_to_date != '%' and collection_from_date != '' and collection_to_date != '':
        sub_collection_query_date_range += " AND vwlogger_instance.date_created BETWEEN '" + str(
            collection_from_date) + "' AND '" + str(collection_to_date) + "'"
        selectedFilter += "Collection Date-"
    if submission_from_date != '%' and submission_to_date != '%' and submission_from_date != '' and submission_to_date != '':
        sub_submission_query_date_range += " AND vwlogger_instance.date_modified BETWEEN '" + str(
            submission_from_date) + "' AND '" + str(submission_to_date) + "'"
        selectedFilter += "Submission Date-"

    selectedFilter = selectedFilter[:-1]

    # *************    Filter for creating  Batch  (Start)***********


    # For Contact Person Value of Each Form *******

    if id_string == 'hh_registration':
        subContactPerson = "json->>'respondent_name'Contact_Person"
    elif id_string == 'school_registration_form':
        subContactPerson = "json->>'headmaster_name'Contact_Person"


    # Query *********
    batchCreateQuery = "INSERT INTO batch_creation(id, batch_name, pngo_id, district_id, upazila_id, union_id, ward_id, village_id, status, action_batch, sender,collection_from_date," \
                       "collection_to_date,submission_from_date,submission_to_date,batch_status,batch_form,total_data,selected_filter) VALUES(nextval('batch_creation_id_seq'::regclass),'" + batchname + "' , '" + pngo + "', '" + district + "', '" + upazila + "', '" + union + "', '" + ward + "', '" + village + "','" + status + "','" + action + "', '" + sender + "','" + collection_from_date + "','" + collection_to_date + "','" + submission_from_date + "','" + submission_to_date + "','" + batchStatus + "','" + batchForm + "','" + batchDataTotal + "','" + selectedFilter + "');"

    currentCreatedBatchIdQuery = "SELECT id FROM public.batch_creation order by id desc limit 1;"

    createdBatchDataInstanceIdListQuery = "SELECT id , "+subContactPerson+" , user_id FROM public.vwlogger_instance where xform_id = (select id from public.logger_xform where id_string = '" + id_string + "') " + str(
        sub_query_sender) + str(sub_query_pngo) + str(sub_query_district) + str(sub_query_upazila) + str(
        sub_query_union) + str(sub_query_ward) + str(sub_query_village) + str(sub_query_action) + str(
        sub_query_action) + str(sub_query_status) + str(sub_collection_query_date_range) + str(
        sub_submission_query_date_range)


   # Creating Cursor ********

    batchCreateCursor = connection.cursor()
    currentCreatedBatchIdCursor = connection.cursor()
    createdBatchDataInstanceIdListCursor = connection.cursor()
    batchDetailsEntryCursor = connection.cursor()

#   Excetuing Query *********

    batchCreateCursor.execute(batchCreateQuery)

    currentCreatedBatchIdCursor.execute(currentCreatedBatchIdQuery)
    currentCreatedBatchId = currentCreatedBatchIdCursor.fetchone()[0]

    createdBatchDataInstanceIdList = multipleValuedQuryExecution(createdBatchDataInstanceIdListQuery)

    # Inserting into Batch_Details *********

    for index in createdBatchDataInstanceIdList:
        batchDetailsQuery = "INSERT INTO public.batch_details (id, batch_id, instance_id,creation_date,batch_form,contact_person,sender_or_user_id) VALUES(nextval('batch_details_id_seq'::regclass), " + str(
            currentCreatedBatchId) + " ," + str(index[0]) + ",now()::date ,'"+batchForm+"','"+str(index[1])+"',"+str(index[2])+")"
        batchDetailsEntryCursor.execute(batchDetailsQuery)
    return HttpResponse('')


def batchManagement(request):
    queryFormList = " SELECT id, user_id, id_string, title FROM public.logger_xform "
    formList = makeTableList(queryFormList)

    queryBatchDetails = " SELECT id,  batch_name  , batch_status, (select title from public.logger_xform  where  id_string = batch_form) batch_form , total_data, selected_filter FROM public.batch_creation order by id asc;"
    batchDetails = makeTableList(queryBatchDetails)

    queryBatchStatusCount = "with t as (SELECT batch_status , count( batch_status) FROM public.batch_creation group by batch_status) " \
                            "select * , (case " \
                            "when t.batch_status = 'New' then 1 " \
                            "when t.batch_status = 'Assigned to CCA' then 2 " \
                            "when t.batch_status = 'Closed' then 3 " \
                            "end )serial_num from t order by serial_num asc"

    print(queryBatchStatusCount)

    batchStatusCount = makeTableList(queryBatchStatusCount)

    contentList = json.dumps({
        'batchDetails': batchDetails,
    }, default=decimal_date_default)

    content = {
        'formList': formList,
        'batchDetails': batchDetails,
        'batchStatusCount': batchStatusCount,
        'contentList': contentList

    }

    return render(request, 'batchmodule/batchManagement.html', content)

def createBatchManagementList(request):
    formName = request.POST.get("formName")
    batchId = request.POST.get("batchId")
    batchStatus = request.POST.get("batchStatus")

    if(formName != '%'):
        queryBatchDetails = " SELECT id,  batch_name  , batch_status, (select title from public.logger_xform  where  id_string = batch_form) batch_form_name , total_data, selected_filter , batch_form FROM public.batch_creation where batch_form like  (select id_string from  public.logger_xform where id::text like '"+formName+"') and batch_status like '"+batchStatus+"' and id::text like '"+batchId+"' order by id asc;"
    else:
        queryBatchDetails = " SELECT id,  batch_name  , batch_status, (select title from public.logger_xform  where  id_string = batch_form) batch_form_name , total_data, selected_filter, batch_form FROM public.batch_creation where batch_form like '"+formName+"' and batch_status like '"+batchStatus+"' and id::text like '"+batchId+"' order by id asc;"

    batchDetails = makeTableList(queryBatchDetails)
    contentList = json.dumps({
        'batchDetails': batchDetails,
    }, default=decimal_date_default)

    return HttpResponse(contentList,mimetype='text/json')

def getBatchDelete(request):

    selectedBatchId = request.POST.get('selecteDbatchID')

    queryDeleteFromBatchDeatailsTable = "delete FROM public.batch_details where batch_id::text like '"+selectedBatchId+"'"
    queryDeleteFromBatchCreatedTable = "delete  FROM public.batch_creation where id::text like '"+selectedBatchId+"'"

    DeleteFromBatchDeatailsTable = connection.cursor()
    DeleteFromBatchCreatedTable = connection.cursor()

    DeleteFromBatchDeatailsTable.execute(queryDeleteFromBatchDeatailsTable)
    DeleteFromBatchCreatedTable.execute(queryDeleteFromBatchCreatedTable)

    return HttpResponse('')

"""
******************** Import for CC Verification (Start)********************
"""

def importForCCVerification(request):
    queryBatchDetails = " SELECT id,  batch_name  , batch_status, (select title from public.logger_xform  where  id_string = batch_form) batch_form , total_data, selected_filter FROM public.batch_creation order by id asc;"
    batchDetails = makeTableList(queryBatchDetails)
    content = {
        'batchDetails': batchDetails
    }



    return render(request,'batchmodule/importForCCVerification.html',content)

@csrf_exempt
def importDataForVerification(request):
    if request.POST:

        username = request.user.username
        username = "'"+username + "'"
        status = "'" + 'New' + "'"
        verification_status = "'"+'Due'+"'"


        #******** Saving File ********
        myfile = request.FILES['importedFileForCCVerification']
        url = "onadata/media/uploadedFileForCCVerification/"   # saving path
        fs = FileSystemStorage(location=url)
        myfile.name = str(datetime.datetime.now()) + "_" + str(myfile.name)
        filename = fs.save(myfile.name, myfile)
        filename = "'" +filename.encode('ascii','ignore')+"'"

        # ******** Reading File *******
        full_file_path = "onadata/media/uploadedFileForCCVerification/" + myfile.name  # reaading path
        df = pandas.DataFrame()
        xlsx = pandas.ExcelFile(full_file_path)
        df = xlsx.parse(0)
        for each in df.index:
            if str(df.loc[each][0]) != "nan" and str(df.loc[each][1]) != "nan" and str(int(df.loc[each][0])).isdigit() and (str(int(df.loc[each][1])).isdigit()):
                # select_query = "select * FROM public.""import_File_Data_Strore_CC_verification"" where batch_id=" + str(
                #     int(df.loc[each]['batch_id'])) + " and unique_id = '" + str(df.loc[each]['unique_id']) + "'"
                # sf = pandas.DataFrame()
                # sf = pandas.read_sql(select_query, connection)
                # if sf.empty:
                insert_query = 'INSERT INTO public."upload_data_CC_verification_store" (batch_id, unique_id,from_name , user_name , status,verification_status) VALUES('+str(df.loc[each][0])+', '+str(df.loc[each][1])+', '+filename+', '+username+', '+status+', '+verification_status+')'
                __db_commit_query(insert_query)
    return HttpResponseRedirect('/maxmodule/batchmodule/importForCCVerification/')



def importDataForVerificationDelete(request):
    batch_id = request.POST.get('batch_id')
    batch_id = "'"+ batch_id + "'"
    queryDeleteUploadedData = 'DELETE FROM public."upload_data_CC_verification_store" where batch_id = '+ batch_id+''
    __db_commit_query(queryDeleteUploadedData)  ## Function  For Query Execution
    return HttpResponse('')

def importDataForVerificationListCount(request):

    queryGetUpdataFileInfo = 'SELECT  batch_id,  from_name , count(unique_id) FROM public."upload_data_CC_verification_store" group by batch_id , from_name'
    updataFileInfo = makeTableList(queryGetUpdataFileInfo)

    jsonContent = json.dumps({'updataFileInfo':updataFileInfo},default=decimal_date_default)

    return HttpResponse(jsonContent ,mimetype='text/json')


"""
******************** Import for CC Verification (End )********************
"""


"""
************************************* Call Center Verification (Start)***************
"""

def call_center_verification(request):


    print("RMTTTTTTTTTTTTTTTTTTTTTTT")

    submitted = "'"+'Submitted'+"'"
    due = "'"+'Due'+"'"

    submittedStatus = 'select count(verification_status) FROM public."upload_data_CC_verification_store" where verification_status = '+submitted+' '
    deuStatus =  'select count(verification_status) FROM public."upload_data_CC_verification_store" where verification_status = '+due+' '
    totalStatus= 'select count(verification_status) FROM public."upload_data_CC_verification_store" where verification_status is not NULL '

    queryBatchDetails = " SELECT id,  batch_name  , batch_status, (select title from public.logger_xform  where  id_string = batch_form) batch_form , total_data, selected_filter FROM public.batch_creation order by id asc;"
    batchDetails = makeTableList(queryBatchDetails)


    countSubmitStatus = makeTableList(submittedStatus)
    countDueStatus = makeTableList(deuStatus)
    countTotalStatus = makeTableList(totalStatus)



   # queryBatchStatusCount = 'with t as(SELECT verification_status , count( verification_status) FROM public."upload_data_CC_verification_store" where verification_status is not NULL  group by verification_status) select * , (case when t.verification_status = '+submitted+' then 1 when t.verification_status = '+deu+' then 2 end )serial_num from t order by serial_num asc'
   # batchStatusCount = makeTableList(queryBatchStatusCount)

    contentList = json.dumps({
        'batchDetails': batchDetails,
    }, default=decimal_date_default)

    content = {
        'batchDetails': batchDetails,
        'countSubmitStatus':countSubmitStatus,
        'countDueStatus':countDueStatus,
        'countTotalStatus':countTotalStatus,
      # 'batchStatusCount': batchStatusCount,
        'contentList': contentList

    }

    return render(request, 'batchmodule/call_center_verification.html', content)


def callCenterlist(request):

    print("ENTERRRRRRRRRRRR")

    batchId = request.POST.get('batchId')
    verificationStatus = request.POST.get('verificationStatus')

    batchId = "'"+ batchId +"'"
    verificationStatus = "'"+ verificationStatus + "'"

    batchDetailsQuery = 'with t as ( select batch_id , batch_details.instance_id, contact_person,  (select username ' \
                        'from public.auth_user where id = sender_or_user_id) sender_or_user_name , creation_date, ' \
                        'batch_form,sender_or_user_id , app_inst.status Data_Status FROM public.batch_details LEFT JOIN public.approval_instanceapproval app_inst' \
                        ' ON batch_details.instance_id = app_inst.instance_id  )select t.* , upload_data.verification_status ' \
                        ' from t left join public."upload_data_CC_verification_store" upload_data' \
                        ' on t.instance_id = upload_data.unique_id  where t.instance_id = any (select unique_id ' \
                        'FROM public."upload_data_CC_verification_store") and ' \
                        't.batch_id::text like '+batchId+' and upload_data.verification_status like '+verificationStatus+' '

    batchDetails = multipleValuedQuryExecution(batchDetailsQuery)
    jsonBatchDetails = json.dumps({'batchDetails': batchDetails},default=decimal_date_default)


    print("jsonBatchDetails")
    print(jsonBatchDetails)

    return HttpResponse(jsonBatchDetails, mimetype='text/json' )

"""
************************************* Call Center Verification (End)****************
"""

"""
************************************* Info Chencking Page for Call Center(Start)**************
"""

def call_center_id_info_checking_page(request,selectedID):

    content= {
        'selectedID':selectedID

    }
    return render(request, 'batchmodule/call_center_id_info_checking_page.html' , content)


"""
************************************* Info Chencking Page for Call Center(End)**************
"""
