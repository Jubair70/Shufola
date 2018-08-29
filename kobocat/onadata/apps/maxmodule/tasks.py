import celery
from celery.task import task
from celery import uuid
from django.core.cache import cache
import threading
from celery.task import periodic_task
from datetime import timedelta
from celery.task.schedules import crontab
from django.db import connection
from django.conf import settings
import requests
import datetime
import urllib2, json
import os
import bisect
import socket
import httplib, urllib

# app = Celery('onadata.apps.ltconfig',
#              broker='amqp://guest:guest@localhost:5672/',
#              backend='librabbitmq',
#              include=['ltconfig.tasks'])
# app = Celery('ltconfig', broker='amqp://guest:guest@localhost:5672/')

class myThread(threading.Thread):
    def __init__(self, task_id):
        threading.Thread.__init__(self)
        self.task_id = task_id

    def run(self):
        print "Starting " + self.task_id
        check_task_status(self.task_id)
        print "Exiting " + self.task_id

def sms_api(dest_no,text):

    conn = httplib.HTTPConnection("107.20.199.106")

    payload = "{\"from\":\"InfoSMS\", \"to\":\"88"+ dest_no +"\", \"binary\":{\"hex\":\""+ text +"\", \"dataCoding\":8, \"esmClass\":0}}"
    #payload = "{\"from\":\"InfoSMS\", \"to\":\"88"+ dest_no +"\", \"binary\":{\"hex\":\"54 65 73 74 20 6d 65 73 73 61 67 65 2e\", \"dataCoding\":0, \"esmClass\":0}}"

    headers = {    'authorization': "Basic Q0FJUzc5ODpvMlZrRXh2OA==",    'content-type': "application/json",    'accept': "application/json"    }

    conn.request("POST", "/restapi/sms/1/binary/single", payload.encode('utf-8'), headers)

    res = conn.getresponse()
    data = res.read()
    #print(data.decode("utf-8"))
    return data.decode("utf-8")







def send_sms(dataid, dest_no, text):
    print 'dest number *******************8'
    # print dest_no
    # print text
    response = {}
    #url = "http://202.73.4.104/g4aw/geobis_sms.php?msisdn=88" + dest_no + "&text=" + text
    try:        
        #r=sms_api(dest_no,text)
        r=sms_api(dest_no,text)
        #print r
        
    except Exception, e:
        print "sending failed.."
        print str(e)
        return
    cursor = connection.cursor()
    try:
        #cursor.execute("BEGIN")
        cursor.execute("select update_cais_send_sms_data(" + str(dataid) + "::bigint,'" + str(r) + "'::text)")
        #cursor.execute("COMMIT")

    except Exception, e:
        print "db get error te"
        print str(e)
        # Rollback in case there is any error
        #connection.rollback()
    finally:
        cursor.close()

        # print r.text


# @periodic_task(run_every=timedelta(seconds=10))
@periodic_task(run_every=timedelta(seconds=10), name="sending_task")
def start_sending_sms_task(lock_expire=1200):
    lock_key = 'send_sms_lock'
    acquire_lock = lambda: cache.add(lock_key, '1', lock_expire)
    release_lock = lambda: cache.delete(lock_key)
    if acquire_lock():
        print "inside acquire"
        try:
            PENDING = 'New'
            SUCCESS = 1
            DELAY = 2
            FAILED = -1
            tmp_db_value = None
            

            cursor = connection.cursor()
            try:
                cursor.execute("BEGIN")
                cursor.callproc('get_cais_send_sms_data', [PENDING])
                tmp_db_value = cursor.fetchall()
                cursor.execute("COMMIT")

            except Exception, e:
                print "db get error"
                print str(e)
                # Rollback in case there is any error
                connection.rollback()
            finally:
                cursor.close()

            if tmp_db_value is not None:
                for eachval in tmp_db_value:
                    print eachval[0]
                    #send_sms(eachval[0], eachval[1], eachval[2])
                    a_string= eachval[2]
                    s=" ".join("{:02X}".format(ord(c)) for c in a_string.encode('utf-8'))
                    print s
                    #send_sms(eachval[0], eachval[1], s)
                    send_sms(eachval[0], eachval[1], a_string)
                    print 'going for sleep'
                    break
        except Exception, e:
            print "lock error"
            print str(e)
        finally:
            # release allow other task to execute
            release_lock()

   
    print "#####################periodic task###################"


def __get_db_function_val(function_name, *args):
    tmp_db_value = []
    cursor = connection.cursor()
    try:
        cursor.execute("BEGIN")
        if args is not None:
            cursor.callproc(function_name, list(args))
        else:
            cursor.callproc(function_name)
        tmp_db_value = cursor.fetchall()
        cursor.execute("COMMIT")
    except Exception, e:
        print('Db query Error:: ', str(e))
    finally:
        cursor.close()
    return tmp_db_value

