from collections import OrderedDict
import datetime
import os
import csv
import xml.etree.ElementTree as ET
import dateutil.parser
import requests
import json
import pandas as pd
import pandas

from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib import messages


def __db_fetch_values(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = cursor.fetchall()
    cursor.close()
    return fetch_val


def __db_fetch_single_value(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = cursor.fetchone()
    cursor.close()
    return fetch_val[0]


def __db_commit_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    fetch_val = cursor.fetchone()
    cursor.close()
    return fetch_val[0]


def __db_fetch_values_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = dictfetchall(cursor)
    cursor.close()
    return fetch_val


def __db_commit_query_void(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


@csrf_exempt
def get_daily_weather_information(request,type,from_date,to_date,location):
    if "HTTP_TOKEN" in request.META:
        token = request.META['HTTP_TOKEN']
        check_query = "select * from authtoken_token where key='"+str(token)+"'"
        df = pandas.DataFrame()
        df = pandas.read_sql(check_query,connection)
        if df.empty:
            return HttpResponse(json.dumps({'message': 'Access Denied'}))
    else:
        return HttpResponse(json.dumps({'message': 'Token Needed'}))

    try:
        datetime.datetime.strptime(from_date, '%Y-%m-%d')
        datetime.datetime.strptime(to_date, '%Y-%m-%d')
    except ValueError:
        return HttpResponse(json.dumps({'message': 'Wrong Date Format'}))
    else:
        if from_date > to_date:
            return HttpResponse(json.dumps({'message': 'First date must be less or equal than Last date'}))    
        if type == 'forecast':
            if location == 'np':
                weather_forecast_data = __db_fetch_values_dict(
                    "with t as(select * from weather_forecast where place_id = any(select place_id from union_place_station_mapping where union_id = any(select id from vwunion where geo_country_id = 2)) and DATE(date_time) between DATE('" + str(
                        from_date) + "') and DATE('" + str(to_date) + "')) select 'Nepal' as country, DATE(date_time) as currentdate,TRUNC(max(temperature::float)::numeric,1)::text as max_temperature,TRUNC(min(temperature::float)::numeric,1)::text as min_temperature, TRUNC(max(wind_speed::float)::numeric,1)::text as wind_speed, TRUNC(max(humidity::float)::numeric,1)::text as max_humidity, TRUNC(min(humidity::float)::numeric,1)::text as min_humidity,TRUNC(sum(rainfall::float)::numeric,1)::text as rainfall from t group by DATE(date_time) order by DATE(date_time) asc")
            elif location == 'bd':
                weather_forecast_data = __db_fetch_values_dict(
                    "with t as(select * from weather_forecast where place_id = any(select place_id from union_place_station_mapping where union_id = any(select id from vwunion where geo_country_id = 1)) and DATE(date_time) between DATE('" + str(
                        from_date) + "') and DATE('" + str(to_date) + "')) select 'Bangladesh' as country, DATE(date_time) as currentdate,TRUNC(max(temperature::float)::numeric,1)::text as max_temperature, TRUNC(min(temperature::float)::numeric,1)::text as min_temperature, TRUNC(max(wind_speed::float)::numeric,1)::text as wind_speed, TRUNC(max(humidity::float)::numeric,1)::text as max_humidity, TRUNC(min(humidity::float)::numeric,1)::text as min_humidity,TRUNC(sum(rainfall::float)::numeric,1)::text as rainfall from t group by DATE(date_time) order by DATE(date_time) asc")
            else:
                return HttpResponse(json.dumps({'message': 'Wrong country parameter'}))

            final_data = {}
            final_data['data'] = weather_forecast_data
            final_data['units'] = {"country": "N/A", "rainfall": "mm", "currentdate": "N/A",
                                   "max_temperature": "Degree celsius", "min_temperature": "Degree celsius",
                                   "wind_speed": "m/s", "max_humidity": "Percent(%)", "min_humidity": "Percent(%)"}
            return HttpResponse(json.dumps(final_data, default=default))
        elif type == 'observed':
            if location == 'np':
                weather_observed_data = __db_fetch_values_dict("with t as( select * from weather_observed where station_id::int = any( select station_id from union_place_station_mapping where union_id = any(select id from vwunion where geo_country_id = 2)) and date_time::date between '" + str(from_date) + "' and '" + str(to_date) + "' )select 'Nepal' as country, DATE(date_time) as currentdate, TRUNC(max(temperature::float)::numeric,1)::text as max_temperature, TRUNC(min(temperature::float)::numeric,1)::text as min_temperature, TRUNC(avg(temperature::float)::numeric,1)::text as avg_temperature, TRUNC(max(humidity::float)::numeric,1)::text  as max_humidity, TRUNC(min(humidity::float)::numeric,1)::text as min_humidity, TRUNC(sum(rainfall::float)::numeric,1)::text as rainfall, TRUNC(max(wind_speed::float)::numeric,1)::text as wind_speed,TRUNC(sum(solar_radiation::float)::numeric,1)::text as solar_radiation from t group by DATE(date_time) order by DATE(date_time) asc")
            elif location == 'bd':
                weather_observed_data = __db_fetch_values_dict("with t as( select * from weather_observed where station_id::int = any( select station_id from union_place_station_mapping where union_id = any(select id from vwunion where geo_country_id = 1)) and date_time::date between '" + str(from_date) + "' and '" + str(to_date) + "' )select 'Bangladesh' as country, DATE(date_time) as currentdate, TRUNC(max(temperature::float)::numeric,1)::text as max_temperature, TRUNC(min(temperature::float)::numeric,1)::text as min_temperature, TRUNC(avg(temperature::float)::numeric,1)::text  as avg_temperature, TRUNC(max(humidity::float)::numeric,1)::text as max_humidity, TRUNC(min(humidity::float)::numeric,1)::text as min_humidity, TRUNC(sum(rainfall::float)::numeric,1)::text as rainfall, TRUNC(max(wind_speed::float)::numeric,1)::text as wind_speed, TRUNC(sum(solar_radiation::float)::numeric,1)::text as solar_radiation from t group by DATE(date_time) order by DATE(date_time) asc")
            else:
                return HttpResponse(json.dumps({'message': 'Wrong country parameter'}))
            final_data = {}
            final_data['data'] = weather_observed_data
            final_data['units'] = {"country": "N/A", "rainfall": "mm", "currentdate": "N/A",
                                   "max_temperature": "Degree celsius", "min_temperature": "Degree celsius","avg_temperature": "Degree celsius",
                                   "wind_speed": "m/s", "max_humidity": "Percent(%)", "min_humidity": "Percent(%)","solar_radiation": "j/m2"}
            return HttpResponse(json.dumps(final_data, default=default))
        else:
            return HttpResponse(json.dumps({'message': 'Wrong type parameter'}))


@csrf_exempt
def get_hourly_weather_information(request, type, from_date,to_date, location):
    if "HTTP_TOKEN" in request.META:
        token = request.META['HTTP_TOKEN']
        check_query = "select * from authtoken_token where key='"+str(token)+"'"
        df = pandas.DataFrame()
        df = pandas.read_sql(check_query,connection)
        if df.empty:
            return HttpResponse(json.dumps({'message': 'Access Denied'}))
    else:
        return HttpResponse(json.dumps({'message': 'Token Needed'}))
    try:
        datetime.datetime.strptime(from_date, '%Y-%m-%d')
        datetime.datetime.strptime(to_date, '%Y-%m-%d')
    except ValueError:
        return HttpResponse(json.dumps({'message': 'Wrong Date Format'}))
    else:
        if type == 'forecast':
            if location == 'np':
                weather_forecast_data = __db_fetch_values_dict(
                    "select 'Nepal' as country,date_time,TRUNC(temperature::numeric,1)::text temperature,TRUNC(humidity::numeric,1)::text humidity,TRUNC(wind_speed::numeric,1)::text wind_speed, TRUNC(wind_direction::numeric,1)::text wind_direction, TRUNC(rainfall::numeric,1)::text rainfall from weather_forecast where place_id = any(select place_id from union_place_station_mapping where union_id = any(select id from vwunion where geo_country_id = 2)) and DATE(date_time) between DATE('" + str(
                        from_date) + "') and DATE('" + str(to_date) + "') order by DATE(date_time) asc")
            elif location == 'bd':
                weather_forecast_data = __db_fetch_values_dict(
                    "select 'Bangladesh' as country, date_time,TRUNC(temperature::numeric,1)::text temperature,TRUNC(humidity::numeric,1)::text humidity,TRUNC(wind_speed::numeric,1)::text wind_speed, TRUNC(wind_direction::numeric,1)::text wind_direction,TRUNC(rainfall::numeric,1)::text rainfall from weather_forecast where place_id = any(select place_id from union_place_station_mapping where union_id = any(select id from vwunion where geo_country_id = 1)) and DATE(date_time) between DATE('" + str(
                        from_date) + "') and DATE('" + str(to_date) + "') order by DATE(date_time) asc")
            else:
                return HttpResponse(json.dumps({'message': 'Wrong country parameter'}))

            final_data = {}
            final_data['data'] = weather_forecast_data
            final_data['units'] = {"country": "N/A", "date_time": "N/A", "temperature": "Degree Celsius",
                                   "humidity": "Percent(%)", "wind_speed": "m/s", "wind_direction": "Degree(0-360)",
                                   "rainfall": "mm"}
            return HttpResponse(json.dumps(final_data, default=default))
        elif type == 'observed':
            if location == 'np':
                weather_observed_data = __db_fetch_values_dict("select 'Nepal' as country,date_time,TRUNC(temperature::numeric,1)::text temperature,TRUNC(humidity::numeric,1)::text humidity,TRUNC(wind_speed::numeric,1)::text wind_speed,  TRUNC(wind_direction::numeric,1)::text wind_direction,TRUNC(rainfall::numeric,1)::text rainfall,TRUNC(solar_radiation::numeric,1)::text solar_radiation from weather_observed where id = any(select distinct first_value(id)over(PARTITION by date_time::date ORDER by date_time desc) from weather_observed where station_id::int = any( select station_id from union_place_station_mapping where union_id = any(select id from vwunion where geo_country_id = 2)) and date_time::date between '" + str(from_date) + "' and '" + str(to_date) + "') order by DATE(date_time) asc")
            elif location == 'bd':
                weather_observed_data = __db_fetch_values_dict("select 'Bangladesh' as country,date_time,TRUNC(temperature::numeric,1)::text temperature,TRUNC(humidity::numeric,1)::text humidity,TRUNC(wind_speed::numeric,1)::text wind_speed,  TRUNC(wind_direction::numeric,1)::text wind_direction,TRUNC(rainfall::numeric,1)::text rainfall,TRUNC(solar_radiation::numeric,1)::text solar_radiation from weather_observed where id = any(select distinct first_value(id)over(PARTITION by date_time::date ORDER by date_time desc) from weather_observed where station_id::int = any( select station_id from union_place_station_mapping where union_id = any(select id from vwunion where geo_country_id = 1)) and date_time::date between '" + str(from_date) + "' and '" + str(to_date) + "') order by DATE(date_time) asc")
            else:
                return HttpResponse(json.dumps({'message': 'Wrong country parameter'}))
            final_data = {}
            final_data['data'] = weather_observed_data
            final_data['units'] = {"country": "N/A", "date_time": "N/A", "temperature": "Degree Celsius",
                                   "humidity": "Percent(%)", "wind_speed": "m/s", "wind_direction": "Degree(0-360)",
                                   "rainfall": "mm","solar_radiation": "j/m2"}
            return HttpResponse(json.dumps(final_data, default=default))
        else:
            return HttpResponse(json.dumps({'message': 'Wrong type parameter'}))

import time
@csrf_exempt
def get_farmers_info(request):
    start = datetime.datetime.now()
    if 'user_id' in request.GET:
        print(request.GET.get('user_id'))
        user_id = request.GET.get('user_id')
        farmer_tbl_qry = """ select id farmer_id,farmer_name "name",mobile_number mobile,
        (select "name" from vwdistrict where id = district_id limit 1) district,
        (select "name" from vwupazila where id = upazila_id limit 1) upazilla,
        (select "name" from vwunion where id = union_id limit 1) "union"
        from farmer where organization_id =any (select organisation_name_id from usermodule_usermoduleprofile where user_id =  """+str(user_id)+""") """
        farmer_tbl_df = pandas.read_sql(farmer_tbl_qry, connection)
        # print(farmer_tbl_df)

        # crop_tbl_qry = """ select farmer_id , (
        # select (json_agg(row_to_json(t))) crop
        # from (select
        # (select crop_name from crop where id  = crop_id limit 1) "name"
        # ,(select season_name from cropping_season where id  = season_id limit 1) season
        # ,(select variety_name FROM public.crop_variety x WHERE x.id = crop_variety_id limit 1) variety
        # ,sowing_date
        # ,land_size || ' ' || (SELECT unit_name FROM public.land_units x WHERE x.id = unit_id limit 1 ) land_size
        # from farmer_crop_info s where s.farmer_id = h.farmer_id and s.farmer_id = any(select id from farmer where organization_id =any (select organisation_name_id from usermodule_usermoduleprofile where user_id =  """+str(user_id)+"""))
        # ) as t
        # ) from farmer_crop_info h """
        crop_tbl_qry = """ select farmer_id,
        (select crop_name from crop where id  = crop_id limit 1)  "name"
        ,(select season_name from cropping_season where id  = season_id limit 1) season
        ,(select variety_name FROM public.crop_variety x WHERE x.id = crop_variety_id limit 1) variety
        ,to_char(sowing_date,'YYYY-MM-DD') sowing_date
        ,land_size || ' ' || (SELECT unit_name FROM public.land_units x WHERE x.id = unit_id limit 1 ) land_size
        from farmer_crop_info where farmer_id = any(select id from farmer where organization_id =any (select organisation_name_id from usermodule_usermoduleprofile where user_id =  """+str(user_id)+""" )) """
        crop_tbl_df = pandas.read_sql(crop_tbl_qry, connection)
        # print(crop_tbl_df)
        col = ['name','season','variety','sowing_date','land_size']
        crop_tbl_df = crop_tbl_df.groupby("farmer_id").apply(lambda x: x.to_dict(orient='records')).reset_index(name="crop")
        # [[' name', 'season', 'variety', 'sowing_date', 'land_size']]

        result_df = farmer_tbl_df.merge(crop_tbl_df, on=['farmer_id'], how='left')
        # print(result_df)
        data = {}
        if not result_df.empty:
            data = result_df.to_json(orient='records')
        print(datetime.datetime.now()-start)
        return HttpResponse(data)

    elif 'farmer_id' in request.GET:
        print(request.GET.get('farmer_id'))
        farmer_id = request.GET.get('farmer_id')
        farmer_tbl_qry = """ select id farmer_id,farmer_name "name",mobile_number mobile,
        (select "name" from vwdistrict where id = district_id limit 1) district,
        (select "name" from vwupazila where id = upazila_id limit 1) upazilla,
        (select "name" from vwunion where id = union_id limit 1) "union"
        from farmer where id =  """+str(farmer_id)
        farmer_tbl_df = pandas.read_sql(farmer_tbl_qry,connection)
        crop_tbl_qry = """ select """ + str(farmer_id) + """ farmer_id,json_agg(row_to_json(t)) crop
                from (select 
                (select crop_name from crop where id  = crop_id limit 1) "name" 
                ,(select season_name from cropping_season where id  = season_id limit 1) season
                ,(select variety_name FROM public.crop_variety x WHERE x.id = crop_variety_id limit 1) variety
                ,sowing_date
                ,land_size || ' ' || (SELECT unit_name FROM public.land_units x WHERE x.id = unit_id limit 1 ) land_size
                from farmer_crop_info where farmer_id = """ + str(farmer_id) + """
                ) as t """
        crop_tbl_df = pandas.read_sql(crop_tbl_qry,connection)
        result_df = farmer_tbl_df.merge(crop_tbl_df,on=['farmer_id'],how='left')
        data = {}
        if not result_df.empty:
            data = json.loads(result_df.to_json(orient='records'))[0]
        print(datetime.datetime.now() - start)
        return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps({'message': 'Wrong type parameter'}))