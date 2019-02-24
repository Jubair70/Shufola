from datetime import date, timedelta, datetime
import json
import logging
import sys
import operator
import pandas
import numpy
import time
import datetime
from datetime import date, timedelta, datetime
from collections import OrderedDict
import decimal
import os
import shutil
import psycopg2
connection = psycopg2.connect("dbname='ifc' user='kobo' host='192.168.19.19' password='DB@mPower@786'")


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


def management_sms_rule():
    try:
        # conn = psycopg2.connect("dbname='ifc' user='kobo' host='192.168.19.36' password='kobo'")
        # print conn
        # updatecurl=conn.cursor()
        # cur.execute("select user_id,json->>'hh_id' hh_id,xform_id,count(distinct xform_id) submit from logger_instance group by user_id,json->>'hh_id',xform_id")
        cur = connection.cursor()
        start = datetime.now()
        df = []
        crop_sql = "SELECT crop_id, variety_id, crop_name, variety_name FROM vwcrop_variety;"
        df_crop = pandas.read_sql(crop_sql, connection)

        farmer_sql = "SELECT id farmer_id, farmer_name,mobile_number,organization_id, program_id, country_id FROM farmer"
        df_farmer = pandas.read_sql(farmer_sql, connection)

        farmer_crop_sql = "SELECT id farmer_crop_id, farmer_id, crop_id, season_id, crop_variety_id, sowing_date,unit_id, land_size,zone_id, district_id, upazila_id, union_id FROM farmer_crop_info;"
        df_farmer_crop = pandas.read_sql(farmer_crop_sql, connection)
        print
        "here1"

        df_frm = pandas.merge(df_farmer, df_farmer_crop, on='farmer_id')
        print
        "here2"

        farmer_crop_stage_sql = "SELECT farmer_crop_id, stage stage_id FROM farmer_crop_stage"
        df_farmer_crop_stage = pandas.read_sql(farmer_crop_stage_sql, connection)

        stage_sql = "SELECT id::text stage_id, stage_name FROM crop_stage;"
        df_stage = pandas.read_sql(stage_sql, connection)

        df_farmer_crop_stage = pandas.merge(df_farmer_crop_stage, df_stage, on='stage_id')

        df_frm_stage = pandas.merge(df_frm, df_farmer_crop_stage, on='farmer_crop_id')

        # df_frm_stage=pd.merge(df_frm_stage, df_stage, on='stage_id')

        sms_sql = "SELECT id sms_id,org_id organization_id, program_id, crop_id, variety_id crop_variety_id, season_id, stage_id::text,sms_description,coalesce(hour_sms,0) hour_sms,voice_sms_file_path,group_id,content_id,offset_days FROM management_sms_rule where category_id=1 and group_id=0;"
        df_sms = pandas.read_sql(sms_sql, connection)

        df_farmer_sms = pandas.merge(df_frm_stage, df_sms,
                                     on=['organization_id', 'program_id', 'season_id', 'crop_id', 'crop_variety_id',
                                         'stage_id'])

        # else


        sms_sql_group = "SELECT id sms_id,org_id organization_id, program_id, crop_id, variety_id crop_variety_id, season_id, stage_id::text,sms_description,coalesce(hour_sms,0) hour_sms,voice_sms_file_path,group_id,content_id,offset_days FROM management_sms_rule where category_id=1 and group_id<>0;"
        df_sms_group = pandas.read_sql(sms_sql_group, connection)

        farmer_group_sql = "select farmer_id,group_id from farmer_group"
        df_farmer_grp = pandas.read_sql(farmer_group_sql, connection)
        df_frm_stage = pandas.merge(df_frm_stage, df_farmer_grp, on=['farmer_id'])

        df_farmer_sms_group = pandas.merge(df_frm_stage, df_sms_group,
                                           on=['organization_id', 'program_id', 'season_id', 'crop_id',
                                               'crop_variety_id', 'stage_id', 'group_id'])

        i = 0
        # print df_frm_stage.head(5)
        # df_sms.to_csv('rawsms.csv')
        qry_1 = "INSERT INTO management_sms_que(organization_id, program_id, crop_id, variety_id, season_id, stage_id, farmer_id, farmer_name, mobile_number, sms_id, sms_text,voice_sms_file_path, status, created_by, created_at, updated_by, updated_at,schedule_time,content_id) values("
        for index, row in df_farmer_sms.iterrows():
            chk_qry = "select count(*) is_exist from management_sms_que where sms_id=" + str(
                row['sms_id']) + " and farmer_id=" + str(row['farmer_id']) + ";"
            print(chk_qry)
            cur.execute(chk_qry)

            chk_value = cur.fetchone()
            is_exist = chk_value[0]
            # print row['organization_id'], row['program_id'], row['crop_id'], row['crop_variety_id'], row['season_id'],row['stage_id'],row['farmer_id'], row['farmer_name'],row['mobile_number'],row['sms_id'],row['sms_description']

            if is_exist == 0:
                qry_2 = str(row['organization_id']) + "," + str(row['program_id']) + "," + str(
                    row['crop_id']) + "," + str(row['crop_variety_id']) + "," + str(row['season_id']) + "," + str(
                    row['stage_id']) + "," + str(row['farmer_id']) + ",'" + str(row['farmer_name']) + "','" + str(
                    row['mobile_number']) + "'," + str(row['sms_id']) + ",'" + row['sms_description'] + "','" + row[
                            'voice_sms_file_path'] + "','New','system',now(),'system',now(),now()+ interval '1d' * " + str(
                    row['offset_days'])
                qry = qry_1 + qry_2 + ",'" + str(row['content_id']) + "');"
                print
                qry
                cur.execute(qry)
                connection.commit()
            else:
                print
                'Already Inserted'

        qry_1 = "INSERT INTO management_sms_que(organization_id, program_id, crop_id, variety_id, season_id, stage_id, farmer_id, farmer_name, mobile_number, sms_id, sms_text,voice_sms_file_path, status, created_by, created_at, updated_by, updated_at,schedule_time,content_id) values("
        for index, row in df_farmer_sms_group.iterrows():
            chk_qry = "select count(*) is_exist from management_sms_que where sms_id=" + str(
                row['sms_id']) + " and farmer_id=" + str(row['farmer_id']) + ";"
            print(chk_qry)
            cur.execute(chk_qry)

            chk_value = cur.fetchone()
            is_exist = chk_value[0]
            # print row['organization_id'], row['program_id'], row['crop_id'], row['crop_variety_id'], row['season_id'],row['stage_id'],row['farmer_id'], row['farmer_name'],row['mobile_number'],row['sms_id'],row['sms_description']

            if is_exist == 0:
                qry_2 = str(row['organization_id']) + "," + str(row['program_id']) + "," + str(
                    row['crop_id']) + "," + str(row['crop_variety_id']) + "," + str(row['season_id']) + "," + str(
                    row['stage_id']) + "," + str(row['farmer_id']) + ",'" + str(row['farmer_name']) + "','" + str(
                    row['mobile_number']) + "'," + str(row['sms_id']) + ",'" + row['sms_description'] + "','" + row[
                            'voice_sms_file_path'] + "','New','system',now(),'system',now(),now()+ interval '1d' * " + str(
                    row['offset_days'])
                qry = qry_1 + qry_2 + ",'" + str(row['content_id']) + "');"
                print
                qry
                cur.execute(qry)
                connection.commit()
            else:
                print
                'Already Inserted'

        print(datetime.now())
        print(datetime.now() - start)
        print('\n\n\n\n\n')


        # print len(df_sms)


    except:
        print
        "I am unable to connect to the database"


