import urllib.request
from bs4 import BeautifulSoup
import datetime
import pandas as pd


def update_check(tar_date, recorded_date):
    # 対象日と最新の更新日付を比較して対象日の方が最新の場合ステータス1を返す
    if tar_date > recorded_date:
        return 1
    else:
        return -1


def find_target_words(text, tar_words_list):
    # テキストを半角スペースによりトークン化した上で指定したリストの単語が含まれていればその単語の前後5単語をmessageに設定する
    out_str = ""
    words_list = text.split(' ')
    # 事前に設定した単語が含まれているか確認
    word_bool = False
    for i in range(len(words_list)):
        if words_list[i] in tar_words_list:
            word_bool = True
            tmp_str = (' '.join(map(str, words_list[i - 5:i + 5])))
            out_str = out_str + tmp_str + "\n"
    if word_bool:
        return out_str
    else:
        # 指定したリストの単語がふくまれていない場合Not Foundを返す
        return "Not Found"


# ターゲットとなる単語を指定
# tar_words_list = ["Japan", "Japanese"]
tar_words_list = input().split()

# transcriptの一覧ページのURL
base_url = "http://transcripts.cnn.com/"
aired_list_url = base_url + "TRANSCRIPTS/sn.html"  # Transcriptの一覧ページ
res = urllib.request.urlopen(aired_list_url)
soup = BeautifulSoup(res, "lxml")
link_soup = soup.find_all('div', class_="cnnSectBulletItems")  # 各放送のTranscriptのみに範囲を絞る

# messageリストを初期化
message_list = []

# 取得したい項目のリストを初期化
title_list = []
content_list = []
date_list = []

for i, l in enumerate(link_soup):
    # 対象日が更新最新日よりも未来日の間ずっと処理を実施する
    with open("cnn10.init") as f:
        date_str = f.read()
        init_date = datetime.datetime.strptime(date_str, "%Y%m%d")
    script_url = l.a["href"]  # 各放送日のTranscriptのURLを取得
    title = l.a.text  # 各放送のタイトルを取得
    # 取得したURLをパースして放送年月日を文字列で抽出
    # '/TRANSCRIPTS/1912/13/sn.01.html'のような形式からパース
    # 2100年移行には使えなくなるよくないコードだが現時点では許容する
    date = "20" + l.a["href"].split("/")[2] + l.a["href"].split("/")[3]
    # datetimeを使用してdatetime型に変換
    conv_date = datetime.datetime.strptime(date, '%Y%m%d')

    # 更新があったかどうかを確認し、なかった場合はforループを抜ける
    flg = update_check(tar_date=conv_date, latest_date=init_date)
    if flg == -1:
        if i == 0:
            message = "本日の更新はありません" + "\n"
            message_list.append(message)
        break

    if i == 0:  # リストの１件目が最新日付となるため0かどうかを判定する
        latest_date = date

    tar_url = base_url + script_url
    try:
        script_res = urllib.request.urlopen(tar_url)
        script_soup = BeautifulSoup(script_res, "lxml")
        content = script_soup.find_all("p", class_="cnnBodyText")[2].text  # T0DO:うまく本文のみで絞り込めなかった

        # 当該日の放送にtarget_wordに関する話題があるかどうかチェックする
        result = find_target_words(content, tar_words_list)
        if result == "Not Found":
            message = "{}の更新には日本の話題はありませんでした".format(datetime.datetime.strftime(conv_date, "%Y年%m月%d日")) + "\n"
        else:
            message = "{}の更新に日本の話題がありました".format(datetime.datetime.strftime(conv_date, "%Y年%m月%d日")) + "\n" + result
        message_list.append(message)

        # データの更新情報を準備する
        title_list.append(title)
        content_list.append(content)
        date_list.append(date)


    except:  # エラーの際はエラーになったURLを出力して処理は継続 # 404エラーの場合が多い
        message = "Error:{}".format(tar_url)
        message_list.append(message)

for m in message_list:
    with open("cnn10_result_20200101.txt", mode="a") as f:
        f.write(m)
with open("cnn10.init", mode="w") as f:
    f.write(latest_date)

# 更新情報の追記
out_df = pd.DataFrame({"title": title_list, "content": content_list, "date": date_list})
out_df = out_df[["title", "content", "date"]]
out_df.to_csv("./out/cnn10_scripts_test.csv", header=False, index=False, mode="a")
