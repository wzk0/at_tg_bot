import telebot
import os
import re
import requests
import json
import config
from datetime import datetime, timedelta

API_TOKEN=config.API_TOKEN
information='🎉使用 /new {date/future} [[time]] [[type]] [[content]] 指令创建一条新的提醒或任务.\n\n示例:\n\n/new +3 8:00 去公园\n_设置一条三天后上午八点的提醒, 内容是\"去公园\"_\n\n/new 2024-2-10 19:00 send 吃饭\n_设置一条于2024年2月10日傍晚七点的提醒, 内容是\"吃饭\"_\n\n/new 23:30 睡觉\n_设置一条于今日晚11点半的提醒, 内容是\"睡觉\"_\n\n/new +1 7:00 do dnf update\n_设置一条于明早七执行的任务, 指令是\"dnf update\"_\n\n任务与提醒的设置格式相似, 只需在[[content]]前指定[[type]]为\"do\"即可, 若指定[[type]]为\"send\"或不指定, 则默认而选择创建一条新提醒而非任务.\n\n--------------------------------\n\n🎉使用 /list 指令列出当前所有提醒或任务.\n\n--------------------------------\n\n🎉使用 /clear 指令清空所有提醒或任务记录.\n\n--------------------------------\n\n🎉使用 /sudo [[do]] [[ID]] 指令添加或移除一位管理员.\n\n示例: /sudo add 123456\n_设置ID为123456的用户或会话为管理员_\n\n/sudo rm 123456\n_移除ID为123456的用户的管理员身份_\n\n[[do]]参数共有"add"(添加)和"rm"(移除)两个, [[ID]]则为用户或会话的ID, 可输入 /id 查看自己或当前会话的ID.\n\n--------------------------------\n\n🎉使用 /id 指令获取自己或当前会话的ID.\n\n--------------------------------\n\n🎉使用 /ai [[word]] 指令与机器人聊天.'
proxy='-x 127.0.0.1:2080'
tips='请使用 /help 指令查看说明.'

bot=telebot.TeleBot(API_TOKEN,parse_mode='MARKDOWN')

# /new [number/date/NOTHING] [time] [type] [content]
# +3         8:00         send hello
# 2024-1-30  8:00         send hello
#         3:00         send hello

def is_good_time(text):
    model=re.compile(r'^([01]?\d|2[0-3]):([0-5]?\d)$')
    return bool(model.match(text))

def is_good_date(text):
    model=re.compile(r'^(?!0000)[0-9]{4}-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01])$')
    return bool(model.match(text))

def send_to(who,what):
    os.system("curl -s %s -X POST \"https://api.telegram.org/bot%s/sendMessage\" -d \"chat_id=%s\" -d \"text=%s\" -d \"parse_mode=Markdown\" >> .tmp"%(proxy,API_TOKEN,who,what))

def get_content(w):
    return ' '.join(w).replace('"','\\"').replace('send ','')

def new_data(who,when,way,what):
    with open('data.json','r')as file:
        data=json.loads(file.read())
    data.append({'who':who,'when':when,'way':way,'what':what})
    with open('data.json','w')as file:
        file.write(json.dumps(data,ensure_ascii=False))

def is_su(who):
    with open('data.json','r')as file:
        for u in json.loads(file.read()):
            if u['who']=='root':
                if who in u['admin']:
                    return True

def control_admin(do,who,user):
    if is_su(who):
        with open('data.json','r')as file:
            data=json.loads(file.read())
            for u in data:
                if u['who']=='root':
                    if do=='add':
                        u['admin'].append(int(user))
                        word='✅成功添加 %s 为管理员🎉'%user
                    elif do=='rm':
                        u['admin'].remove(int(user))
                        word='✅成功移除 %s 的管理员🎉'%user
                    else:
                        word='⚠️格式错误😱\n\n%s'%tips
        with open('data.json','w')as file:
            file.write(json.dumps(data,ensure_ascii=False))
        return word
    else:
        return '⚠️不在管理员列表中, 无法添加或移除新管理员🚨'