def update_stage():
    start = datetime.now()
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
                                                                                                     i]) + ", (SELECT(SELECT CASE when crop_variety_id :: INT = 0 and season_id :: INT != 0 then (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + " limit 1) when crop_variety_id :: INT != 0 and season_id :: INT = 0 then (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + " limit 1) WHEN crop_variety_id :: INT = 0 and season_id :: INT = 0 THEN (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + " limit 1) ELSE (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + ") end FROM crop_stage WHERE crop_id = t.crop_id LIMIT 1) FROM farmer_crop_info t WHERE t.id = " + str(
                farmer_crop_id[i]) + "))"
            __db_commit_query(insert_query)
        else:
            update_query = "update farmer_crop_stage set stage =(SELECT(SELECT CASE when crop_variety_id :: INT = 0 and season_id :: INT != 0 then (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + " limit 1) when crop_variety_id :: INT != 0 and season_id :: INT = 0 then (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + " limit 1) WHEN crop_variety_id :: INT = 0 and season_id :: INT = 0 THEN (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + " limit 1) ELSE (SELECT id FROM crop_stage WHERE crop_id :: INT = t.crop_id :: INT AND crop_variety_id :: INT = t.crop_variety_id :: INT AND season_id :: INT = t.season_id :: INT AND Now() :: date - t.sowing_date >= start_day AND Now() :: date - t.sowing_date <= end_day AND t.id = " + str(
                farmer_crop_id[
                    i]) + ") end FROM crop_stage WHERE crop_id = t.crop_id LIMIT 1) FROM farmer_crop_info t WHERE t.id = " + str(
                farmer_crop_id[i]) + ") where farmer_crop_id =" + str(farmer_crop_id[i])
            __db_commit_query(update_query)
    print(datetime.now())
    print(datetime.now() - start)
    print('\n\n\n\n\n')
    # return render(request,'ifcmodule/index.html')
    # return HttpResponse('')


