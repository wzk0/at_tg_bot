import telebot
import os
import re
import requests
import json
import config

API_TOKEN=config.API_TOKEN
information='使用 /new {date/future} [[time]] [[type]] [[content]] 指令创建一条新的提醒或定时任务.\n\n示例:\n\n*/new +3 8:00 去公园*\n_设置一条三天后上午八点的提醒, 内容是\"去公园\"_\n\n*/new 2024-2-10 19:00 send 吃饭*\n_设置一条于2024年2月10日傍晚七点的提醒, 内容是\"吃饭\"_\n\n*/new 23:30 睡觉*\n_设置一条于今日晚11点半的提醒, 内容是\"睡觉\"_\n\n*/new +1 7:00 do dnf update*\n_设置一条于明早七点执行的定时任务, 指令是\"dnf update\"_\n\n定时任务与提醒的设置格式相似, 只需在[[content]]前指定[[type]]为\"do\"即可, 若指定[[type]]为\"send\"或不指定, 则默认而选择创建一条新提醒而非定时任务.'
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

def analysis(word,who):
    w=word.split(' ')
    try:
        if is_good_time(w[0]):
            if w[1]=='do':
                os.system("echo '%s' | at %s"%(get_content(w[2:]),w[0]))
                send_to(who,'已成功添加任务👌\n\n将于 *今天 - %s* 执行: *%s*'%(w[0],get_content(w[2:])))
            else:
                os.system('echo "curl %s -X POST \'https://api.telegram.org/bot%s/sendMessage\' -d \'chat_id=%s\' -d \'text=%s\' -d \'parse_mode=Markdown\'" | at %s'%(proxy,API_TOKEN,who,get_content(w[1:]),w[0]))
                send_to(who,'已成功添加提醒👌 接收者: %s\n\n将于 *今天 - %s *发送: *%s*'%(who,w[0],get_content(w[1:])))
        elif is_good_date(w[0]):
            if w[2]=='do':
                os.system("echo '%s' | at %s %s"%(get_content(w[3:]),w[1],w[0]))
                send_to(who,'已成功添加任务👌\n\n将于 *%s - %s* 执行: *%s*'%(w[0],w[1],get_content(w[3:])))
            else:
                os.system('echo "curl %s -X POST \'https://api.telegram.org/bot%s/sendMessage\' -d \'chat_id=%s\' -d \'text=%s\' -d \'parse_mode=Markdown\'" | at %s %s'%(proxy,API_TOKEN,who,get_content(w[2:]),w[1],w[0]))
                send_to(who,'已成功添加提醒👌 接收者: %s\n\n将于 *%s - %s *发送: *%s*'%(who,w[0],w[1],get_content(w[2:])))
        elif w[0].startswith('+'):
            if w[2]=='do':
                os.system("echo '%s' | at %s + %s days"%(get_content(w[3:]),w[1],w[0].replace('+','')))
                send_to(who,'已成功添加任务👌\n\n将于 *%s天后 - %s* 执行: *%s*'%(w[0].replace('+',''),w[1],get_content(w[3:])))
            else:
                os.system('echo "curl %s -X POST \'https://api.telegram.org/bot%s/sendMessage\' -d \'chat_id=%s\' -d \'text=%s\' -d \'parse_mode=Markdown\'" | at %s + %s days'%(proxy,API_TOKEN,who,get_content(w[2:]),w[1],w[0].replace('+','')))
                send_to(who,'已成功添加提醒👌 接收者: %s\n\n将于 *%s天后 - %s *发送: *%s*'%(who,w[0].replace('+',''),w[1],get_content(w[2:])))
        elif is_good_time(w[0])==False and is_good_date(w[0])==False and (w[0].startswith('+'))==False:
            send_to(who,'格式错误😱\n\n%s'%tips)
    except IndexError:
        send_to(who,'缺少参数🤯\n\n%s'%tips)

@bot.message_handler(commands=['help','start'])
def send_welcome(message):
    bot.reply_to(message,information)

@bot.message_handler(regexp='/new *')
def send_welcome(message):
    analysis(message.text.replace('/new ',''),message.chat.id)

@bot.message_handler(regexp='/ai *')
def echo_message(message):
    bot.reply_to(message,json.loads(requests.get('http://api.qingyunke.com/api.php?key=free&appid=0&msg=%s'%message.text.replace('/ai ','')).text)['content'])

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message,message.text)


bot.infinity_polling()