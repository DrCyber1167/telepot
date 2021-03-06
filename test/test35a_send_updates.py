# coding=utf8

import asyncio
import time
import threading
import pprint
import sys
import traceback
import aiohttp
import telepot
import telepot.namedtuple
import telepot.async

def equivalent(data, nt):
    if type(data) is dict:
        keys = list(data.keys())

        # number of dictionary keys == number of non-None values in namedtuple?
        if len(keys) != len([f for f in nt._fields if getattr(nt, f) is not None]):
            return False

        # map `from` to `from_`
        fields = list([k+'_' if k in ['from'] else k for k in keys])

        return all(map(equivalent, [data[k] for k in keys], [getattr(nt, f) for f in fields]))
    elif type(data) is list:
        return all(map(equivalent, data, nt))
    else:
        return data==nt

def examine(result, type):
    try:
        print('Examining %s ......' % type)

        nt = type(**result)
        assert equivalent(result, nt), 'Not equivalent:::::::::::::::\n%s\n::::::::::::::::\n%s' % (result, nt)

        pprint.pprint(result)
        pprint.pprint(nt)
        print()
    except AssertionError:
        traceback.print_exc()
        print('Do you want to continue? [y]', end=' ')
        answer = input()
        if answer != 'y':
            exit(1)

async def send_everything(msg):
    content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)

    if chat_id != USER_ID:
        print('Unauthorized user:', chat_id)
        exit(1)

    print('Received message from ID: %d' % chat_id)
    print('Start sending various messages ...')

    ##### forwardMessage

    r = await bot.forwardMessage(chat_id, chat_id, msg_id)
    examine(r, telepot.namedtuple.Message)

    ##### sendMessage

    r = await bot.sendMessage(chat_id, 'Hello, I am going to send you a lot of things.', reply_to_message_id=msg_id)
    examine(r, telepot.namedtuple.Message)

    r = await bot.sendMessage(chat_id, '中文')
    examine(r, telepot.namedtuple.Message)

    r = await bot.sendMessage(chat_id, '*bold text*\n_italic text_\n[link](http://www.google.com)', parse_mode='Markdown')
    examine(r, telepot.namedtuple.Message)

    await bot.sendMessage(chat_id, 'http://www.yahoo.com\nwith web page preview')

    await bot.sendMessage(chat_id, 'http://www.yahoo.com\nno web page preview', disable_web_page_preview=True)

    show_keyboard = {'keyboard': [['Yes', 'No'], ['Maybe', 'Maybe not']]}
    hide_keyboard = {'hide_keyboard': True}
    force_reply = {'force_reply': True}

    nt_show_keyboard = telepot.namedtuple.ReplyKeyboardMarkup(**show_keyboard)
    nt_hide_keyboard = telepot.namedtuple.ReplyKeyboardHide(**hide_keyboard)
    nt_force_reply = telepot.namedtuple.ForceReply(**force_reply)

    await bot.sendMessage(chat_id, 'Here is a custom keyboard', reply_markup=show_keyboard)

    await asyncio.sleep(2)

    await bot.sendMessage(chat_id, 'Hiding it now.', reply_markup=nt_hide_keyboard)

    await bot.sendMessage(chat_id, 'Force reply', reply_markup=nt_force_reply)

    ##### sendPhoto

    await bot.sendChatAction(chat_id, 'upload_photo')
    r = await bot.sendPhoto(chat_id, open('lighthouse.jpg', 'rb'))
    examine(r, telepot.namedtuple.Message)

    file_id = r['photo'][0]['file_id']

    await bot.sendPhoto(chat_id, file_id, caption='Show original message and keyboard', reply_to_message_id=msg_id, reply_markup=nt_show_keyboard)

    await bot.sendPhoto(chat_id, file_id, caption='Hide keyboard', reply_markup=hide_keyboard)

    r = await aiohttp.get('http://i.imgur.com/B1fzGoh.jpg')
    bbb = await r.read()

    await bot.sendPhoto(chat_id, ('abc.jpg', bbb))

    ##### getFile

    f = await bot.getFile(file_id)
    examine(f, telepot.namedtuple.File)

    ##### download_file

    try:
        print('Downloading file to non-existent directory ...')
        await bot.download_file(file_id, 'non-existent-dir/file')
    except:
        print('Error: as expected')

    print('Downloading file to down.1 ...')
    await bot.download_file(file_id, 'down.1')

    print('Open down.2 and download to it ...')
    with open('down.2', 'wb') as down:
        await bot.download_file(file_id, down)

    ##### sendAudio
    # Need one of `performer` or `title' for server to regard it as audio. Otherwise, server treats it as voice.

    await bot.sendChatAction(chat_id, 'upload_audio')
    r = await bot.sendAudio(chat_id, open('dgdg.mp3', 'rb'), title='Ringtone')
    examine(r, telepot.namedtuple.Message)

    file_id = r['audio']['file_id']

    await bot.sendAudio(chat_id, file_id, duration=6, performer='Ding Dong', title='Ringtone', reply_to_message_id=msg_id, reply_markup=show_keyboard)

    await bot.sendAudio(chat_id, file_id, performer='Ding Dong', reply_markup=nt_hide_keyboard)

    ##### sendDocument

    await bot.sendChatAction(chat_id, 'upload_document')
    r = await bot.sendDocument(chat_id, open('document.txt', 'rb'))
    examine(r, telepot.namedtuple.Message)

    file_id = r['document']['file_id']

    await bot.sendDocument(chat_id, file_id, reply_to_message_id=msg_id, reply_markup=nt_show_keyboard)

    await bot.sendDocument(chat_id, file_id, reply_markup=hide_keyboard)

    ##### sendSticker

    r = await bot.sendSticker(chat_id, open('gandhi.png', 'rb'))
    examine(r, telepot.namedtuple.Message)

    file_id = r['sticker']['file_id']

    await bot.sendSticker(chat_id, file_id, reply_to_message_id=msg_id, reply_markup=show_keyboard)

    await bot.sendSticker(chat_id, file_id, reply_markup=nt_hide_keyboard)

    ##### sendVideo

    await bot.sendChatAction(chat_id, 'upload_video')
    r = await bot.sendVideo(chat_id, open('hktraffic.mp4', 'rb'))
    examine(r, telepot.namedtuple.Message)

    try:
        file_id = r['video']['file_id']

        await bot.sendVideo(chat_id, file_id, duration=5, caption='Hong Kong traffic', reply_to_message_id=msg_id, reply_markup=nt_show_keyboard)
        await bot.sendVideo(chat_id, file_id, reply_markup=hide_keyboard)

    except KeyError:
        # For some reason, Telegram servers may return a document.
        print('****** sendVideo returns a DOCUMENT !!!!!')

        file_id = r['document']['file_id']

        await bot.sendDocument(chat_id, file_id, reply_to_message_id=msg_id, reply_markup=nt_show_keyboard)
        await bot.sendDocument(chat_id, file_id, reply_markup=hide_keyboard)

    ##### download_file, multiple chunks

    print('Downloading file to down.3 ...')
    await bot.download_file(file_id, 'down.3')

    ##### sendVoice

    r = await bot.sendVoice(chat_id, open('example.ogg', 'rb'))
    examine(r, telepot.namedtuple.Message)

    file_id = r['voice']['file_id']

    await bot.sendVoice(chat_id, file_id, duration=6, reply_to_message_id=msg_id, reply_markup=show_keyboard)

    await bot.sendVoice(chat_id, file_id, reply_markup=nt_hide_keyboard)

    ##### sendLocation

    await bot.sendChatAction(chat_id, 'find_location')
    r = await bot.sendLocation(chat_id, 22.33, 114.18)  # Hong Kong
    examine(r, telepot.namedtuple.Message)

    await bot.sendLocation(chat_id, 49.25, -123.1, reply_to_message_id=msg_id, reply_markup=nt_show_keyboard)  # Vancouver

    await bot.sendLocation(chat_id, -37.82, 144.97, reply_markup=hide_keyboard)  # Melbourne

    ##### Done sending messages

    await bot.sendMessage(chat_id, 'I am done.')