def weather_forecast():
    # os.system("sudo -S chmod -R 777 /home/ftpuserifc/20180826_00")
    start = datetime.now()
    query = "select * from weather_forecast"
    # directory = "20180917_00"
    # os.system("echo ''|sudo -S chmod -R 777 /home/ftpuserifc/20180916_00")
    directory = str(datetime.now().date()).replace('-','')+'_00'
    if not os.path.exists("/home/ftpuserifc/weather_files/"):
        os.makedirs("/home/ftpuserifc/weather_files/")
    if not os.path.exists("/home/ftpuserifc/weather_files/"+str(directory)) and os.path.exists('/home/ftpuserifc/'+str(directory)):
        shutil.copytree('/home/ftpuserifc/'+str(directory),'/home/ftpuserifc/weather_files/'+str(directory))
        #list_of_files in that directory
        list_of_files = os.listdir('/home/ftpuserifc/weather_files/'+str(directory))
        # print(list_of_files)
        for each in list_of_files:
            # print('.txt' in each)
            if '.txt' in each:
                # read from directory
                # shutil.copyfile('onadata/media/test/Tar_02.txt', 'onadata/media/uploaded_files/Tar_02.txt')
                file = open('/home/ftpuserifc/weather_files/'+str(directory)+'/'+str(each), 'r')
                insert_content = file.read()
                file.close()
                insert_content = insert_content.split('\n')
                for each in insert_content:
                    # print(re.split(r"\s+",each,maxsplit=6))
                    temp_data = each.split(None,6)
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
                        # rainfall 0 as there is a string existing in parsing file
                        if rainfall[0] == 'E':
                            rainfall = '0'

                        # formatting the date_time
                        res_date = ''
                        res_date = date_time[0]+'-'
                        if int(date_time[1]) <= 9:
                            res_date += '0'+date_time[1]+'-'
                        else:
                            res_date += date_time[1] + '-'
                        if int(date_time[2]) <= 9:
                            res_date += '0'+date_time[2]
                        else:
                            res_date += date_time[2]
                        if int(date_time[3]) <= 9:
                            res_date += ' 0' + date_time[3]+ ':00'+ ':00'
                        else:
                            res_date += ' ' + date_time[3] + ':00' + ':00'

                        # check if data is exists or not
                        query = "select id from weather_forecast where place_name = '"+str(place_name)+"' and date_time = '"+str(res_date)+"'"
                        df = pandas.DataFrame()
                        df = pandas.read_sql(query,connection)
                        if not df.empty:
                            # update query
                            id = df.id.tolist()[0]
                            update_query = "UPDATE public.weather_forecast SET temperature='"+str(temperature)+"', humidity='"+str(humidity)+"', wind_speed='"+str(wind_speed)+"', wind_direction='"+str(wind_direction)+"', rainfall='"+str(rainfall)+"' where id = "+str(id)
                            __db_commit_query(update_query)
                        else:
                            insert_query = "INSERT INTO public.weather_forecast (place_name, date_time, temperature, humidity, wind_speed, wind_direction, rainfall,data_type,place_id) VALUES('"+str(place_name)+"', '"+str(res_date)+"', '"+str(temperature)+"', '"+str(humidity)+"', '"+str(wind_speed)+"', '"+str(wind_direction)+"', '"+str(rainfall)+"','2',(select id from weather_forecast_place where weather_forecast_place.place_name='"+str(place_name)+"'))"
                            __db_commit_query(insert_query)
    print(datetime.now())
    print(datetime.now()-start)
    print('\n\n\n\n\n')
    # return render(request,'ifcmodule/index.html')

