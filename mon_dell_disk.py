#!/usr/bin/env python
#coding: utf-8
'''Script used to monitor disk
'''

import socket
import fcntl
import struct
import time
import smtplib
from email.mime.text import MIMEText
from subprocess import Popen, PIPE

cmd = '/opt/MegaRAID/MegaCli/MegaCli64'

##Items need to be monitored
keys = ['Slot Number',
        'Device Id',
        'Media Error Count',
        'Other Error Count',
        'Predictive Failure Count',
        'PD Type',
        'Raw Size',
        'Firmware state',
        'Inquiry Data',
        'Foreign State',
        'Drive Temperature ']


def get_ip_add(ifname):
    '''Get server ip address.
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,
        struct.pack('256s', ifname[:15])
    )[20:24])


def send_mail(sub, content):
    '''
        to_list:发给谁
        sub:主题
        content:内容
        send_mail([to_list], 'sub', 'content')
    '''
    ##发送给谁
    mailto_list=['xx@example.org', '10000@qq.com']
    ##设置smtp服务器信息
    #mail_host='mail.monitor.com'
    mail_user='disk@monitor.com'
    #mail_pass='xxxxxx'
    #mail_postfix='monitor.com'

    me = mail_user+'<'+mail_user+'>'
    msg = MIMEText(content, _charset='gbk')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ';'.join(mailto_list)

    try:
        server = smtplib.SMTP('localhost')
        ##server.connect(mail_host)
        ##server.login(mail_user, mail_pass)
        server.sendmail(me, mailto_list, msg.as_string())
        server.quit()
        return True
    except Exception, e:
        #print str(e)
        return False


def mon_item(dvar):
    '''Judge monitor items, abnormal info happens,
       An mail will be sent to notfiy administrator.
    '''
    ##Firmware state
    Fs = [' Online, Spun Up', ' Hotspare, Spun Up']

    ##ifname changes according to you system!!
    ip_add = get_ip_add('em2')

    if dvar['Media Error Count'] != ' 0':
        #print 'media error count: %s' % dvar['Media Error Count']
        send_mail('IP: %s Media Error' % ip_add,
                  'IP: %s \nSlot Number:%s\nDevice Id:%s\nMedia Error Count:%s \nTime: %s' %
                  (ip_add, dvar['Slot Number'], dvar['Device Id'], dvar['Media Error Count'],
                  time.strftime('%Y-%m-%d %H:%M:%S')))

    #if dvar['Other Error Count'] != ' 0':
    #    #print 'other error count: %s' % dvar['Other Error Count']
    #    send_mail('IP: %s Other Error' % ip_add,
    #              'IP: %s \nSlot Number:%s\nDevice Id:%s\nOther Error Count:%s \nTime: %s' %
    #              (ip_add, dvar['Slot Number'], dvar['Device Id'], dvar['Other Error Count'],
    #              time.strftime('%Y-%m-%d %H:%M:%S')))

    if dvar['Predictive Failure Count'] != ' 0':
        #print 'Predictive Failure Count: %s' % dvar['Predictive Failure Count']
        send_mail('IP: %s Predictive Failure' % ip_add,
                  'IP: %s \nSlot Number:%s\nDevice Id:%s\nPredictive Failure Count:%s \nTime: %s' %
                  (ip_add, dvar['Slot Number'], dvar['Device Id'], dvar['Predictive Failure Count'],
                  time.strftime('%Y-%m-%d %H:%M:%S')))

    if dvar['Foreign State'] != ' None':
        #print 'Foreign State: %s' % dvar['Foreign State']
        send_mail('IP: %s Foreign State' % ip_add,
                  'IP: %s \nSlot Number:%s\nDevice Id:%s\nForeign State:%s \nTime: %s' %
                  (ip_add, dvar['Slot Number'], dvar['Device Id'], dvar['Foreign State'],
                  time.strftime('%Y-%m-%d %H:%M:%S')))

    if dvar['Firmware state'] not in Fs:
        #print 'Firmware state: %s' % dvar['Firmware state']
        send_mail('IP: %s Firmware state' % ip_add,
                  'IP: %s \nSlot Number:%s\nDevice Id:%s\nFirmware state:%s \nTime: %s' %
                  (ip_add, dvar['Slot Number'], dvar['Device Id'], dvar['Firmware state'],
                  time.strftime('%Y-%m-%d %H:%M:%S')))

    """ Test data:
        diskinfo={'Drive Temperature ': '33C (91.40 F)', 'Predictive Failure Count': ' 0', 'Media Error Count': ' 0', 'Raw Size': ' 1.819 TB [0xe8e088b0 Sectors]', 'Foreign State': ' None', 'PD Type': ' SASHotspare Information', 'Other Error Count': ' 4', 'Device Id': ' 4', 'Firmware state': ' Hotspare, Spun Up', 'Slot Number': ' 4', 'Inquiry Data': ' SEAGATE ST2000NM0023    0003Z1X1ETXW            Hotspare Information'}
        mon_item(diskinfo)
    """


def main():
    '''Main function used to deal megacli data into standard dict format.
    '''
    p1 = Popen([cmd, '-PDList', '-aALL', '-NoLog'], stdout=PIPE, stderr=PIPE)
    tuple1 = p1.communicate()

    list1 = []
    klist = []

    ##split megacli output into standard list
    ##all values stored in list1
    for i in tuple1:
        if len(i.split('\n')) != 1:
            list1 = i.split('\n')
    #print list1

    ##get last items, every disk has 11 item.
    ##values stored in klist
    for j in list1:
        for k in keys:
            if not j.find(k):
                klist.append(j)

    #print klist

    Len = len(klist)
    ns = locals()
    
    for n in range(0, Len/11):
        ##generated dynamically, used to store every disk info
        ns['LK%s' %n] = []
        for m in range(0, 11):
            ns['LK%s' %n].append(klist[m+n*11].strip().split(":", 1))

            ##Following for sentence is to hot spare disk!!
            #for T in range(0, len(ns['LK%s' %n])):
            #    if len(ns['LK%s' %n][T]) == 3:
            #        ns['LK%s' %n][T].pop(-1)

        ##Yes, final data is saved in one dict.
        #print ns['LK%s' %n]
        ns['DK%s' %n] = dict(ns['LK%s' %n])

        ##Call function
        mon_item(ns['DK%s' %n])


if __name__ == '__main__':
    main()

    ##test codes running time
    #import time
    #t1=time.clock()
    #main()
    #t2=time.clock()
    #print t2-t1

    #import timeit
    #print(timeit.timeit("main()", setup="from __main__ import main", number=1))