async def get_user_profile_photos():
    print('Getting user profile photos ...')

    r = await bot.getUserProfilePhotos(USER_ID)
    examine(r, telepot.namedtuple.UserProfilePhotos)

async def test_webhook_getupdates_exclusive():
    await bot.setWebhook('https://www.fake.com/fake', open('old.cert', 'rb'))
    print('Fake webhook set.')

    try:
        await bot.getUpdates()
    except telepot.TelegramError as e:
        print("%d: %s" % (e.error_code, e.description))
        print('As expected, getUpdates() produces an error.')

    await bot.setWebhook()
    print('Fake webhook cancelled.')


expected_content_type = None
content_type_iterator = iter([
    'text', 'voice', 'sticker', 'photo', 'audio' ,'document', 'video', 'contact', 'location',
    'new_chat_member',  'new_chat_title', 'new_chat_photo',  'delete_chat_photo', 'left_chat_member'
])

async def see_every_content_types(msg):
    global expected_content_type, content_type_iterator

    content_type, chat_type, chat_id = telepot.glance(msg)
    from_id = msg['from']['id']

    if chat_id != USER_ID and from_id != USER_ID:
        print('Unauthorized user:', chat_id)
        return

    examine(msg, telepot.namedtuple.Message)
    try:
        if content_type == expected_content_type:
            expected_content_type = next(content_type_iterator)
            await bot.sendMessage(chat_id, 'Please give me a %s.' % expected_content_type)
        else:
            await bot.sendMessage(chat_id, 'It is not a %s. Please give me a %s, please.' % (expected_content_type, expected_content_type))
    except StopIteration:
        # reply to sender because I am kicked from group already
        await bot.sendMessage(from_id, 'Thank you. I am done.')


STEP = 1

async def handle(msg):
    global STEP, expected_content_type, content_type_iterator

    if STEP == 1:
        await send_everything(msg)

        STEP = 2
        expected_content_type = next(content_type_iterator)
        await bot.sendMessage(USER_ID, 'Please give me a %s.' % expected_content_type)
    elif STEP == 2:
        await see_every_content_types(msg)
    else:
        print('Out of steps')


TOKEN = sys.argv[1]
USER_ID = int(sys.argv[2])

bot = telepot.async.Bot(TOKEN)
loop = asyncio.get_event_loop()

loop.run_until_complete(test_webhook_getupdates_exclusive())
loop.run_until_complete(get_user_profile_photos())

print('Text me to start.')
loop.create_task(bot.message_loop(handle))
loop.run_forever()
