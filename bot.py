import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

from models import Item, Cart, CartItem


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
updater = Updater(token='697137758:AAHyhtAb-eWMdUeAFSY-oAncB58Vnz5nCVY')
dispatcher = updater.dispatcher


def start(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text="I'm a bot, please talk to me!"
    )


def buy(bot, update, args):
    try:
        item_id = int(args[0])
        item = Item.select().where(Item.id == item_id)[0]
        cart = Cart(
            customer=1
        )
        cart.save()
        cart_item = CartItem(
            cart=cart,
            item=item
        )
        cart_item.save()
        bot.send_message(
            chat_id=update.message.chat_id,
            text='OK {} {}'.format(cart.id, cart_item.id)
        )
    except Exception as e:
        logging.error(e)
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Fail {}'.format(e)
        )


def echo(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text=update.message.text
    )


start_handler = CommandHandler('start', start)
buy_handler = CommandHandler('buy', buy, pass_args=True)
echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(buy_handler)
dispatcher.add_handler(echo_handler)


if __name__ == '__main__':
    updater.start_polling()