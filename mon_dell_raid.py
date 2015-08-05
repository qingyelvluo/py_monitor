#!/usr/bin/env python
#coding: utf-8
'''Script used to monitor raid.
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
keys = ['Virtual Drive',
        'RAID Level',
        'Size',
        'State',
        'Current Cache Policy',
        'Bad Blocks Exist',]

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
    mail_user='raid@monitor.com'
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


def mon_item(dargv):
    '''Judge monitor items, abnormal info happens,
       An mail will be sent to notfiy administrator.
    '''
    ##RAID Level, change it according your raid!!
    RL = [' Primary-1, Secondary-0, RAID Level Qualifier-0',]

    ##remove key's space of dargv
    dvar = {}
    for p in dargv.keys():
        Val = dargv[p]
        dvar[p.strip()] = Val

    #print dvar

    ##ifname changes according to you system!!
    ip_add = get_ip_add('em2')

    if dvar['State'] != ' Optimal':
        #print 'state error: %s' % dvar['State']
        send_mail('IP: %s state error' % ip_add,
                  'IP: %s \nVirtual Drive:%s\nState:%s \nTime: %s' %
                  (ip_add, dvar['Virtual Drive'], dvar['State'],
                  time.strftime('%Y-%m-%d %H:%M:%S')))

    if dvar['RAID Level'] not in RL:
        #print 'RAID Level error: %s' % dvar['RAID Level']
        send_mail('IP: %s RAID Level error' % ip_add,
                  'IP: %s \nVirtual Drive:%s\nRAID Level:%s \nTime: %s' %
                  (ip_add, dvar['Virtual Drive'], dvar['RAID Level'],
                  time.strftime('%Y-%m-%d %H:%M:%S')))

    if dvar['Bad Blocks Exist'] != ' No':
        #print 'Bad Blocks Exist: %s' % dvar['Bad Blocks Exist']
        send_mail('IP: %s Bad Blocks Exist' % ip_add,
                  'IP: %s \nVirtual Drive:%s\nBad Blocks Exist:%s \nTime: %s' %
                  (ip_add, dvar['Virtual Drive'], dvar['Bad Blocks Exist'],
                  time.strftime('%Y-%m-%d %H:%M:%S')))

def main():
    '''Main function used to deal megacli data into standard dict format.
    '''
    p1 = Popen([cmd, '-ldinfo', '-lall', '-aall', '-NoLog'], stdout=PIPE, stderr=PIPE)
    tuple1 = p1.communicate()

    list1 = []
    klist = []

    ##split megacli output into standard list
    ##all values stored in list1
    for i in tuple1:
        if len(i.split('\n')) != 1:
            list1 = i.split('\n')
    #print list1

    ##get last items, every vd has 6 item.
    ##values stored in klist
    for j in list1:
        for k in keys:
            if not j.find(k):
                klist.append(j)

    #print klist

    Len = len(klist)
    ns = locals()

    for n in range(0, Len/6):
        ##generated dynamically, used to store every virtual disk info
        ns['LK%s' %n] = []
        for m in range(0, 6):
            #ns['LK%s' %n].append(klist[m+n*6].strip().replace('d:', 'd', 1).split(":"))
            ns['LK%s' %n].append(klist[m+n*6].strip().split(":", 1))

        ##Yes, final data is saved in one dict.
        #print ns['LK%s' %n]
        ns['DK%s' %n] = dict(ns['LK%s' %n])
        #print ns['DK%s' %n]
        mon_item(ns['DK%s' %n])


if __name__ == '__main__':
    main()
