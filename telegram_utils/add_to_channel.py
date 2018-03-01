import argparse
import csv
import re
import sys

import telegram_client as tc


def match_to_phone(phone):
    return phone and re.match('^\d+$', phone)


def match_to_telegram_name(telegram_name):
    return telegram_name and re.match('^@[a-zA-Z0-9_]+$', telegram_name)


def try_get_user_telegram_id(telegram_client, phones, tg_name):
    if match_to_telegram_name(tg_name):
        res = telegram_client.make_request("resolve_username %s" % (tg_name.lstrip('@')))
        if res and "id" in res:
            return res["id"]

    for phone in phones:
        if match_to_phone(phone):
            res = telegram_client.make_request("add_contact %s %s %s" % (phone, '?', '?'))
            if res and ("error" not in res) and ("id" in res[0]):
                return res[0]["id"]

    return ''  # telegram account is not found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', type=str, help='path to file with input data in csv')
    parser.add_argument('--channel-id', required=True, type=str, help='channel telegram internal_id')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbose')
    parser.add_argument('--phone-column', type=int, help='0-index of column with phone')
    parser.add_argument('--tg-name-column', type=int, help='0-index of column with telegram name')
    parser.add_argument('--tg-user-id-column', type=int, help='0-index of column with telegram-id')
    parser.add_argument('--channel-comment-column', type=int, help='0-index of column with channel-comment')
    args = parser.parse_args()

    channel_id = args.channel_id
    input_file = args.input_file

    verbose = args.verbose

    phone_column = args.phone_column
    tg_name_column = args.tg_name_column
    tg_user_id_column = args.tg_user_id_column
    channel_comment_column = args.channel_comment_column

    not_found_users = 0
    errors = {}

    with tc.TelegramClient(port=2390, verbose=verbose) as telegram_client:
        with open(input_file) as f:
            csv_reader = csv.reader(f, delimiter='\t')
            csv_writer = csv.writer(sys.stdout, delimiter='\t')
            i = 0
            for row in csv_reader:
                if i % 100 == 0:
                    sys.stderr.write('Processed %d lines...\n' % i)
                i += 1

                if verbose:
                    sys.stderr.write(str(row) + '\n')

                phones = row[phone_column].replace(' ', '').split(',') if phone_column else []
                tg_name = row[tg_name_column] if tg_name_column else None
                if match_to_phone(tg_name):  # a little strange case
                    phones = [tg_name] + phones
                    tg_name = ''

                if verbose:
                    sys.stderr.write('%s %s\n' % (str(phones), tg_name))
                # break

                user_id = row[tg_user_id_column] if tg_user_id_column else ''
                channel_comment = row[channel_comment_column] if channel_comment_column else ''

                if not user_id:
                    user_id = try_get_user_telegram_id(telegram_client, phones, tg_name)

                if not user_id:
                    channel_comment = ''
                    not_found_users += 1
                else:
                    if channel_comment.find('PEER_FLOOD') != -1:
                        channel_comment = ''
                    if not channel_comment:
                        res = telegram_client.make_request("channel_invite %s %s" % (channel_id, user_id))
                        if res["result"] == 'FAIL':
                            channel_comment = res["error"]
                            if channel_comment not in errors:
                                errors[channel_comment] = 1
                            else:
                                errors[channel_comment] += 1
                        else:
                            channel_comment = "ok"

                if tg_user_id_column:
                    row[tg_user_id_column] = user_id
                else:
                    row.append(user_id)
                if channel_comment_column:
                    row[channel_comment_column] = channel_comment
                else:
                    row.append(channel_comment)

                csv_writer.writerow(row)
                sys.stdout.flush()
                # break

    sys.stderr.write('%d users were not found\n' % not_found_users)
    for error, count in errors.items():
        if count:
            sys.stderr.write('%s: %d times\n' % (error, count))

if __name__ == '__main__':
    main()
