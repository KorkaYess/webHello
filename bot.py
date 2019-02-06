import os
import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from playhouse.shortcuts import model_to_dict

from models import Item, Cart, CartItem, Customer


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
token = os.environ['BOT_TOKEN']
updater = Updater(token=token)
dispatcher = updater.dispatcher


def exception(func):
    def wrapper(bot, update, *args, **kwargs):
        try:
            func(bot, update, *args, **kwargs)
        except Exception as e:
            logging.error(e, exc_info=True)
            bot.send_message(
                chat_id=update.message.chat_id,
                text='Fail {}'.format(e)
            )
    return wrapper


def start(bot, update):
    # Бот просит представиться при каждом вызове старт
    bot.send_message(
        chat_id=update.message.chat_id,
        text='Здравствуйте! Как вас Зовут?'
        '\nВы можете ознакомиться с функционалом бота помощью команды /help'
        '\nОзнакомиться с товарами можно на сайте http://127.0.0.1:5000/'
    )


def help(bot, update):
    # Список всех команд
    bot.send_message(
        chat_id=update.message.chat_id,
        text='/name + (Ваше имя) - проверяем Вас в базе и выдаем ID корзины;'
        '\n\n/add + (ID вашей корзины) + (ID товара) + (количество продуктов) '
        '- добавляет определенное количество товара в вашу корзину;'
        '\n\n/remove + (ID товара в корзине) - удаляет определенный'
        ' товар из корзины;'
        '\n\n/price + (ID корзины) - вывод текущей стоимости товаров в корзине;'
        '\n\n/buy + (ID вашей корзины) - олачивает всю стоимость корзины.'
    )


@exception
def name(bot, update, args):
    '''
    Данная функция проверяет наличие пользователя в БД по имени.
    Если такого пользователя нет, вносит его в БД.
    И создает для него корзину, т.е. каждый новый name - новая корзина
    '''
    try:
        name = args[0]
        customers = Customer.select(Customer.name).where(Customer.name == name)
        if len(customers) == 1:
            customer = customers[0]
            bot.send_message(
                chat_id=update.message.chat_id,
                text='{}, мы Вас узнали :)'
                '\nРады вновь Вас видеть в Alma Shop.'.format(customer)
            )
        if len(customers) == 0:
            customer = Customer(
                name=name
            )
            customer.save()
            bot.send_message(
                chat_id=update.message.chat_id,
                text='Отлично, {}. Мы добавили Вас в базу.'.format(name)
            )
        customers = Customer.select().where(Customer.name == name)
        customer = [model_to_dict(customer) for customer in customers][0]
        cart = Cart(
            customer=customer['id']
        )
        cart.save()
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ID вашей корзины {}. Не потеряйте!'
            '\n\nДля добавления товаров в корзину используйте команду:'
            '\n/add + ID вашей корзины + ID товара и необходимое количество'.
            format(cart.id)
        )
    except IndexError:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Вы забыли ввести имя :('
            '\nПопробуйте еще разок.'
        )


@exception
def add(bot, update, args):
    '''
    Добавление товаров в корзину
    ID корзины + ID товара(сайте) + количество.
    Выдает ID операции
    '''
    if len(args) == 3:
        quantity = args[2]
        item_id = args[1]
        item = Item.select().where(
            Item.id == item_id
        )[0]
        cart_id = args[0]
        cart = Cart.select().where(Cart.id == cart_id)[0]
        cart_item = CartItem(
            cart=cart,
            item=item,
            quantity=quantity
        )
        cart_item.save()
        bot.send_message(
            chat_id=update.message.chat_id,
            text='{} в корзине ({} шт.)'
            '\n\nID операции - {}. Не потеряйте, пригодится при удалении.'.
            format(cart_item.item, cart_item.quantity, cart_item.id)
        )
    elif len(args) == 2:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Кажется, Вы не ввели нужное количество продукта.'
            '\nПопробуйте еще разок.'
            '\n/add + ID вашей корзины + ID товара и необходимое количество.'
        )
    elif len(args) == 1:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Кажется, Вы не ввели ID товара и количество.'
            '\nПопробуйте еще разок.'
            '\n/add + ID вашей корзины + ID товара и необходимое количество.'
        )
    elif len(args) == 0:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Похоже, вы ничего не добавили.'
            '\nПопробуйте еще разок.'
            '\n/add + ID вашей корзины + ID товара и необходимое количество.'
        )


@exception
def remove(bot, update, args):
    # Удаляет CartItem по ID
    if len(args) == 1:
        cartitem_id = args[0]
        cart_item = CartItem.select().where(CartItem.id == cartitem_id)[0]
        cart_item.delete()
        bot.send_message(
            chat_id=update.message.chat_id,
            text='OK, {} удален из Вашей корзины.'.
            format(cart_item.item.name)
        )
    else:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Вы забыли ввести ID операции :('
            '\nПопробуйте еще разок.'
            '\n/remove + ID операции, которую Вы хотите отменить.'
        )


@exception
def price(bot, update, args):
    # Возвращает общую стоимость товаров в корзине
    # Принимает Id корзины
    try:
        cart_id = args[0]
        cart = Cart.select().where(Cart.id == cart_id)[0]
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Общая стоимость составляет: {} KZT.'.format(cart.price)
        )
    except IndexError:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Похоже, вы не ввели ID корзины'
            '\nПопробуйте еще разок.'
        )


@exception
def buy(bot, update, args):
    # Принимает ID корзины и закрывает сделку
    try:
        cart_id = args[0]
        cart = Cart.update(paid=True).where(Cart.id == cart_id)
        cart.execute()
        cart = Cart.select().where(Cart.id == cart_id)[0]
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Оплата прошла успешно :)'
            '\nСумма оплаты составляет: {} KZT.'.format(cart.price)
        )
    except IndexError:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Похоже, вы не ввели ID корзины'
            '\nПопробуйте еще разок.'
        )


def echo(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text=update.message.text
    )


def unknown(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text='Такой команды не существует.'
        '\nНажмите на /help'
    )


start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', help)
name_handler = CommandHandler('name', name, pass_args=True)
add_handler = CommandHandler('add', add, pass_args=True)
remove_handler = CommandHandler('remove', remove, pass_args=True)
price_handler = CommandHandler('price', price, pass_args=True)
buy_handler = CommandHandler('buy', buy, pass_args=True)
echo_handler = MessageHandler(Filters.text, echo)
unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(name_handler)
dispatcher.add_handler(add_handler)
dispatcher.add_handler(remove_handler)
dispatcher.add_handler(price_handler)
dispatcher.add_handler(buy_handler)
dispatcher.add_handler(echo_handler)
dispatcher.add_handler(unknown_handler)


if __name__ == '__main__':
    updater.start_polling()
