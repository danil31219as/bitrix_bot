import random
from bitrix24 import *
import vk_api
import logging
import requests
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import os
TOKEN = str(os.environ.get('TOKEN'))
GROUP_ID = int(os.environ.get('GROUP_ID'))
TOKEN_BITRIX = str(os.environ.get('TOKEN_BITRIX'))
DOMAIN = str(os.environ.get('DOMAIN'))
logging.info('Keys are getting')
WAY = 'UF_CRM_1588349613887'

HASH = {}
PRODUCT_DICT = {'вконтакте': {"PRODUCT_ID": 9, "PRICE": 300},
                'telegram': {"PRODUCT_ID": 7, "PRICE": 400},
                'other.platform': {"PRODUCT_ID": 15, "PRICE": 350},
                'чат-бот': {"PRODUCT_ID": 1, "PRICE": 100},
                'бот-автоответчик': {"PRODUCT_ID": 3, "PRICE": 50},
                "бот-игра": {"PRODUCT_ID": 5, "PRICE": 400},
                'other.bot': {"PRODUCT_ID": 17, "PRICE": 150},
                'сообщество': {"PRODUCT_ID": 13, "PRICE": 50},
                'страница': {"PRODUCT_ID": 11, "PRICE": 100},
                'нет': {"PRODUCT_ID": 19, "PRICE": 0},
                'да': {"PRODUCT_ID": 21, "PRICE": 25}}
logging.basicConfig(level=logging.INFO)