def weather_observed():
    start = datetime.now()
    if not os.path.exists("/home/sftpuserifc/weather_observed_files/"):
        os.makedirs("/home/sftpuserifc/weather_observed_files/")
    list_of_files = os.listdir("/home/sftpuserifc/awsdata/")
    for file_name in list_of_files:
        full_file_path = "/home/sftpuserifc/awsdata/"+str(file_name)
        df = pandas.DataFrame()
        df = pandas.read_csv(full_file_path)
        cols = df.columns
        for each in df.index:
            if "aws1" in file_name:
                station_id = 1
            elif "aws2" in file_name:
                station_id = 2
            elif "aws3" in file_name:
                station_id = 3
            date_time = set_nan_to_blank(df.loc[each][str(cols[0])])
            wind_speed = set_nan_to_blank(df.loc[each][str(cols[2])])
            wind_direction = set_nan_to_blank(df.loc[each][str(cols[5])])
            qfe = set_nan_to_blank(df.loc[each][str(cols[6])])
            qff = set_nan_to_blank(df.loc[each][str(cols[7])])
            temperature = set_nan_to_blank(df.loc[each][str(cols[8])])
            humidity = set_nan_to_blank(df.loc[each][str(cols[9])])
            dew_point_temperature = set_nan_to_blank(df.loc[each][str(cols[10])])
            solar_radiation = set_nan_to_blank(df.loc[each][str(cols[11])])
            soil_moisture = set_nan_to_blank(df.loc[each][str(cols[12])])
            rainfall = set_nan_to_blank(df.loc[each][str(cols[13])])
            # check if data exists
            query = "select id from weather_observed where date_time = '" + str(date_time) + "'"
            df1 = pandas.DataFrame()
            df1 = pandas.read_sql(query, connection)
            if not df1.empty:
                # update query
                id = df1.id.tolist()[0]
                update_query = "UPDATE public.weather_observed SET soil_moisture='"+str(soil_moisture)+"',qff='"+str(qff)+"',qfe='"+str(qfe)+"',wind_direction = '"+str(wind_direction)+"',station_id='"+str(station_id)+"', date_time='"+str(date_time)+"', wind_speed ='"+str(wind_speed)+"', temperature ='"+str(temperature)+"', dew_point_temperature ='"+str(dew_point_temperature)+"', humidity ='"+str(humidity)+"', solar_radiation ='"+str(solar_radiation)+"', rainfall ='"+str(rainfall)+"' where id = " + str(id)
                __db_commit_query(update_query)
            else:
                # insert query
                insert_query = "INSERT INTO public.weather_observed (soil_moisture,qff,qfe,wind_direction,station_id, date_time, wind_speed, temperature, dew_point_temperature, humidity, solar_radiation, rainfall) VALUES('"+str(soil_moisture)+"','"+str(qfe)+"','"+str(qff)+"','"+str(wind_direction)+"','"+str(station_id)+"', '"+str(date_time)+"', '"+str(wind_speed)+"', '"+str(temperature)+"','"+str(dew_point_temperature)+"', '"+str(humidity)+"', '"+str(solar_radiation)+"', '"+str(rainfall)+"')"
                __db_commit_query(insert_query)
        shutil.move('/home/sftpuserifc/awsdata/'+str(file_name),'/home/sftpuserifc/weather_observed_files/'+str(file_name))
    print(datetime.now())
    print(datetime.now()-start)
    print('\n\n\n\n\n')

def set_nan_to_blank(var):
    if str(var) == "nan":
        var = ""
    return var


