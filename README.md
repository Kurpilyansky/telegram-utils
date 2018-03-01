Telegram utils
=======

## Install

    $ git clone --recursive git@github.com:Kurpilyansky/telegram-utils
    $ cd telegram-utils/

## Configure telegram client

    See tg/README.md to compile telegram-cli

    Run tg/bin/telegram-cli -I -W --json
    - Login to your account
    - Use command 'channel_info <Tab>' to find telegram channel-id (long hex-number starting with $)

## Add users to channel

    $ python telegram_utils/add_to_channel.py [-v] input.csv                       \
                                              --channel-id \$01000021321321...ab81 \
                                              [--phone-column N]                   \
                                              [--tg-name-column N]                 \
                                              [--tg-user-id-column N]              \
                                              [--channel-comment-column N]         \
                                              > output.csv 

    Script update (or add) data in tg-user-id-column and channel-comment-column.
    If you run with --tg-user-id-column and --channel-comment-column, it will run faster.
    Script could run long time, because Telegram limits count of requests.
    Also you can not add more than 50 people in channel in one day (See errors PEER_FLOOD in channel-comment-column).