def create_keyboard(buttons=[], inline=False, one_time=False, d=3, ask=True):
    keyboard = VkKeyboard(one_time=one_time, inline=inline)
    line = False
    for i in range(len(buttons) // d):
        for j in range(d):
            keyboard.add_button(buttons[i * d + j][0],
                                color=buttons[i * d + j][1])
        if ask:
            keyboard.add_line()
        else:
            if i * d + j != len(buttons) - 1:
                keyboard.add_line()
        line = True
    for i in range(len(buttons) % d):
        keyboard.add_button(buttons[- i - 1][0],
                            color=buttons[- i - 1][1])
        line = False
    if ask:
        if not line and len(buttons) != 0:
            keyboard.add_line()
        keyboard.add_button('Задать вопрос', VkKeyboardColor.POSITIVE)
    return keyboard.get_keyboard()


class BitrixBot():
    def __init__(self, vk, id):
        self.vk = vk
        self.btx = Bitrix24(
            f'https://{DOMAIN}.bitrix24.ru/rest/1/{TOKEN_BITRIX}')
        self.user_id = id
        self.FUNCTION_DICT = {'start': self.start,
                              'platform': self.platform,
                              'category': self.category,
                              'char_2': self.char_2,
                              'char_1': self.char_1, 'accept': self.accept,
                              'description': self.description,
                              'contact': self.contact, 'manager': self.manager}

    def analyse_type(self, message):
        if message['attachments']:
            if 'sticker' in message['attachments'][0]:
                self.vk.messages.send(user_id=self.user_id,
                                      sticker_id=11758,
                                      random_id=random.randint(0, 2 ** 64))
            elif 'photo' in message['attachments'][0]:
                url = self.vk.photos.getMessagesUploadServer()

                response = requests.post(url=url['upload_url'],
                                         files={'photo': open('cat.jpg',
                                                              'rb')}).json()

                photo_info = self.vk.photos.saveMessagesPhoto(
                    photo=response['photo'],
                    server=response['server'],
                    hash=response['hash'])[0]
                photo = f'photo{photo_info["owner_id"]}_{photo_info["id"]}'
                self.vk.messages.send(user_id=self.user_id,
                                      message='',
                                      random_id=random.randint(0,
                                                               2 ** 64),
                                      attachment=photo)
        else:
            text = message['text'].lower().strip()
            self.analyse_text(text)

    def analyse_text(self, text):

        try:
            ask_method = HASH[self.user_id]['ask']
        except:
            ask_method = 'false'
        if text == 'начать':
            if self.user_id not in HASH:
                HASH[self.user_id] = {}
            HASH[self.user_id]["now"] = 'start'
            keyboard = create_keyboard(
                buttons=[['Хочу бота&#129302;', VkKeyboardColor.POSITIVE]])
            if 'contact_id' not in HASH[self.user_id]:
                response = self.vk.users.get(user_id=self.user_id)[0]

                id = self.btx.callMethod("crm.contact.add",
                                         fields={'TYPE_ID': 'CLIENT',
                                                 'NAME': response[
                                                     'first_name'],
                                                 'LAST_NAME': response[
                                                     'last_name'],
                                                 "IM": [{"VALUE": 'id' + str(
                                                     response['id']),
                                                         'VALUE_TYPE': 'VK'}],
                                                 })
                HASH[self.user_id]['contact_id'] = id
            self.vk.messages.send(user_id=self.user_id,
                                  message=f'Вас приветствует служба покупки ботов DanAsOne&#128104;&#8205;&#128187;',
                                  random_id=random.randint(0, 2 ** 64))
            self.vk.messages.send(user_id=self.user_id,
                                  message=f'Следуйте инструкциям на клавиатуре&#9000;',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)

        elif text == 'задать вопрос' or ask_method == 'true':
            self.ask(ask_method=ask_method)
        else:
            try:
                state = HASH[self.user_id]["now"]
            except Exception:
                state = 'start'
                HASH[self.user_id]["now"] = 'start'
            logging.info(state)
            self.FUNCTION_DICT[state](text)

    def ask(self, ask_method='false'):
        if ask_method == 'false':
            HASH[self.user_id]['ask'] = 'true'
            self.vk.messages.send(user_id=self.user_id,
                                  message='Опишите вашу проблему в одно сообщение&#128172;',
                                  random_id=random.randint(0, 2 ** 64))
        else:
            HASH[self.user_id]['ask'] = 'false'
            id = HASH[self.user_id]['id']
            deal = self.btx.callMethod('crm.deal.get', ID=id)
            self.btx.callMethod('im.notify', to=1,
                                message=f'Есть вопрос по {"№".join(deal["TITLE"].split("#"))}',
                                type='SYSTEM')
            self.vk.messages.send(user_id=self.user_id,
                                  message='Дождитесь менеджера...&#8986;',
                                  random_id=random.randint(0, 2 ** 64))

    def start(self, text):
        if text.startswith('хочу бота'):
            contact_id = HASH[self.user_id]['contact_id']
            id = self.btx.callMethod("crm.deal.add",
                                     fields={'CONTACT_ID': contact_id})
            HASH[self.user_id]['id'] = id
            HASH[self.user_id]['now'] = "platform"
            keyboard = create_keyboard(
                buttons=[['Вконтакте', VkKeyboardColor.DEFAULT],
                         ['Telegram', VkKeyboardColor.DEFAULT]], d=2)
            self.vk.messages.send(user_id=self.user_id,
                                  message=f'Выберите платформу бота (или укажите свою)&#128221;',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)

    def platform(self, text):
        if text not in ['вконтакте', 'telegram']:
            text = 'other.platform'
        HASH[self.user_id]['products'] = text
        id = HASH[self.user_id]['id']
        self.set_products(id)
        HASH[self.user_id]['now'] = "category"
        keyboard = create_keyboard(
            buttons=[['Чат-бот', VkKeyboardColor.DEFAULT],
                     ['Бот-игра', VkKeyboardColor.DEFAULT],
                     ['Бот-автоответчик', VkKeyboardColor.DEFAULT]], d=2)
        self.vk.messages.send(user_id=self.user_id,
                              message=f'Выберите категорию бота (или укажите свою)&#128221;',
                              random_id=random.randint(0, 2 ** 64),
                              keyboard=keyboard)

    def category(self, text):
        if text not in ['чат-бот', 'бот-автоответчик', 'бот-игра']:
            text = 'other.bot'
        HASH[self.user_id]['products'] += '_' + text
        id = HASH[self.user_id]['id']
        self.set_products(id)
        HASH[self.user_id]["now"] = 'char_2'
        keyboard = create_keyboard()
        self.vk.messages.send(user_id=self.user_id,
                              message='Пройдите опрос&#128196;',
                              random_id=random.randint(0, 2 ** 64),
                              keyboard=keyboard)
        keyboard = create_keyboard(
            buttons=[['Да', VkKeyboardColor.PRIMARY],
                     ['Нет', VkKeyboardColor.PRIMARY]], d=2,
            ask=False, inline=True)
        self.vk.messages.send(user_id=self.user_id,
                              message=f'Реагирует на вложения (стикеры, фото, VkPay)?',
                              random_id=random.randint(0, 2 ** 64),
                              keyboard=keyboard)

    def char_2(self, text):
        if text in ['да', 'нет']:
            HASH[self.user_id]['products'] += '_' + text
            id = HASH[self.user_id]['id']
            self.set_products(id)
            HASH[self.user_id]["now"] = 'char_1'
            keyboard = create_keyboard(
                buttons=[['Сообщество', VkKeyboardColor.PRIMARY],
                         ['Страница', VkKeyboardColor.PRIMARY]], d=2,
                ask=False, inline=True)
            self.vk.messages.send(user_id=self.user_id,
                                  message=f'К чему подключено?',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)

    def char_1(self, text):
        if text in ['сообщество', 'страница']:
            HASH[self.user_id]["now"] = "accept"
            HASH[self.user_id]['products'] += '_' + text
            id = HASH[self.user_id]['id']
            self.set_products(id)
            self.btx.callMethod("crm.deal.update", ID=id,
                                fields={'STAGE_ID': 'PREPARATION'})
            cost = int(self.btx.callMethod('crm.deal.get', ID=id)[
                           'OPPORTUNITY'].split('.')[0])
            keyboard = create_keyboard(
                buttons=[['Я согласен с условиями', VkKeyboardColor.POSITIVE],
                         ['Отменить заказ', VkKeyboardColor.NEGATIVE]], d=1,
                ask=False)
            self.vk.messages.send(user_id=self.user_id,
                                  message=f'Предварительная стоимость составляет {cost}\nПредоплата {cost * 0.3}&#128179;(-50% на всё!!!)\nВы согласны с условиями?',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)

    def accept(self, text):
        if text.startswith('я согласен'):
            HASH[self.user_id]["now"] = "description"
            id = HASH[self.user_id]['id']
            self.btx.callMethod("crm.deal.update", ID=id,
                                fields={'STAGE_ID': 'PREPAYMENT_INVOICE'})
            keyboard = create_keyboard(
                buttons=[['Продолжить', VkKeyboardColor.PRIMARY]])
            self.vk.messages.send(user_id=self.user_id,
                                  message='Кратко опишите вашу идею и нажмите "Продолжить"',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)
        elif text.startswith('отменить'):
            HASH[self.user_id]["now"] = 'start'
            id = HASH[self.user_id]['id']
            self.btx.callMethod("crm.deal.update", ID=id,
                                fields={'STAGE_ID': 'LOSE'})
            keyboard = create_keyboard(
                buttons=[['Хочу бота&#129302;', VkKeyboardColor.POSITIVE]])
            self.vk.messages.send(user_id=self.user_id,
                                  message=f'Вас приветствует служба покупки ботов DanAsOne&#128104;&#8205;&#128187;',
                                  random_id=random.randint(0, 2 ** 64))
            self.vk.messages.send(user_id=self.user_id,
                                  message=f'Следуйте инструкциям на клавиатуре&#9000;',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)

    def description(self, text):
        if text == "продолжить":
            try:
                comment = HASH[self.user_id]['comment'].decode(
                    'utf-8')
                HASH[self.user_id]['comment'] = ''
                id = HASH[self.user_id]['id']
                self.btx.callMethod('crm.deal.update', ID=id,
                                    fields={'COMMENTS': comment})
            except:
                pass
            HASH[self.user_id]["now"] = 'contact'
            keyboard = create_keyboard(
                buttons=[['Вконтакте', VkKeyboardColor.DEFAULT],
                         ['Email', VkKeyboardColor.DEFAULT],
                         ['Viber', VkKeyboardColor.DEFAULT],
                         ['Telegram', VkKeyboardColor.DEFAULT],
                         ['Звонок на мобильный', VkKeyboardColor.DEFAULT]],
                d=2)
            self.vk.messages.send(user_id=self.user_id,
                                  message=f'Как нам с вами связаться?&#128222;',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)
        else:
            comment = ''
            try:
                comment += HASH[self.user_id]['comment']
            except Exception:
                pass
            comment += '\n' + text
            HASH[self.user_id]['comment'] = comment

    def contact(self, text):
        id = HASH[self.user_id]['id']
        if text.startswith('вк'):
            HASH[self.user_id]["contact"] = "VK"
            self.btx.callMethod("crm.deal.update", ID=id,
                                fields={WAY: 'Вконтакте'})
            return self.final()
        elif text == 'email':
            self.btx.callMethod("crm.deal.update", ID=id,
                                fields={WAY: 'email'})
            if self.check_contact('email'):
                return self.final()
            HASH[self.user_id]["contact"] = "EMAIL"
            HASH[self.user_id]["now"] = 'manager'
            keyboard = create_keyboard(
                buttons=[])
            self.vk.messages.send(user_id=self.user_id,
                                  message='Введите ваш адрес email',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)
        elif text.startswith('звонок') or text.startswith(
                'viber') or text.startswith('telegram'):
            self.btx.callMethod("crm.deal.update", ID=id,
                                fields={WAY: text})
            if self.check_contact('phone'):
                return self.final()
            HASH[self.user_id]["contact"] = "PHONE-" + text.upper()
            HASH[self.user_id]["now"] = 'manager'
            keyboard = create_keyboard(
                buttons=[])
            self.vk.messages.send(user_id=self.user_id,
                                  message='Введите ваш номер телефона',
                                  random_id=random.randint(0, 2 ** 64),
                                  keyboard=keyboard)

    def manager(self, text):
        contact = HASH[self.user_id]["contact"]

        if contact.startswith('VK'):
            pass
        elif contact.startswith('EMAIL'):
            contact_id = HASH[self.user_id]['contact_id']
            self.btx.callMethod('crm.contact.update', ID=contact_id,
                                fields={'EMAIL': [{"VALUE": text}]})
        elif contact.startswith('PHONE'):
            contact_id = HASH[self.user_id]['contact_id']
            contact = contact.split('-')[1]
            response = self.vk.users.get(user_id=self.user_id)[0]
            if contact in ['VIBER', 'TELEGRAM']:
                self.btx.callMethod('crm.contact.update', ID=contact_id,
                                    fields={"IM": [{"VALUE": 'id' + str(
                                        response['id']), 'VALUE_TYPE': 'VK'},
                                                   {"VALUE": text,
                                                    'VALUE_TYPE': contact}]})
            self.btx.callMethod('crm.contact.update', ID=contact_id,
                                fields={'PHONE': [{"VALUE": text}]})
        self.final()

    def final(self):
        id = HASH[self.user_id]['id']
        deal = self.btx.callMethod('crm.deal.get', ID=id)
        self.btx.callMethod('im.notify', to=1,
                            type='SYSTEM',
                            message=f'Оформлена {"№".join(deal["TITLE"].split("#"))}'
                            )
        self.btx.callMethod("crm.deal.update", ID=id,
                            fields={'STAGE_ID': 'EXECUTING'})
        HASH[self.user_id]["now"] = 'start'
        keyboard = create_keyboard(
            buttons=[['Хочу бота&#129302;', VkKeyboardColor.POSITIVE]])
        self.vk.messages.send(user_id=self.user_id,
                              message=f'В течении следующего часа с вами свяжется менеджер для оговорения стоимости и сроков сдачи.\nОжидайте...&#128242;',
                              random_id=random.randint(0, 2 ** 64),
                              keyboard=keyboard)

    def set_products(self, id):
        search = f'https://{DOMAIN}.bitrix24.ru/rest/1/{TOKEN_BITRIX}/crm.deal.productrows.set/?id={id}'
        products = HASH[self.user_id]['products'].split('_')
        for i in range(len(products)):
            search += f'&rows[{i}][PRODUCT_ID]={PRODUCT_DICT[products[i]]["PRODUCT_ID"]}&rows[{i}][PRICE]={PRODUCT_DICT[products[i]]["PRICE"] * 0.5}'
        requests.get(search)

    def check_contact(self, object):
        contact_id = HASH[self.user_id]['contact_id']
        response = self.btx.callMethod('crm.contact.get', ID=contact_id)
        if object == 'phone':
            return response['HAS_PHONE'] == 'Y'
        elif object == 'email':
            return response['HAS_EMAIL'] == 'Y'


def info_about_user(id, state):
    pass


def main():
    print('----------------------------------------------------------')
    vk_session = vk_api.VkApi(
        token=TOKEN)
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    vk = vk_session.get_api()
    logging.info('Бот запущен...')
    print('Бот запущен...')
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            try:
                bitrix_bot = BitrixBot(vk, event.obj.message['from_id'])
                bitrix_bot.analyse_type(event.obj.message)
            except Exception as e:
                print(e)
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=f'Что-то пошло не так, попробуйте еще раз, если проблема повторится, напишите "Начать"',
                                 random_id=random.randint(0, 2 ** 64))
            print(HASH)


if __name__ == '__main__':
    main()