def get_farmers_sms():
    start = datetime.now()
    query = "WITH first_q AS(SELECT weather_sms_rule.id, category_id, sms_description, org_id, program_id, crop_id, season_id, variety_id, stage_id,group_id, rules_relation FROM weather_sms_rule, weather_sms_rule_relation WHERE  weather_sms_rule.id = weather_sms_rule_relation.weather_sms_rule_id), q2 AS (SELECT Unnest(Regexp_split_to_array(rules_relation, '[&||]')) details_id, * FROM first_q), q3 AS (SELECT q2.id weather_sms_rule_id, q2.*, weather_sms_rule_details.*, Substring(rules_relation, Position( weather_sms_rule_details.id :: text IN rules_relation) :: INT - 1, 1) operations FROM weather_sms_rule_details, q2 WHERE weather_sms_rule_details.id = q2.details_id :: INT) SELECT *,(select sub_parameter_name from weather_sub_parameters where id = sub_parameter_id::int) FROM q3 order by weather_sms_rule_id::int,details_id::int"
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
            group_id = df.loc[df.index[df['weather_sms_rule_id'] == each]]['group_id'].tolist()[0]
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
                    # str_condition = "with t as( select place_id, date_time::date," + str(agg_fun_sub_parameter) + "(" + str(
                    #     column_name) + "::numeric) daily_calc from weather_forecast where date_time::date between now()::date + interval '1 day' and now()::date + interval '" + str(
                    #     consecutive_days[i]) + " day' group by place_id,date_time::date)select distinct place_id from t where place_id is not null group by place_id having " + str(
                    #     calculation_type[i]) + "(daily_calc) " + str(operators[i]) + " " + str(parameter_value[i]) + " "
                    try:
                        str_condition = "WITH g AS(SELECT place_id,date_time::date," + str(agg_fun_sub_parameter) + "(" + str(column_name) + "::float) daily_calc FROM weather_forecast WHERE date_time::date BETWEEN now()::date + interval '1 day' AND now()::date + interval '" + str(consecutive_days[i]) + " day' GROUP BY place_id,date_time::date),t as (select place_id," + str(calculation_type[i]) + "(daily_calc) daily_calc from g GROUP BY place_id) SELECT distinct g.place_id FROM t,g WHERE t.place_id = g.place_id and g.place_id IS NOT NULL and t.daily_calc " + str(operators[i]) + " " + str(parameter_value[i]) + ""
                    except e:
                        print("Forecast")
                        print(e)
                elif parameter_type_id[i] == 1:
                    # str_condition = "with t as( select station_id, date_time::date," + str(agg_fun_sub_parameter) + "(" + str(
                    #     column_name) + "::numeric) daily_calc from weather_observed where date_time::date between now()::date - interval '1 day' and now()::date - interval '" + str(
                    #     consecutive_days[i]) + " day' group by station_id,date_time::date),t1 as( select station_id,place_id from union_place_station_mapping where station_id IS NOT NULL and station_id = any(SELECT DISTINCT station_id::int FROM t)) select place_id from t, t1 where t.station_id::int = t1.station_id GROUP BY t.station_id,t1.place_id HAVING " + str(calculation_type[i]) + "(daily_calc) " + str(operators[i]) + " " + str(parameter_value[i]) + ""
                    try:
                        str_condition = "WITH g AS( SELECT station_id, date_time::date, " + str(agg_fun_sub_parameter) + "(" + str(column_name) + "::float) daily_calc FROM weather_observed WHERE date_time::date BETWEEN now()::date - interval '1 day' AND now()::date - interval '" + str( consecutive_days[i]) + " day' GROUP BY station_id, date_time::date),t as (select station_id," + str(calculation_type[i]) + "(daily_calc) daily_calc from g GROUP BY station_id),t1 AS ( SELECT station_id, place_id FROM union_place_station_mapping WHERE station_id IS NOT NULL AND station_id = ANY (SELECT DISTINCT station_id::int FROM g)) SELECT distinct place_id FROM t,t1 where t.station_id::int = t1.station_id and daily_calc " + str(operators[i]) + " " + str(parameter_value[i]) + ""
                    except e:
                        print("Observed")
                        print(e)
                # if parameter_type_id[i] == 2:
                #     str_condition = "with t as( select place_id, date_time::date," + str(agg_fun_sub_parameter) + "(" + str(
                #         column_name) + "::numeric) daily_calc from weather_forecast where date_time::date between now()::date + interval '1 day' and now()::date + interval '" + str(
                #         consecutive_days[i]) + " day' group by place_id,date_time::date)select distinct place_id from t where place_id is not null group by place_id having " + str(
                #         calculation_type[i]) + "(daily_calc) " + str(operators[i]) + " " + str(parameter_value[i]) + " "
                # elif parameter_type_id[i] == 1:
                #     str_condition = "with t as( select station_id, date_time::date," + str(agg_fun_sub_parameter) + "(" + str(
                #         column_name) + "::numeric) daily_calc from weather_observed where date_time::date between now()::date - interval '1 day' and now()::date - interval '" + str(
                #         consecutive_days[i]) + " day' group by station_id,date_time::date),t1 as( select station_id,place_id from union_place_station_mapping where station_id IS NOT NULL and station_id = any(SELECT DISTINCT station_id::int FROM t)) select place_id from t, t1 where t.station_id::int = t1.station_id GROUP BY t.station_id,t1.place_id HAVING " + str(calculation_type[i]) + "(daily_calc) " + str(operators[i]) + " " + str(parameter_value[i]) + ""

                if i != 0:
                    if operations[i] == '&':
                        result_str_condition += ' INTERSECT '
                    else:
                        result_str_condition += ' UNION '
                    result_str_condition += '(' + str_condition + ')'
                else:
                    result_str_condition += str_condition

            # print(result_str_condition)
            if group_id == 0:
                query_t = "insert into weather_sms_rule_queue(weather_sms_rule_id,mobile_number,sms_description,crop_id,season_id,variety_id,stage_id,org_id,program_id,union_id,voice_sms_file_path,content_id,farmer_id,farmer_name) with dfg1 as( select * from farmer_crop_info,farmer_crop_stage where farmer_crop_info.id = farmer_crop_stage.farmer_crop_id and stage is not null),dfg as ( select * from dfg1,farmer where dfg1.farmer_id = farmer.id ) select weather_sms_rule.id weather_sms_rule_id,(select mobile_number from farmer where id = farmer_id limit 1)mobile_number,sms_description, weather_sms_rule.crop_id,weather_sms_rule.season_id,weather_sms_rule.variety_id,weather_sms_rule.stage_id,weather_sms_rule.org_id,weather_sms_rule.program_id,( SELECT union_id FROM farmer WHERE id = farmer_id limit 1) union_id,voice_sms_file_path,content_id,farmer_id,farmer_name from weather_sms_rule,dfg where weather_sms_rule.id = "+str(wea_sms_id)+" and weather_sms_rule.crop_id = dfg.crop_id and weather_sms_rule.season_id = dfg.season_id and weather_sms_rule.variety_id = dfg.crop_variety_id and weather_sms_rule.stage_id = dfg.stage::int and weather_sms_rule.org_id = dfg.organization_id and weather_sms_rule.program_id = dfg.program_id and farmer_id=any ( select distinct farmer_id from farmer_crop_info where union_id = any (select distinct union_id from union_place_station_mapping where place_id =any ("+str(result_str_condition)+"))) order by farmer_crop_id"
            else:
                query_t = "insert into weather_sms_rule_queue(weather_sms_rule_id,mobile_number,sms_description,crop_id,season_id,variety_id,stage_id,org_id,program_id,union_id,voice_sms_file_path,content_id,farmer_id,farmer_name) with dfg1 as( select * from farmer_crop_info,farmer_crop_stage where farmer_crop_info.id = farmer_crop_stage.farmer_crop_id and stage is not null),dfg as ( select * from dfg1,farmer where dfg1.farmer_id = farmer.id ) select weather_sms_rule.id weather_sms_rule_id,(select mobile_number from farmer where id = farmer_id limit 1)mobile_number,sms_description, weather_sms_rule.crop_id,weather_sms_rule.season_id,weather_sms_rule.variety_id,weather_sms_rule.stage_id,weather_sms_rule.org_id,weather_sms_rule.program_id,( SELECT union_id FROM farmer WHERE id = farmer_id limit 1) union_id,voice_sms_file_path,content_id,farmer_id,farmer_name from weather_sms_rule,dfg where weather_sms_rule.id = "+str(wea_sms_id)+" and weather_sms_rule.crop_id = dfg.crop_id and weather_sms_rule.season_id = dfg.season_id and weather_sms_rule.variety_id = dfg.crop_variety_id and weather_sms_rule.stage_id = dfg.stage::int and weather_sms_rule.org_id = dfg.organization_id and weather_sms_rule.program_id = dfg.program_id and farmer_id=any ( select distinct farmer_id from farmer_crop_info where farmer_id = any(select farmer_id from farmer_group where group_id = weather_sms_rule.group_id) and union_id = any (select distinct union_id from union_place_station_mapping where place_id =any ("+str(result_str_condition)+"))) order by farmer_crop_id"
            print(query_t)
            __db_commit_query(query_t)
            # query_u = "update weather_sms_rule set sms_status = 1 where id = "+str(wea_sms_id)
            # __db_commit_query(query_u)
            # print(query_t)

    print(datetime.now())
    print(datetime.now() - start)
    print('\n\n\n\n\n')
    # return render(request, 'ifcmodule/index.html')

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