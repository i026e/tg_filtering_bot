from tg_filtering_bot.bot.filtering_bot import start_filtering_bot
from tg_filtering_bot.channel_client.client import start_monitoring_process
from tg_filtering_bot.service import start_service


def main():
    channel_queue = start_monitoring_process()
    bot_message_queue = start_filtering_bot()

    start_service(
        channel_queue=channel_queue,
        bot_message_queue=bot_message_queue
    )


if __name__ == "__main__":
    main()