def analysis(word,who):
    w=word.split(' ')
    try:
        if is_good_time(w[0]):
            if w[1]=='do':
                if is_su(who):
                    content=get_content(w[2:])
                    os.system("echo '%s' | at %s"%(content,w[0]))
                    today=datetime.now().strftime('%Y-%-m-%-d')
                    new_data(who,today+' '+w[0],'do',content)
                    send_to(who,'📌已成功添加任务👌\n\n🛠️将于 *今天(%s) - %s*\n└─ 执行: *%s*'%(today,w[0],content))
                else:
                    send_to(who,'⚠️不在管理员列表中, 无法创建任务🚨')
            else:
                content=get_content(w[1:])
                os.system('echo "curl %s -X POST \'https://api.telegram.org/bot%s/sendMessage\' -d \'chat_id=%s\' -d \'text=%s\' -d \'parse_mode=Markdown\'" | at %s'%(proxy,API_TOKEN,who,content,w[0]))
                today=datetime.now().strftime('%Y-%-m-%-d')
                new_data(who,today+' '+w[0],'send',content)
                send_to(who,'💡已成功添加提醒👌\n└─ 接收者: %s\n\n✉️将于 *今天(%s) - %s*\n└─ 发送: *%s*'%(who,today,w[0],content))
        elif is_good_date(w[0]):
            if w[2]=='do':
                if is_su(who):
                    content=get_content(w[3:])
                    os.system("echo '%s' | at %s %s"%(content,w[1],w[0]))
                    new_data(who,w[0]+' '+w[1],'do',content)
                    send_to(who,'📌已成功添加任务👌\n\n🛠️将于 *%s - %s*\n└─ 执行: *%s*'%(w[0],w[1],content))
                else:
                    send_to(who,'⚠️不在管理员列表中, 无法创建任务🚨')
            else:
                content=get_content(w[2:])
                os.system('echo "curl %s -X POST \'https://api.telegram.org/bot%s/sendMessage\' -d \'chat_id=%s\' -d \'text=%s\' -d \'parse_mode=Markdown\'" | at %s %s'%(proxy,API_TOKEN,who,content,w[1],w[0]))
                new_data(who,w[0]+' '+w[1],'send',content)
                send_to(who,'💡已成功添加提醒👌\n└─ 接收者: %s\n\n✉️将于 *%s - %s*\n└─ 发送: *%s*'%(who,w[0],w[1],content))
        elif w[0].startswith('+'):
            if w[2]=='do':
                if is_su(who):
                    content=get_content(w[3:])
                    os.system("echo '%s' | at %s + %s days"%(content,w[1],w[0].replace('+','')))
                    today=(datetime.now()+timedelta(days=int(w[0].replace('+','')))).strftime('%Y-%-m-%-d')
                    new_data(who,today+' '+w[1],'do',content)
                    send_to(who,'📌已成功添加任务👌\n\n🛠️将于 *%s天后(%s) - %s*\n└─ 执行: *%s*'%(w[0].replace('+',''),today,w[1],content))
                else:
                    send_to(who,'⚠️不在管理员列表中, 无法创建任务🚨')
            else:
                content=get_content(w[2:])
                os.system('echo "curl %s -X POST \'https://api.telegram.org/bot%s/sendMessage\' -d \'chat_id=%s\' -d \'text=%s\' -d \'parse_mode=Markdown\'" | at %s + %s days'%(proxy,API_TOKEN,who,content,w[1],w[0].replace('+','')))
                today=(datetime.now()+timedelta(days=int(w[0].replace('+','')))).strftime('%Y-%-m-%-d')
                new_data(who,today+' '+w[1],'send',content)
                send_to(who,'💡已成功添加提醒👌\n└─ 接收者: %s\n\n✉️将于 *%s天后(%s) - %s*\n└─ 发送: *%s*'%(who,w[0].replace('+',''),today,w[1],content))
        elif is_good_time(w[0])==False and is_good_date(w[0])==False and (w[0].startswith('+'))==False:
            send_to(who,'⚠️格式错误😱\n\n%s'%tips)
    except IndexError:
        send_to(who,'⚠️缺少参数🤯\n\n%s'%tips)

def get_ls(who):
    user=[]
    with open('data.json','r')as file:
        for u in json.loads(file.read()):
            if u['who']==who:
                user.append('%s %s\t│\t`%s`'%(u['way'].replace('do','📌').replace('send','💡'),u['when'].replace(' ','\t│\t'),u['what'],))
            else:
                pass
    return '设定来源: %s\n任务或提醒总数: %s\n\n💡/📌 日期\t│\t时间\t│\t`内容`\n\n'%(who,len(user))+'\n\n'.join(user)

def clear(who):
    with open('data.json','r')as file:
        data=json.loads(file.read())
    new_data=[]
    for d in data:
        if d['who']==who:
            pass
        else:
            new_data.append(d)
    with open('data.json','w')as file:
        file.write(json.dumps(new_data,ensure_ascii=False))

@bot.message_handler(commands=['help','start'])
def send_help(message):
    bot.reply_to(message,information)

@bot.message_handler(regexp='/new *')
def send_new(message):
    analysis(message.text.replace('/new ',''),message.chat.id)

@bot.message_handler(regexp='/sudo *')
def admin(message):
    # /sudo add 171717171
    word=message.text.replace('/sudo ','').split(' ')
    try:
        result=control_admin(word[0],message.chat.id,word[1])
    except IndexError:
        result='缺少参数🤯\n\n%s'%tips
    bot.reply_to(message,result)

@bot.message_handler(regexp='/list')
def send_list(message):
    bot.reply_to(message,get_ls(message.chat.id))

@bot.message_handler(regexp='/id')
def send_id(message):
    bot.reply_to(message,'🪄ID: `%s`'%message.chat.id)

@bot.message_handler(regexp='/clear')
def clean(message):
    clear(message.chat.id)
    bot.reply_to(message,'✅已完成🎉')

@bot.message_handler(regexp='/ai *')
def send_ai(message):
    bot.reply_to(message,json.loads(requests.get('http://api.qingyunke.com/api.php?key=free&appid=0&msg=%s'%message.text.replace('/ai ','')).text)['content'])

@bot.message_handler(func=lambda message: True)
def echo_reply(message):
    bot.reply_to(message,message.text)

bot.infinity_polling()