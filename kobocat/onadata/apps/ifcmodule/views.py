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
import os


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
    return render(request, 'ifcmodule/add_program_form.html',{'organization': organization})


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
                  {'organization':organization,'set_org_id':set_org_id,
                   'program_id':program_id,'program_name':program_name
                    })


@login_required
def update_program_form(request):
    if request.POST:
        program_id = request.POST.get('program_id')
        program = request.POST.get('program')
        org_id = request.POST.get('org_id')
        update_query = "UPDATE public.usermodule_programs SET program_name='" + str(program) + "', org_id=" + str(org_id) + "  WHERE id=" + str(program_id)
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